import uuid
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status

from app.v1_0.modules.shipment.domain import IShipmentRepository
from app.infraestructure.models.shipment import Shipment, ShippingType
from app.v1_0.modules.shipment.dto.schemas import ShipmentCreateDTO, ShipmentUpdateDTO, ShipmentListResponseDTO, ShipmentResponseDTO
from app.utils.shipment_calculator import ShipmentCalculator
from app.utils.shipment_helpers import generate_vehicle_plate, generate_fleet_number

from app.v1_0.modules.customer.domain import ICustomerRepository
from app.v1_0.modules.product.domain import IProductRepository
from app.v1_0.modules.logistics.domain import IWarehouseRepository, ISeaportRepository
from app.infraestructure.redis.redis_cache_service import RedisCacheService

class ShipmentService:
    """
    Service layer responsible for orchestrating shipment business logic, 
    including automated pricing, ETA calculation, and unique identification.
    """

    def __init__(
        self,
        shipment_repo: IShipmentRepository,
        customer_repo: ICustomerRepository,
        product_repo: IProductRepository,
        warehouse_repo: IWarehouseRepository,
        seaport_repo: ISeaportRepository,
        redis_cache: RedisCacheService
    ):
        """
        Initializes the service with required repositories and Redis cache.
        
        Args:
            shipment_repo: Repository for shipment persistence.
            customer_repo: Repository for customer validation.
            product_repo: Repository for product details.
            warehouse_repo: Repository for land infrastructure.
            seaport_repo: Repository for maritime infrastructure.
            redis_cache: Redis service for atomic serial generation.
        """
        self._shipment_repo = shipment_repo
        self._customer_repo = customer_repo
        self._product_repo = product_repo
        self._warehouse_repo = warehouse_repo
        self._seaport_repo = seaport_repo
        self._redis_cache = redis_cache

    async def get_all(self, skip: int = 0, limit: int = 100) -> ShipmentListResponseDTO:
        """
        Retrieves a paginated list of shipments.
        
        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            
        Returns:
            ShipmentListResponseDTO containing the list of shipments and total count.
        """
        shipments = await self._shipment_repo.get_all(skip=skip, limit=limit)
        total = await self._shipment_repo.count_all()
        
        return ShipmentListResponseDTO(
            data=[ShipmentResponseDTO.model_validate(s) for s in shipments],
            total=total,
            skip=skip,
            limit=limit
        )

    async def get_by_id(self, shipment_id: uuid.UUID) -> ShipmentResponseDTO:
        """
        Retrieves a specific shipment by its UUID.
        
        Args:
            shipment_id: The unique identifier of the shipment.
            
        Returns:
            ShipmentResponseDTO with the shipment details.
            
        Raises:
            HTTPException: If the shipment is not found.
        """
        shipment = await self._shipment_repo.get_by_id(shipment_id)
        if not shipment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Shipment {shipment_id} not found."
            )
        return ShipmentResponseDTO.model_validate(shipment)

    def _to_base36(self, number: int) -> str:
        """
        Converts an integer to a base36 (alphanumeric 0-9, A-Z) string.
        Used to create compact and professional serial numbers.
        
        Args:
            number: The integer to convert.
            
        Returns:
            String representation in Base36.
        """
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        if number == 0:
            return chars[0]
        res = ""
        while number > 0:
            number, i = divmod(number, len(chars))
            res = chars[i] + res
        return res

    async def _generate_unique_guide_number(self, country: str, continent: str) -> str:
        """
        Generates a globally unique, serialized guide number.
        
        This implementation uses Redis INCR to ensure atomic sequentiality. 
        In a distributed environment with multiple devices/servers, Redis ensures 
        that no two requests receive the same serial number, even if they occur 
        at the exact same microsecond.
        
        Format: COUNTRY(3) + CONT(3) + DATE(YYMMDD) + SERIAL(Base36, 5 chars)
        
        Args:
            country: Destination country name.
            continent: Destination continent name.
            
        Returns:
            A unique alphanumeric guide number.
        """
        c_code = country.strip().upper()[:3]
        cont_code = continent.strip().upper()[:3]
        
        from app.utils.time import now_colombian_time
        now_col = now_colombian_time()
        date_prefix = now_col.strftime("%y%m%d")
        
        # Atomic increment ensures thread-safety and distributed concurrency safety
        serial_int = await self._redis_cache.incr("shipment_guide_serial")
        serial_b36 = self._to_base36(serial_int).zfill(5)
        
        return f"{c_code}{cont_code}{date_prefix}{serial_b36}"

    async def create(self, dto: ShipmentCreateDTO) -> ShipmentResponseDTO:
        """
        Creates a new shipment, calculating logistics and pricing automatically.
        
        Workflow:
        1. Validates Customer and Product existence.
        2. Resolves destination geography (Warehouse or Seaport).
        3. Calculates Shipping Type (LAND/MARITIME), ETA and Base Cost.
        4. Applies automatic business discounts (>10 units).
        5. Generates unique Guide Number and Vehicle/Fleet identification.
        
        Args:
            dto: Data transfer object with shipment details.
            
        Returns:
            ShipmentResponseDTO with the newly created shipment.
            
        Raises:
            HTTPException: If related entities or logistics constraints are violated.
        """
        customer = await self._customer_repo.get_by_id(dto.customer_id)
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
            
        product = await self._product_repo.get_by_id(dto.product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

        if not dto.warehouse_id and not dto.seaport_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must provide either warehouse_id or seaport_id.")

        dest_country = ""
        dest_continent = ""
        
        if dto.warehouse_id:
            warehouse = await self._warehouse_repo.get_by_id(dto.warehouse_id)
            if not warehouse:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")
            dest_country = warehouse.country
            dest_continent = warehouse.continent
        elif dto.seaport_id:
            seaport = await self._seaport_repo.get_by_id(dto.seaport_id)
            if not seaport:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seaport not found.")
            dest_country = seaport.country
            dest_continent = seaport.continent

        registry_date = datetime.now(timezone.utc)
        shipping_type, eta, total_base_price, extra_fee = ShipmentCalculator.calculate(
            dispatch_country=dto.dispatch_location,
            dispatch_continent=dto.dispatch_continent,
            dest_country=dest_country,
            dest_continent=dest_continent,
            product_size=product.size,
            quantity=dto.product_quantity,
            registry_date=registry_date
        )

        if shipping_type == ShippingType.LAND:
            if not dto.warehouse_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="This is a LAND shipment based on geographical rules. You must provide a warehouse_id."
                )
            dto.seaport_id = None
        else:
            if not dto.seaport_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, 
                    detail="This is a MARITIME shipment based on geographical rules. You must provide a seaport_id."
                )
            dto.warehouse_id = None

        auto_discount = 0.0
        if dto.product_quantity > 10:
            auto_discount = 5.0 if shipping_type == ShippingType.LAND else 3.0

        final_discount_percentage = min(100.0, dto.discount_percentage + auto_discount)
        base_price_with_extra = total_base_price + extra_fee
        total_price = base_price_with_extra - (base_price_with_extra * (final_discount_percentage / 100))

        guide_number = await self._generate_unique_guide_number(dest_country, dest_continent)
        
        vehicle_plate = dto.vehicle_plate
        fleet_number = dto.fleet_number
        
        if shipping_type == ShippingType.LAND and not vehicle_plate:
            vehicle_plate = generate_vehicle_plate()
        elif shipping_type == ShippingType.MARITIME and not fleet_number:
            fleet_number = generate_fleet_number()

        shipment = Shipment(
            customer_id=dto.customer_id,
            product_id=dto.product_id,
            warehouse_id=dto.warehouse_id,
            seaport_id=dto.seaport_id,
            product_quantity=dto.product_quantity,
            shipping_type=shipping_type,
            base_price=base_price_with_extra,
            discount_percentage=final_discount_percentage,
            total_price=total_price,
            dispatch_location=dto.dispatch_location,
            dispatch_continent=dto.dispatch_continent,
            guide_number=guide_number,
            vehicle_plate=vehicle_plate,
            fleet_number=fleet_number,
            registry_date=registry_date,
            shipping_date=eta
        )

        created_shipment = await self._shipment_repo.create(shipment)
        
        response = ShipmentResponseDTO.model_validate(created_shipment)
        response.applied_extra_fee = extra_fee
        return response

    async def update(self, shipment_id: uuid.UUID, dto: ShipmentUpdateDTO) -> ShipmentResponseDTO:
        """
        Updates the status or identification of an existing shipment.
        
        Args:
            shipment_id: UUID of the shipment to update.
            dto: Data to update.
            
        Returns:
            ShipmentResponseDTO with the updated shipment.
        """
        shipment = await self._shipment_repo.get_by_id(shipment_id)
        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found.")

        if dto.shipping_status is not None:
            shipment.shipping_status = dto.shipping_status
        
        if dto.vehicle_plate is not None:
            if shipment.shipping_type != ShippingType.LAND:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="vehicle_plate is only valid for LAND shipping.")
            shipment.vehicle_plate = dto.vehicle_plate
            
        if dto.fleet_number is not None:
            if shipment.shipping_type != ShippingType.MARITIME:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="fleet_number is only valid for MARITIME shipping.")
            shipment.fleet_number = dto.fleet_number

        updated_shipment = await self._shipment_repo.update(shipment)
        return ShipmentResponseDTO.model_validate(updated_shipment)

    async def delete(self, shipment_id: uuid.UUID) -> None:
        """
        Deletes a shipment record.
        
        Args:
            shipment_id: UUID of the shipment to delete.
        """
        shipment = await self._shipment_repo.get_by_id(shipment_id)
        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found.")
        await self._shipment_repo.delete(shipment)

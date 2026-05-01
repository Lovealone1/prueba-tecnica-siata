import uuid
import secrets
from datetime import datetime, timezone, date
from typing import Optional

from fastapi import HTTPException, status

from app.v1_0.modules.shipment.domain import IShipmentRepository
from app.infraestructure.models.shipment import Shipment, ShippingType, ShippingStatus, ShipmentStatusLog
from app.v1_0.modules.shipment.dto.schemas import (
    ShipmentCreateDTO, ShipmentUpdateDTO, ShipmentListResponseDTO, 
    ShipmentResponseDTO, ShipmentStatusLogResponseDTO, ShipmentAdminUpdateDTO, 
    ShipmentAdminStatsDTO
)
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

    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        customer_id: Optional[uuid.UUID] = None,
        dispatch_location: Optional[str] = None,
        destination_country: Optional[str] = None,
        shipping_type: Optional[ShippingType] = None,
        shipping_status: Optional[ShippingStatus] = None,
        guide_number: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> ShipmentListResponseDTO:
        """
        Retrieves a paginated and filtered list of shipments.
        
        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            customer_id: Optional customer filter.
            dispatch_location: Optional origin country filter.
            destination_country: Optional destination country filter (searches in warehouses/seaports).
            shipping_type: Optional LAND/MARITIME filter.
            shipping_status: Optional PENDING/SENT/DELIVERED filter.
            start_date: Optional starting date for registry_date filter.
            end_date: Optional ending date for registry_date filter.
            
        Returns:
            ShipmentListResponseDTO containing the list of shipments and total count.
        """
        shipments = await self._shipment_repo.get_all(
            skip=skip, 
            limit=limit,
            customer_id=customer_id,
            dispatch_location=dispatch_location,
            destination_country=destination_country,
            shipping_type=shipping_type,
            shipping_status=shipping_status,
            guide_number=guide_number,
            start_date=start_date,
            end_date=end_date
        )
        total = await self._shipment_repo.count_all(
            customer_id=customer_id,
            dispatch_location=dispatch_location,
            destination_country=destination_country,
            shipping_type=shipping_type,
            shipping_status=shipping_status,
            guide_number=guide_number,
            start_date=start_date,
            end_date=end_date
        )
        
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

        final_discount_percentage = auto_discount
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
        
        # Prepare response with clear breakdown for the frontend
        response = ShipmentResponseDTO.model_validate(created_shipment)
        response.base_price = total_base_price # Pure base price (without extra fee)
        response.applied_extra_fee = extra_fee # The bonus fee
        return response

    async def update(self, shipment_id: uuid.UUID, dto: ShipmentUpdateDTO) -> ShipmentResponseDTO:
        """
        Updates an existing shipment. Allows correcting order details (product, quantity, destination)
        only if the shipment is currently in PENDING status. Recalculates pricing and logistics.
        """
        shipment = await self._shipment_repo.get_by_id(shipment_id)
        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found.")

        # BUSINESS RULE: Locked if not PENDING
        if shipment.shipping_status != ShippingStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only shipments in PENDING status can be modified. Current status: {shipment.shipping_status}"
            )

        # 1. Detect changes that require recalculation
        recalculate = False
        
        if dto.product_id is not None and dto.product_id != shipment.product_id:
            product = await self._product_repo.get_by_id(dto.product_id)
            if not product:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New product not found.")
            shipment.product_id = dto.product_id
            recalculate = True
        else:
            product = await self._product_repo.get_by_id(shipment.product_id)

        if dto.product_quantity is not None and dto.product_quantity != shipment.product_quantity:
            shipment.product_quantity = dto.product_quantity
            recalculate = True

        # Handle destination changes
        new_warehouse_id = dto.warehouse_id if dto.warehouse_id is not None else (shipment.warehouse_id if not dto.seaport_id else None)
        new_seaport_id = dto.seaport_id if dto.seaport_id is not None else (shipment.seaport_id if not dto.warehouse_id else None)

        if new_warehouse_id != shipment.warehouse_id or new_seaport_id != shipment.seaport_id:
            shipment.warehouse_id = new_warehouse_id
            shipment.seaport_id = new_seaport_id
            recalculate = True

        # 2. Re-run Logistics and Pricing calculation if needed
        extra_fee = 0.0
        total_base_price = shipment.base_price # Default to existing if no recalculation
        
        if recalculate:
            dest_country = ""
            dest_continent = ""
            
            if shipment.warehouse_id:
                node = await self._warehouse_repo.get_by_id(shipment.warehouse_id)
                if not node: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found.")
                dest_country, dest_continent = node.country, node.continent
            elif shipment.seaport_id:
                node = await self._seaport_repo.get_by_id(shipment.seaport_id)
                if not node: raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Seaport not found.")
                dest_country, dest_continent = node.country, node.continent
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Shipment must have a warehouse_id or seaport_id.")

            # Calculate new logistics
            shipping_type, eta, total_base_price, extra_fee = ShipmentCalculator.calculate(
                dispatch_country=shipment.dispatch_location,
                dispatch_continent=shipment.dispatch_continent,
                dest_country=dest_country,
                dest_continent=dest_continent,
                product_size=product.size,
                quantity=shipment.product_quantity,
                registry_date=shipment.registry_date
            )

            # Validation: Mismatch check
            if shipping_type == ShippingType.LAND and not shipment.warehouse_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Route requires a warehouse_id.")
            if shipping_type == ShippingType.MARITIME and not shipment.seaport_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Route requires a seaport_id.")

            # Update pricing fields
            auto_discount = 5.0 if shipping_type == ShippingType.LAND else 3.0
            final_discount_percentage = auto_discount if shipment.product_quantity > 10 else 0.0
            
            base_price_with_extra = total_base_price + extra_fee
            total_price = base_price_with_extra - (base_price_with_extra * (final_discount_percentage / 100))

            shipment.shipping_type = shipping_type
            shipment.shipping_date = eta
            shipment.base_price = base_price_with_extra
            shipment.discount_percentage = final_discount_percentage
            shipment.total_price = total_price
            
            # If shipping type changed, we might need to reset vehicle/fleet
            if shipping_type == ShippingType.LAND:
                shipment.seaport_id = None
                shipment.fleet_number = None
            else:
                shipment.warehouse_id = None
                shipment.vehicle_plate = None

        # 3. Manual vehicle/fleet updates (optional)
        if dto.vehicle_plate is not None:
            if shipment.shipping_type != ShippingType.LAND:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="vehicle_plate is only valid for LAND shipping.")
            shipment.vehicle_plate = dto.vehicle_plate
            
        if dto.fleet_number is not None:
            if shipment.shipping_type != ShippingType.MARITIME:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="fleet_number is only valid for MARITIME shipping.")
            shipment.fleet_number = dto.fleet_number

        updated_shipment = await self._shipment_repo.update(shipment)
        
        # Prepare response
        response = ShipmentResponseDTO.model_validate(updated_shipment)
        
        # We need the destination info for the breakdown calculation
        if not recalculate:
            dest_country = ""
            dest_continent = ""
            if shipment.warehouse_id:
                node = await self._warehouse_repo.get_by_id(shipment.warehouse_id)
                dest_country, dest_continent = node.country, node.continent
            elif shipment.seaport_id:
                node = await self._seaport_repo.get_by_id(shipment.seaport_id)
                dest_country, dest_continent = node.country, node.continent

            _, _, t_base, e_fee = ShipmentCalculator.calculate(
                dispatch_country=shipment.dispatch_location,
                dispatch_continent=shipment.dispatch_continent,
                dest_country=dest_country,
                dest_continent=dest_continent,
                product_size=product.size,
                quantity=shipment.product_quantity,
                registry_date=shipment.registry_date
            )
            response.base_price = t_base
            response.applied_extra_fee = e_fee
        else:
            response.base_price = total_base_price
            response.applied_extra_fee = extra_fee
            
        return response

    async def delete(self, shipment_id: uuid.UUID) -> None:
        """
        Deletes a shipment record. Only allowed if PENDING.
        """
        shipment = await self._shipment_repo.get_by_id(shipment_id)
        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found.")
        
        if shipment.shipping_status != ShippingStatus.PENDING:
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only shipments in PENDING status can be deleted."
            )
            
        await self._shipment_repo.delete(shipment)

    # --- ADMIN METHODS ---

    async def admin_update_status(self, shipment_id: uuid.UUID, dto: ShipmentAdminUpdateDTO) -> ShipmentResponseDTO:
        """
        Admin-only status update. Enforces sequential transitions:
        PENDING -> SENT -> DELIVERED.
        """
        shipment = await self._shipment_repo.get_by_id(shipment_id)
        if not shipment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found.")

        old_status = shipment.shipping_status
        new_status = dto.shipping_status

        if old_status == new_status:
             return ShipmentResponseDTO.model_validate(shipment)

        # STATE MACHINE VALIDATION
        valid_transitions = {
            ShippingStatus.PENDING: [ShippingStatus.SENT],
            ShippingStatus.SENT: [ShippingStatus.DELIVERED],
            ShippingStatus.DELIVERED: [] # Final state
        }

        if new_status not in valid_transitions.get(old_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition. Cannot move from {old_status} to {new_status}. "
                       f"Sequential flow required: PENDING -> SENT -> DELIVERED."
            )

        shipment.shipping_status = new_status
        
        # Always log admin changes
        await self._shipment_repo.create_status_log(ShipmentStatusLog(
            shipment_id=shipment.id,
            old_status=old_status,
            new_status=new_status,
            reason="ADMIN OVERRIDE: Manual status management by logistics administrator."
        ))

        updated_shipment = await self._shipment_repo.update(shipment)
        return ShipmentResponseDTO.model_validate(updated_shipment)

    async def get_status_history(self, shipment_id: uuid.UUID) -> list[ShipmentStatusLogResponseDTO]:
        """
        Returns the full audit trail of status changes for a shipment.
        """
        # Verify existence
        shipment = await self._shipment_repo.get_by_id(shipment_id)
        if not shipment:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found.")
             
        logs = await self._shipment_repo.get_status_history(shipment_id)
        return [ShipmentStatusLogResponseDTO.model_validate(log) for log in logs]

    async def get_admin_stats(self) -> ShipmentAdminStatsDTO:
        """
        Returns a high-level summary of the logistics operation.
        """
        stats = await self._shipment_repo.get_admin_stats()
        return ShipmentAdminStatsDTO(**stats)

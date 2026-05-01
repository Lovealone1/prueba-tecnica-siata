import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from datetime import datetime, timezone

from app.v1_0.modules.shipment.service import ShipmentService
from app.v1_0.modules.shipment.domain import IShipmentRepository
from app.v1_0.modules.customer.domain import ICustomerRepository
from app.v1_0.modules.product.domain import IProductRepository
from app.v1_0.modules.logistics.domain import IWarehouseRepository, ISeaportRepository, ILogisticsNodeRepository
from app.infraestructure.redis.redis_cache_service import RedisCacheService

from app.v1_0.modules.shipment.dto.schemas import ShipmentCreateDTO, ShipmentUpdateDTO, ShippingStatus
from app.infraestructure.models.shipment import Shipment, ShippingType
from app.infraestructure.models.customer import Customer
from app.infraestructure.models.product import Product, ProductSize
from app.infraestructure.models.warehouse import Warehouse
from app.infraestructure.models.seaport import Seaport

@pytest.fixture
def mock_shipment_repo(): return AsyncMock(spec=IShipmentRepository)

@pytest.fixture
def mock_customer_repo(): return AsyncMock(spec=ICustomerRepository)

@pytest.fixture
def mock_product_repo(): return AsyncMock(spec=IProductRepository)

@pytest.fixture
def mock_warehouse_repo(): return AsyncMock(spec=ILogisticsNodeRepository)

@pytest.fixture
def mock_seaport_repo(): return AsyncMock(spec=ILogisticsNodeRepository)

@pytest.fixture
def mock_redis():
    redis = AsyncMock(spec=RedisCacheService)
    redis.incr.return_value = 1
    return redis

@pytest.fixture
def service(
    mock_shipment_repo, mock_customer_repo, mock_product_repo,
    mock_warehouse_repo, mock_seaport_repo, mock_redis
):
    return ShipmentService(
        shipment_repo=mock_shipment_repo,
        customer_repo=mock_customer_repo,
        product_repo=mock_product_repo,
        warehouse_repo=mock_warehouse_repo,
        seaport_repo=mock_seaport_repo,
        redis_cache=mock_redis
    )

async def test_create_shipment_land_success(service, mock_customer_repo, mock_product_repo, mock_warehouse_repo, mock_shipment_repo):
    # Setup
    customer_id = uuid.uuid4()
    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    
    payload = ShipmentCreateDTO(
        customer_id=customer_id,
        product_id=product_id,
        warehouse_id=warehouse_id,
        product_quantity=15, # > 10 triggers auto-discount
        dispatch_location="USA",
        dispatch_continent="North America"
    )
    
    mock_customer_repo.get_by_id.return_value = Customer(id=customer_id)
    mock_product_repo.get_by_id.return_value = Product(id=product_id, size=ProductSize.SMALL)
    mock_warehouse_repo.get_by_id.return_value = Warehouse(id=warehouse_id, country="USA", continent="North America")
    
    # Mock repository creation
    def side_effect(shipment):
        shipment.id = uuid.uuid4()
        shipment.created_at = datetime.now(timezone.utc)
        shipment.updated_at = datetime.now(timezone.utc)
        shipment.shipping_status = ShippingStatus.PENDING
        return shipment
    mock_shipment_repo.create.side_effect = side_effect
    
    # Execute
    result = await service.create(payload)
    
    # Assert
    assert result.shipping_type == ShippingType.LAND
    assert result.discount_percentage == 5.0 # LAND + >10 units = 5%
    assert result.applied_extra_fee == 0.0 # SMALL limit is 100
    mock_shipment_repo.create.assert_called_once()

async def test_create_shipment_maritime_with_extra_fee(service, mock_customer_repo, mock_product_repo, mock_seaport_repo, mock_shipment_repo):
    # Setup
    customer_id = uuid.uuid4()
    product_id = uuid.uuid4()
    seaport_id = uuid.uuid4()
    
    payload = ShipmentCreateDTO(
        customer_id=customer_id,
        product_id=product_id,
        seaport_id=seaport_id,
        product_quantity=12, # > 10 triggers auto-discount
        dispatch_location="Colombia",
        dispatch_continent="South America"
    )
    
    mock_customer_repo.get_by_id.return_value = Customer(id=customer_id)
    # Extra Large threshold is 10. Quantity 12 > 10.
    mock_product_repo.get_by_id.return_value = Product(id=product_id, size=ProductSize.EXTRA_LARGE)
    # China is Intercontinental from Colombia
    mock_seaport_repo.get_by_id.return_value = Seaport(id=seaport_id, country="China", continent="Asia")
    
    def side_effect(shipment):
        shipment.id = uuid.uuid4()
        shipment.created_at = datetime.now(timezone.utc)
        shipment.updated_at = datetime.now(timezone.utc)
        shipment.shipping_status = ShippingStatus.PENDING
        return shipment
    mock_shipment_repo.create.side_effect = side_effect
    
    # Execute
    result = await service.create(payload)
    
    # Assert
    assert result.shipping_type == ShippingType.MARITIME
    assert result.discount_percentage == 3.0 # MARITIME + >10 units = 3%
    assert result.applied_extra_fee == 200.0 # EXTRA_LARGE fee
    assert result.fleet_number is not None # Generated for maritime
    assert "CHI" in result.guide_number # Country code prefix

async def test_update_shipment_locked_if_not_pending(service, mock_shipment_repo):
    # Setup
    shipment_id = uuid.uuid4()
    existing_shipment = Shipment(
        id=shipment_id,
        shipping_status=ShippingStatus.SENT # Already sent!
    )
    mock_shipment_repo.get_by_id.return_value = existing_shipment
    
    payload = ShipmentUpdateDTO(shipping_status=ShippingStatus.DELIVERED)
    
    # Execute & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.update(shipment_id, payload)
    
    assert exc_info.value.status_code == 400
    assert "PENDING" in exc_info.value.detail

async def test_create_shipment_invalid_infrastructure_mismatch(service, mock_customer_repo, mock_product_repo, mock_warehouse_repo):
    # Setup
    customer_id = uuid.uuid4()
    product_id = uuid.uuid4()
    warehouse_id = uuid.uuid4()
    
    # Colombia to China is Intercontinental -> MARITIME
    payload = ShipmentCreateDTO(
        customer_id=customer_id,
        product_id=product_id,
        warehouse_id=warehouse_id, # User provides warehouse for maritime route
        product_quantity=1
    )
    
    mock_customer_repo.get_by_id.return_value = Customer(id=customer_id)
    mock_product_repo.get_by_id.return_value = Product(id=product_id, size=ProductSize.SMALL)
    mock_warehouse_repo.get_by_id.return_value = Warehouse(id=warehouse_id, country="China", continent="Asia")
    
    # Execute & Assert
    with pytest.raises(HTTPException) as exc_info:
        await service.create(payload)
    
    assert exc_info.value.status_code == 400
    assert "MARITIME" in exc_info.value.detail
    assert "seaport_id" in exc_info.value.detail

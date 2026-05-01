import pytest
import uuid
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, ANY
from datetime import datetime, timezone

from app.main import app
from app.infraestructure.models.user import User, GlobalRole
from app.v1_0.modules.shipment.dto.schemas import ShipmentResponseDTO, ShipmentListResponseDTO, ShippingStatus, ShippingType

# Bypass authentication
async def mock_require_authenticated():
    return User(id=uuid.uuid4(), email="admin@test.com", global_role=GlobalRole.ADMIN)

@pytest.fixture(autouse=True)
def override_dependencies():
    from app.middlewares.auth import require_authenticated
    app.dependency_overrides[require_authenticated] = mock_require_authenticated
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def sample_shipment_response():
    now = datetime.now(timezone.utc)
    return ShipmentResponseDTO(
        id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        product_id=uuid.uuid4(),
        warehouse_id=uuid.uuid4(),
        seaport_id=None,
        product_quantity=5,
        shipping_type=ShippingType.LAND,
        base_price=100.0,
        discount_percentage=0.0,
        total_price=100.0,
        dispatch_location="USA",
        dispatch_continent="North America",
        guide_number="TESTGUIDE123",
        vehicle_plate="AAA123",
        fleet_number=None,
        registry_date=now,
        shipping_date=now,
        shipping_status=ShippingStatus.PENDING,
        applied_extra_fee=0.0,
        created_at=now,
        updated_at=now
    )

async def test_create_shipment_router(async_client: AsyncClient, sample_shipment_response):
    with patch("app.v1_0.modules.shipment.service.ShipmentService.create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = sample_shipment_response
        
        payload = {
            "customer_id": str(uuid.uuid4()),
            "product_id": str(uuid.uuid4()),
            "warehouse_id": str(uuid.uuid4()),
            "product_quantity": 5,
            "dispatch_location": "USA",
            "dispatch_continent": "North America"
        }
        
        response = await async_client.post("/api/v1/shipments", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["guide_number"] == "TESTGUIDE123"
        assert data["applied_extra_fee"] == 0.0

async def test_list_shipments_router_with_filters(async_client: AsyncClient, sample_shipment_response):
    with patch("app.v1_0.modules.shipment.service.ShipmentService.get_all", new_callable=AsyncMock) as mock_get_all:
        mock_get_all.return_value = ShipmentListResponseDTO(
            data=[sample_shipment_response],
            total=1,
            skip=0,
            limit=10
        )
        
        # Test query parameters for filters
        params = {
            "customer_id": str(uuid.uuid4()),
            "shipping_status": "PENDING",
            "start_date": "2026-05-01",
            "end_date": "2026-05-01"
        }
        
        response = await async_client.get("/api/v1/shipments", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        mock_get_all.assert_called_once()

async def test_update_shipment_router(async_client: AsyncClient, sample_shipment_response):
    shipment_id = sample_shipment_response.id
    with patch("app.v1_0.modules.shipment.service.ShipmentService.update", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = sample_shipment_response
        
        payload = {"shipping_status": "SENT"}
        response = await async_client.patch(f"/api/v1/shipments/{shipment_id}", json=payload)
        
        assert response.status_code == 200
        mock_update.assert_called_once_with(shipment_id, ANY)

async def test_delete_shipment_router(async_client: AsyncClient):
    shipment_id = uuid.uuid4()
    with patch("app.v1_0.modules.shipment.service.ShipmentService.delete", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = None
        
        response = await async_client.delete(f"/api/v1/shipments/{shipment_id}")
        
        assert response.status_code == 204
        mock_delete.assert_called_once_with(shipment_id)

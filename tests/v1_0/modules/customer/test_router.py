import pytest
import uuid
from httpx import AsyncClient
from unittest.mock import AsyncMock

from app.main import app
from app.v1_0.modules.customer.service import CustomerService
from app.v1_0.modules.customer.dto.schemas import CustomerResponseDTO, CustomerListResponseDTO
from app.infraestructure.models.user import User, GlobalRole

# Mock for require_authenticated dependency to bypass JWT validation
async def mock_require_authenticated():
    return User(id=uuid.uuid4(), email="test@admin.com", global_role=GlobalRole.ADMIN)

@pytest.fixture(autouse=True)
def override_dependencies():
    from app.middlewares.auth import require_authenticated
    # Override auth to allow the tests to pass without real JWTs
    app.dependency_overrides[require_authenticated] = mock_require_authenticated
    
    yield
    
    app.dependency_overrides.clear()

from unittest.mock import AsyncMock, patch

async def test_create_customer_endpoint(async_client: AsyncClient):
    customer_id = uuid.uuid4()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    expected_response = CustomerResponseDTO(
        id=customer_id,
        name="API Test User",
        identifier="12345",
        email="api@test.com",
        phone=None,
        address=None,
        created_at=now,
        updated_at=now
    )
    
    with patch("app.v1_0.modules.customer.service.CustomerService.create_customer", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = expected_response
        
        response = await async_client.post("/api/v1/customers/", json={
            "name": "API Test User",
            "identifier": "12345",
            "email": "api@test.com"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test User"
        assert data["id"] == str(customer_id)

async def test_get_customer_not_found(async_client: AsyncClient):
    from fastapi import HTTPException
    
    with patch("app.v1_0.modules.customer.service.CustomerService.get_customer", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = HTTPException(status_code=404, detail="Not found")
        
        response = await async_client.get(f"/api/v1/customers/{uuid.uuid4()}")
        assert response.status_code == 404

async def test_patch_customer_endpoint(async_client: AsyncClient):
    customer_id = uuid.uuid4()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    expected_response = CustomerResponseDTO(
        id=customer_id,
        name="Updated Name",
        identifier="12345",
        email="api@test.com",
        phone=None,
        address=None,
        created_at=now,
        updated_at=now
    )
    
    with patch("app.v1_0.modules.customer.service.CustomerService.update_customer", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = expected_response
        
        response = await async_client.patch(f"/api/v1/customers/{customer_id}", json={
            "name": "Updated Name"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

async def test_list_customers_endpoint(async_client: AsyncClient):
    expected_response = CustomerListResponseDTO(
        data=[],
        total=0,
        skip=0,
        limit=100
    )
    
    with patch("app.v1_0.modules.customer.service.CustomerService.list_customers", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = expected_response
        
        response = await async_client.get("/api/v1/customers/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0



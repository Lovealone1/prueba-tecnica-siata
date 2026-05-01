import pytest
import uuid
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.v1_0.modules.product.dto.schemas import ProductResponseDTO, ProductListResponseDTO
from app.infraestructure.models.user import User, GlobalRole
from app.infraestructure.models.product import TransportMode, ProductSize

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

async def test_create_product_endpoint(async_client: AsyncClient):
    product_id = uuid.uuid4()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    expected_response = ProductResponseDTO(
        id=product_id,
        name="API Test Product",
        description="A great product",
        product_type="API Type",
        transport_mode=TransportMode.LAND,
        size=ProductSize.MEDIUM,
        created_at=now
    )
    
    with patch("app.v1_0.modules.product.service.ProductService.create_product", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = expected_response
        
        response = await async_client.post("/api/v1/products/", json={
            "name": "API Test Product",
            "description": "A great product",
            "product_type": "API Type",
            "transport_mode": "LAND",
            "size": "MEDIUM"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Product"
        assert data["transport_mode"] == "LAND"
        assert data["id"] == str(product_id)

async def test_get_product_not_found(async_client: AsyncClient):
    from fastapi import HTTPException
    
    with patch("app.v1_0.modules.product.service.ProductService.get_product", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = HTTPException(status_code=404, detail="Not found")
        
        response = await async_client.get(f"/api/v1/products/{uuid.uuid4()}")
        assert response.status_code == 404

async def test_patch_product_endpoint(async_client: AsyncClient):
    product_id = uuid.uuid4()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    expected_response = ProductResponseDTO(
        id=product_id,
        name="Updated Product Name",
        description=None,
        product_type="Type",
        transport_mode=TransportMode.MARITIME,
        size=ProductSize.LARGE,
        created_at=now
    )
    
    with patch("app.v1_0.modules.product.service.ProductService.update_product", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = expected_response
        
        response = await async_client.patch(f"/api/v1/products/{product_id}", json={
            "name": "Updated Product Name",
            "transport_mode": "MARITIME"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product Name"
        assert data["transport_mode"] == "MARITIME"

async def test_delete_product_endpoint(async_client: AsyncClient):
    product_id = uuid.uuid4()
    
    with patch("app.v1_0.modules.product.service.ProductService.delete_product", new_callable=AsyncMock) as mock_delete:
        response = await async_client.delete(f"/api/v1/products/{product_id}")
        assert response.status_code == 204
        mock_delete.assert_called_once_with(product_id)

async def test_list_products_endpoint_with_filters(async_client: AsyncClient):
    expected_response = ProductListResponseDTO(
        data=[],
        total=0,
        skip=0,
        limit=10
    )
    
    with patch("app.v1_0.modules.product.service.ProductService.list_products", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = expected_response
        
        response = await async_client.get(
            "/api/v1/products/", 
            params={"transport_mode": "MARITIME", "size": "EXTRA_LARGE", "limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["limit"] == 10
        
        # Verify the router parsed the ENUM strings back into Enum objects
        mock_list.assert_called_once_with(
            skip=0, 
            limit=10, 
            transport_mode=TransportMode.MARITIME, 
            size=ProductSize.EXTRA_LARGE
        )

import pytest
import uuid
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.v1_0.modules.logistics.dto.schemas import LogisticsNodeResponseDTO, LogisticsNodeListResponseDTO
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


async def test_create_seaport_endpoint(async_client: AsyncClient):
    node_id = uuid.uuid4()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    expected_response = LogisticsNodeResponseDTO(
        id=node_id,
        name="API Test Seaport",
        address="Port Area",
        city="Cartagena",
        country="Colombia",
        continent="SOUTH AMERICA",
        created_at=now,
    )
    
    with patch("app.v1_0.modules.logistics.service.LogisticsNodeService.create_node", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = expected_response
        
        response = await async_client.post("/api/v1/seaports/", json={
            "name": "API Test Seaport",
            "address": "Port Area",
            "city": "Cartagena",
            "country": "Colombia"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "API Test Seaport"
        assert data["id"] == str(node_id)
        assert data["continent"] == "SOUTH AMERICA"


async def test_get_seaport_not_found(async_client: AsyncClient):
    from fastapi import HTTPException
    
    with patch("app.v1_0.modules.logistics.service.LogisticsNodeService.get_node", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = HTTPException(status_code=404, detail="Not found")
        
        response = await async_client.get(f"/api/v1/seaports/{uuid.uuid4()}")
        assert response.status_code == 404


async def test_patch_seaport_endpoint(async_client: AsyncClient):
    node_id = uuid.uuid4()
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    
    expected_response = LogisticsNodeResponseDTO(
        id=node_id,
        name="Updated Seaport",
        address="Port Area",
        city="Cartagena",
        country="Colombia",
        continent="SOUTH AMERICA",
        created_at=now,
    )
    
    with patch("app.v1_0.modules.logistics.service.LogisticsNodeService.update_node", new_callable=AsyncMock) as mock_update:
        mock_update.return_value = expected_response
        
        response = await async_client.patch(f"/api/v1/seaports/{node_id}", json={
            "name": "Updated Seaport"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Seaport"


async def test_list_seaports_endpoint(async_client: AsyncClient):
    expected_response = LogisticsNodeListResponseDTO(
        data=[],
        total=0,
        skip=0,
        limit=100
    )
    
    with patch("app.v1_0.modules.logistics.service.LogisticsNodeService.list_nodes", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = expected_response
        
        response = await async_client.get("/api/v1/seaports/?continent=SOUTH AMERICA&country=Colombia")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        
        # Verify query parameters were passed correctly
        mock_list.assert_called_once_with(skip=0, limit=100, continent='SOUTH AMERICA', country='Colombia')

async def test_delete_seaport_endpoint(async_client: AsyncClient):
    with patch("app.v1_0.modules.logistics.service.LogisticsNodeService.delete_node", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = None
        
        response = await async_client.delete(f"/api/v1/seaports/{uuid.uuid4()}")
        
        assert response.status_code == 204

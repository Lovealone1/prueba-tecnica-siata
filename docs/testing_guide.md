# Clean Architecture: Unit Testing Guide

This document establishes the standard guidelines for unit testing CRUD modules within our Clean Architecture framework. These rules ensure that all modules are tested consistently, isolating business logic from infrastructure constraints.

## 1. Directory Structure

Tests should mirror the structure of the application. For a module named `entity`, place tests in:
`tests/v1_0/modules/<entity>/`

It should contain at least:
- `test_service.py` (Domain & Business Logic)
- `test_router.py` (HTTP Endpoints & Dependency Injection)

---

## 2. Service Layer Tests (`test_service.py`)

**Objective**: Test pure business logic, validations, and audit trails without requiring an active database connection or HTTP layer.

### Mocking the Repository
Always mock the Domain Repository (`IEntityRepository`) using `unittest.mock.AsyncMock`. Inject the mock into the Service instance via `pytest` fixtures.

```python
import pytest
from unittest.mock import AsyncMock
from app.v1_0.modules.my_entity.service import MyEntityService
from app.v1_0.modules.my_entity.domain import IMyEntityRepository

@pytest.fixture
def mock_repo():
    return AsyncMock(spec=IMyEntityRepository)

@pytest.fixture
def service(mock_repo):
    return MyEntityService(mock_repo)
```

### Key Scenarios to Cover:
1. **Success Flows**: Verify correct DTO mapping and ensure repository methods (`create`, `update`, `delete`, `get_all`) are called with the correct parameters.
2. **Uniqueness/Validations**: Assert that `HTTPException` (409 Conflict) is raised when unique constraints (like `name` or `identifier`) are violated.
3. **Not Found Cases**: Assert that `HTTPException` (404 Not Found) is raised for `get`, `update`, and `delete` when the entity does not exist in the mocked repository.
4. **Audit Logging (Diff Generation)**: When testing the `update` method, simulate the `audit_context` to ensure field modifications are correctly captured.

#### Example: Testing Audit Context Diff
```python
from app.core.context import audit_context

async def test_update_entity_diff(service, mock_repo):
    # Setup mock data...
    
    # Initialize the context variable
    token = audit_context.set({"diff": {}})
    
    try:
        # Call the service method
        result = await service.update_entity(entity_id, payload)
        
        # Verify the diff was captured
        ctx = audit_context.get()
        assert "diff" in ctx
        assert "field_name" in ctx["diff"]
        assert ctx["diff"]["field_name"]["old"] == "Old Value"
        assert ctx["diff"]["field_name"]["new"] == "New Value"
    finally:
        # Clean up the context
        audit_context.reset(token)
```

---

## 3. Router Layer Tests (`test_router.py`)

**Objective**: Test HTTP endpoints, query parameter parsing, routing, and JSON response serialization.

### Mocking the Service
Mock the `Service` layer using `unittest.mock.patch` with `AsyncMock`. The router tests should never execute the real service logic.

### Bypassing Authentication
Use `app.dependency_overrides` in an `autouse` fixture to bypass JWT validation and simulate an authenticated user context (like `ADMIN` or `USER`).

```python
import pytest
import uuid
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.infraestructure.models.user import User, GlobalRole

# Mock the user dependency
async def mock_require_authenticated():
    return User(id=uuid.uuid4(), email="test@admin.com", global_role=GlobalRole.ADMIN)

@pytest.fixture(autouse=True)
def override_dependencies():
    from app.middlewares.auth import require_authenticated
    app.dependency_overrides[require_authenticated] = mock_require_authenticated
    yield
    app.dependency_overrides.clear()
```

### Key Scenarios to Cover:
1. **HTTP Status Codes**: Verify endpoints return standard codes (200 OK, 201 Created, 204 No Content).
2. **Error Handling Propagation**: Mock the service to throw `HTTPException(404, "Not Found")` and verify the router propagates the 404 status.
3. **Query Parameters**: Verify that optional query parameters (like pagination `skip/limit` or custom filters) are parsed by FastAPI and passed correctly to the mocked service.

#### Example: Testing a Router Endpoint
```python
async def test_get_entity_not_found(async_client: AsyncClient):
    from fastapi import HTTPException
    
    # Patch the specific service method
    with patch("app.v1_0.modules.my_entity.service.MyEntityService.get_entity", new_callable=AsyncMock) as mock_get:
        # Simulate a 404 from the service
        mock_get.side_effect = HTTPException(status_code=404, detail="Not found")
        
        # Make the HTTP request
        response = await async_client.get(f"/api/v1/entities/{uuid.uuid4()}")
        
        # Assert the result
        assert response.status_code == 404
```

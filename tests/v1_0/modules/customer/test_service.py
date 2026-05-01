import pytest
import uuid
from unittest.mock import AsyncMock
from fastapi import HTTPException

from app.v1_0.modules.customer.service import CustomerService
from app.v1_0.modules.customer.domain import ICustomerRepository
from app.v1_0.modules.customer.dto.schemas import CustomerCreateDTO, CustomerUpdateDTO
from app.infraestructure.models.customer import Customer
from app.core.context import audit_context

@pytest.fixture
def mock_repo():
    return AsyncMock(spec=ICustomerRepository)

@pytest.fixture
def service(mock_repo):
    return CustomerService(mock_repo)

async def test_create_customer_success(service, mock_repo):
    payload = CustomerCreateDTO(
        name="Test User",
        identifier="12345",
        email="test@example.com",
        phone="555-1234",
        address="123 Test St"
    )
    
    mock_repo.get_by_identifier.return_value = None
    mock_repo.get_by_email.return_value = None
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    created_customer = Customer(
        id=uuid.uuid4(),
        name=payload.name,
        identifier=payload.identifier,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        created_at=now,
        updated_at=now
    )
    mock_repo.create.return_value = created_customer
    
    result = await service.create_customer(payload)
    
    assert result.name == payload.name
    assert result.identifier == payload.identifier
    assert result.email == payload.email
    mock_repo.create.assert_called_once()

async def test_create_customer_duplicate_identifier(service, mock_repo):
    payload = CustomerCreateDTO(
        name="Test User",
        identifier="12345",
        email="test@example.com"
    )
    mock_repo.get_by_identifier.return_value = Customer()
    
    with pytest.raises(HTTPException) as exc_info:
        await service.create_customer(payload)
    
    assert exc_info.value.status_code == 409
    assert "identifier" in exc_info.value.detail

async def test_create_customer_duplicate_email(service, mock_repo):
    payload = CustomerCreateDTO(
        name="Test User",
        identifier="12345",
        email="test@example.com"
    )
    mock_repo.get_by_identifier.return_value = None
    mock_repo.get_by_email.return_value = Customer()
    
    with pytest.raises(HTTPException) as exc_info:
        await service.create_customer(payload)
    
    assert exc_info.value.status_code == 409
    assert "email" in exc_info.value.detail

async def test_update_customer_diff(service, mock_repo):
    customer_id = uuid.uuid4()
    payload = CustomerUpdateDTO(name="Updated Name")
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    existing_customer = Customer(
        id=customer_id,
        name="Old Name",
        identifier="12345",
        email="test@example.com",
        created_at=now,
        updated_at=now
    )
    mock_repo.get_by_id.return_value = existing_customer
    
    updated_customer = Customer(
        id=customer_id,
        name="Updated Name",
        identifier="12345",
        email="test@example.com",
        created_at=now,
        updated_at=now
    )
    mock_repo.update.return_value = updated_customer
    
    token = audit_context.set({"diff": {}})
    
    try:
        result = await service.update_customer(customer_id, payload)
        
        assert result.name == "Updated Name"
        
        ctx = audit_context.get()
        assert "diff" in ctx
        assert "name" in ctx["diff"]
        assert ctx["diff"]["name"]["old"] == "Old Name"
        assert ctx["diff"]["name"]["new"] == "Updated Name"
    finally:
        audit_context.reset(token)

async def test_delete_customer_not_found(service, mock_repo):
    mock_repo.get_by_id.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await service.delete_customer(uuid.uuid4())
        
    assert exc_info.value.status_code == 404

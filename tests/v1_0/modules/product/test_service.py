import pytest
import uuid
from unittest.mock import AsyncMock
from fastapi import HTTPException

from app.v1_0.modules.product.service import ProductService
from app.v1_0.modules.product.domain import IProductRepository
from app.v1_0.modules.product.dto.schemas import ProductCreateDTO, ProductUpdateDTO
from app.infraestructure.models.product import Product, TransportMode, ProductSize
from app.core.context import audit_context

@pytest.fixture
def mock_repo():
    return AsyncMock(spec=IProductRepository)

@pytest.fixture
def service(mock_repo):
    return ProductService(mock_repo)

async def test_create_product_success(service, mock_repo):
    payload = ProductCreateDTO(
        name="Test Product",
        description="A test product",
        product_type="Electronics",
        transport_mode=TransportMode.LAND,
        size=ProductSize.MEDIUM
    )
    
    mock_repo.get_by_name.return_value = None
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    created_product = Product(
        id=uuid.uuid4(),
        name=payload.name,
        description=payload.description,
        product_type=payload.product_type,
        transport_mode=payload.transport_mode,
        size=payload.size,
        created_at=now
    )
    mock_repo.create.return_value = created_product
    
    result = await service.create_product(payload)
    
    assert result.name == payload.name
    assert result.product_type == payload.product_type
    assert result.transport_mode == payload.transport_mode
    assert result.size == payload.size
    mock_repo.create.assert_called_once()

async def test_create_product_duplicate_name(service, mock_repo):
    payload = ProductCreateDTO(
        name="Duplicate Product",
        product_type="Chemicals",
        transport_mode=TransportMode.MARITIME,
        size=ProductSize.LARGE
    )
    mock_repo.get_by_name.return_value = Product()
    
    with pytest.raises(HTTPException) as exc_info:
        await service.create_product(payload)
    
    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail

async def test_update_product_diff(service, mock_repo):
    product_id = uuid.uuid4()
    payload = ProductUpdateDTO(name="Updated Product Name")
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    existing_product = Product(
        id=product_id,
        name="Old Product Name",
        description="Old description",
        product_type="Electronics",
        transport_mode=TransportMode.LAND,
        size=ProductSize.SMALL,
        created_at=now
    )
    mock_repo.get_by_id.return_value = existing_product
    mock_repo.get_by_name.return_value = None
    
    updated_product = Product(
        id=product_id,
        name="Updated Product Name",
        description="Old description",
        product_type="Electronics",
        transport_mode=TransportMode.LAND,
        size=ProductSize.SMALL,
        created_at=now
    )
    mock_repo.update.return_value = updated_product
    
    token = audit_context.set({"diff": {}})
    
    try:
        result = await service.update_product(product_id, payload)
        
        assert result.name == "Updated Product Name"
        
        ctx = audit_context.get()
        assert "diff" in ctx
        assert "name" in ctx["diff"]
        assert ctx["diff"]["name"]["old"] == "Old Product Name"
        assert ctx["diff"]["name"]["new"] == "Updated Product Name"
    finally:
        audit_context.reset(token)

async def test_update_product_duplicate_name(service, mock_repo):
    product_id = uuid.uuid4()
    payload = ProductUpdateDTO(name="Existing Name")
    
    existing_product = Product(id=product_id, name="Old Name")
    mock_repo.get_by_id.return_value = existing_product
    
    another_product = Product(id=uuid.uuid4(), name="Existing Name")
    mock_repo.get_by_name.return_value = another_product
    
    with pytest.raises(HTTPException) as exc_info:
        await service.update_product(product_id, payload)
        
    assert exc_info.value.status_code == 409
    assert "already exists" in exc_info.value.detail

async def test_delete_product_not_found(service, mock_repo):
    mock_repo.get_by_id.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await service.delete_product(uuid.uuid4())
        
    assert exc_info.value.status_code == 404

async def test_list_products_no_filters(service, mock_repo):
    mock_repo.get_all.return_value = []
    mock_repo.count_all.return_value = 0
    
    result = await service.list_products(skip=10, limit=5)
    
    assert result.total == 0
    assert result.skip == 10
    assert result.limit == 5
    mock_repo.get_all.assert_called_once_with(skip=10, limit=5, transport_mode=None, size=None)
    mock_repo.count_all.assert_called_once_with(transport_mode=None, size=None)

async def test_list_products_with_filters(service, mock_repo):
    mock_repo.get_all.return_value = []
    mock_repo.count_all.return_value = 0
    
    result = await service.list_products(
        skip=0, 
        limit=10, 
        transport_mode=TransportMode.MARITIME, 
        size=ProductSize.EXTRA_LARGE
    )
    
    assert result.total == 0
    mock_repo.get_all.assert_called_once_with(
        skip=0, limit=10, transport_mode=TransportMode.MARITIME, size=ProductSize.EXTRA_LARGE
    )
    mock_repo.count_all.assert_called_once_with(
        transport_mode=TransportMode.MARITIME, size=ProductSize.EXTRA_LARGE
    )

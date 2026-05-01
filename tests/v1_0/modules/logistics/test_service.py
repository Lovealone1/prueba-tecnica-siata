import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from fastapi import HTTPException

from app.v1_0.modules.logistics.service import LogisticsNodeService
from app.infraestructure.models.warehouse import Warehouse
from app.v1_0.modules.logistics.dto.schemas import LogisticsNodeCreateDTO, LogisticsNodeUpdateDTO
from app.core.context import audit_context


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    # Testing the generic service using Warehouse as the model_class
    return LogisticsNodeService(repository=mock_repo, model_class=Warehouse)


def generate_mock_warehouse(id=None):
    return Warehouse(
        id=id or uuid.uuid4(),
        name="Test Warehouse",
        address="123 Test St",
        city="Test City",
        country="Colombia",
        continent="SOUTH AMERICA",
        created_at=datetime.now(timezone.utc),
    )


async def test_list_nodes(service, mock_repo):
    mock_item = generate_mock_warehouse()
    mock_repo.get_all.return_value = [mock_item]
    mock_repo.count_all.return_value = 1

    result = await service.list_nodes(skip=0, limit=10, continent="SOUTH AMERICA", country="Colombia")

    assert result.total == 1
    assert len(result.data) == 1
    assert result.data[0].id == mock_item.id
    mock_repo.get_all.assert_called_once_with(skip=0, limit=10, continent="SOUTH AMERICA", country="Colombia")
    mock_repo.count_all.assert_called_once_with(continent="SOUTH AMERICA", country="Colombia")


async def test_get_node_success(service, mock_repo):
    mock_item = generate_mock_warehouse()
    mock_repo.get_by_id.return_value = mock_item

    result = await service.get_node(mock_item.id)

    assert result.id == mock_item.id
    mock_repo.get_by_id.assert_called_once_with(mock_item.id)


async def test_get_node_not_found(service, mock_repo):
    mock_repo.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await service.get_node(uuid.uuid4())

    assert exc_info.value.status_code == 404


async def test_create_node(service, mock_repo):
    payload = LogisticsNodeCreateDTO(
        name="New Warehouse",
        address="456 New St",
        city="New City",
        country="Ecuador",
    )
    
    # We simulate the created node (the ORM model with populated fields)
    created_id = uuid.uuid4()
    mock_created = Warehouse(
        id=created_id,
        name=payload.name,
        address=payload.address,
        city=payload.city,
        country=payload.country,
        continent="SOUTH AMERICA",  # Simulating @validates behavior
        created_at=datetime.now(timezone.utc),
    )
    mock_repo.create.return_value = mock_created

    result = await service.create_node(payload)

    assert result.id == created_id
    assert result.name == "New Warehouse"
    mock_repo.create.assert_called_once()


async def test_update_node_success_with_diff(service, mock_repo):
    node_id = uuid.uuid4()
    original_node = generate_mock_warehouse(id=node_id)
    mock_repo.get_by_id.return_value = original_node

    payload = LogisticsNodeUpdateDTO(name="Updated Name")

    # Simulate updated node returned by repo
    updated_node = generate_mock_warehouse(id=node_id)
    updated_node.name = "Updated Name"
    mock_repo.update.return_value = updated_node

    # Initialize audit context
    token = audit_context.set({"diff": {}})

    try:
        result = await service.update_node(node_id, payload)

        assert result.name == "Updated Name"
        mock_repo.update.assert_called_once()

        # Check diff
        ctx = audit_context.get()
        assert "diff" in ctx
        assert "name" in ctx["diff"]
        assert ctx["diff"]["name"]["old"] == "Test Warehouse"
        assert ctx["diff"]["name"]["new"] == "Updated Name"
    finally:
        audit_context.reset(token)


async def test_update_node_not_found(service, mock_repo):
    mock_repo.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await service.update_node(uuid.uuid4(), LogisticsNodeUpdateDTO(name="Updated Name"))

    assert exc_info.value.status_code == 404


async def test_delete_node_success(service, mock_repo):
    mock_item = generate_mock_warehouse()
    mock_repo.get_by_id.return_value = mock_item

    await service.delete_node(mock_item.id)

    mock_repo.delete.assert_called_once_with(mock_item)


async def test_delete_node_not_found(service, mock_repo):
    mock_repo.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await service.delete_node(uuid.uuid4())

    assert exc_info.value.status_code == 404

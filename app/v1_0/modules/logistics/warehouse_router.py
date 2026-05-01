import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from dependency_injector.wiring import Provide, inject

from app.infraestructure.models.user import User, GlobalRole
from app.middlewares import require_roles, audit_log
from .dto.schemas import (
    LogisticsNodeCreateDTO,
    LogisticsNodeUpdateDTO,
    LogisticsNodeResponseDTO,
    LogisticsNodeListResponseDTO,
)
from .service import LogisticsNodeService

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])

_allowed_roles = Depends(require_roles(GlobalRole.USER, GlobalRole.ADMIN))


@router.get(
    "/",
    response_model=LogisticsNodeListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="List warehouses",
)
@inject
async def list_warehouses(
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum number of records")] = 100,
    continent: Annotated[Optional[str], Query(description="Filter by continent")] = None,
    country: Annotated[Optional[str], Query(description="Filter by country")] = None,
    _current_user: User = _allowed_roles,
    warehouse_service: LogisticsNodeService = Depends(Provide["warehouse_service"]),
) -> LogisticsNodeListResponseDTO:
    """Returns a paginated list of warehouses."""
    return await warehouse_service.list_nodes(
        skip=skip, limit=limit, continent=continent, country=country
    )


@router.get(
    "/{warehouse_id}",
    response_model=LogisticsNodeResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get warehouse by ID",
)
@inject
async def get_warehouse(
    warehouse_id: uuid.UUID,
    _current_user: User = _allowed_roles,
    warehouse_service: LogisticsNodeService = Depends(Provide["warehouse_service"]),
) -> LogisticsNodeResponseDTO:
    """Gets a specific warehouse by its UUID."""
    return await warehouse_service.get_node(warehouse_id)


@router.post(
    "/",
    response_model=LogisticsNodeResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create warehouse",
)
@inject
async def create_warehouse(
    payload: LogisticsNodeCreateDTO,
    _current_user: User = _allowed_roles,
    warehouse_service: LogisticsNodeService = Depends(Provide["warehouse_service"]),
) -> LogisticsNodeResponseDTO:
    """
    Creates a new warehouse.
    The `continent` field is automatically derived from `country`.
    """
    return await warehouse_service.create_node(payload)


@router.patch(
    "/{warehouse_id}",
    response_model=LogisticsNodeResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Partially update a warehouse",
)
@inject
async def update_warehouse(
    warehouse_id: uuid.UUID,
    payload: LogisticsNodeUpdateDTO,
    _audit_user: User = Depends(
        audit_log(
            action="warehouse.update",
            metadata={"entity": "Warehouse"},
            capture_body=True,
        )
    ),
    warehouse_service: LogisticsNodeService = Depends(Provide["warehouse_service"]),
) -> LogisticsNodeResponseDTO:
    """
    Partially updates a warehouse (PATCH).
    If `country` is updated, `continent` is re-derived automatically.
    The audit log interceptor registers who performed the operation.
    """
    return await warehouse_service.update_node(warehouse_id, payload)


@router.delete(
    "/{warehouse_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete warehouse",
)
@inject
async def delete_warehouse(
    warehouse_id: uuid.UUID,
    _audit_user: User = Depends(
        audit_log(action="warehouse.delete", metadata={"entity": "Warehouse"})
    ),
    warehouse_service: LogisticsNodeService = Depends(Provide["warehouse_service"]),
) -> None:
    """
    Deletes a warehouse.
    The audit log interceptor registers who performed the operation.
    """
    await warehouse_service.delete_node(warehouse_id)

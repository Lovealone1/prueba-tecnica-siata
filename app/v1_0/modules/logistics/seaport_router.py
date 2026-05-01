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

router = APIRouter(prefix="/seaports", tags=["Seaports"])

_allowed_roles = Depends(require_roles(GlobalRole.USER, GlobalRole.ADMIN))


@router.get(
    "/",
    response_model=LogisticsNodeListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="List seaports",
)
@inject
async def list_seaports(
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=200, description="Maximum number of records")] = 100,
    continent: Annotated[Optional[str], Query(description="Filter by continent")] = None,
    country: Annotated[Optional[str], Query(description="Filter by country")] = None,
    _current_user: User = _allowed_roles,
    seaport_service: LogisticsNodeService = Depends(Provide["seaport_service"]),
) -> LogisticsNodeListResponseDTO:
    """Returns a paginated list of seaports."""
    return await seaport_service.list_nodes(
        skip=skip, limit=limit, continent=continent, country=country
    )


@router.get(
    "/{seaport_id}",
    response_model=LogisticsNodeResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get seaport by ID",
)
@inject
async def get_seaport(
    seaport_id: uuid.UUID,
    _current_user: User = _allowed_roles,
    seaport_service: LogisticsNodeService = Depends(Provide["seaport_service"]),
) -> LogisticsNodeResponseDTO:
    """Gets a specific seaport by its UUID."""
    return await seaport_service.get_node(seaport_id)


@router.post(
    "/",
    response_model=LogisticsNodeResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create seaport",
)
@inject
async def create_seaport(
    payload: LogisticsNodeCreateDTO,
    _current_user: User = _allowed_roles,
    seaport_service: LogisticsNodeService = Depends(Provide["seaport_service"]),
) -> LogisticsNodeResponseDTO:
    """
    Creates a new seaport.
    The `continent` field is automatically derived from `country`.
    """
    return await seaport_service.create_node(payload)


@router.patch(
    "/{seaport_id}",
    response_model=LogisticsNodeResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Partially update a seaport",
)
@inject
async def update_seaport(
    seaport_id: uuid.UUID,
    payload: LogisticsNodeUpdateDTO,
    _audit_user: User = Depends(
        audit_log(
            action="seaport.update",
            metadata={"entity": "Seaport"},
            capture_body=True,
        )
    ),
    seaport_service: LogisticsNodeService = Depends(Provide["seaport_service"]),
) -> LogisticsNodeResponseDTO:
    """
    Partially updates a seaport (PATCH).
    If `country` is updated, `continent` is re-derived automatically.
    The audit log interceptor registers who performed the operation.
    """
    return await seaport_service.update_node(seaport_id, payload)


@router.delete(
    "/{seaport_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete seaport",
)
@inject
async def delete_seaport(
    seaport_id: uuid.UUID,
    _audit_user: User = Depends(
        audit_log(action="seaport.delete", metadata={"entity": "Seaport"})
    ),
    seaport_service: LogisticsNodeService = Depends(Provide["seaport_service"]),
) -> None:
    """
    Deletes a seaport.
    The audit log interceptor registers who performed the operation.
    """
    await seaport_service.delete_node(seaport_id)

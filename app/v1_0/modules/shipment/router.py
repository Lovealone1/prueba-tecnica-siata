import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from dependency_injector.wiring import Provide, inject

from app.v1_0.v1_containers import APIContainer
from app.v1_0.modules.shipment.service import ShipmentService
from app.v1_0.modules.shipment.dto.schemas import (
    ShipmentCreateDTO,
    ShipmentUpdateDTO,
    ShipmentResponseDTO,
    ShipmentListResponseDTO,
)
from app.middlewares.auth import require_authenticated
from app.middlewares.roles import require_roles
from app.infraestructure.models.user import GlobalRole

router = APIRouter(prefix="/shipments", tags=["Shipments"])

@router.post(
    "",
    response_model=ShipmentResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new shipment",
    dependencies=[Depends(require_authenticated)]
)
@inject
async def create_shipment(
    payload: ShipmentCreateDTO,
    shipment_service: ShipmentService = Depends(Provide[APIContainer.shipment_service])
):
    return await shipment_service.create(payload)

@router.get(
    "",
    response_model=ShipmentListResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="List shipments",
    dependencies=[Depends(require_authenticated)]
)
@inject
async def list_shipments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    shipment_service: ShipmentService = Depends(Provide[APIContainer.shipment_service])
):
    return await shipment_service.get_all(skip=skip, limit=limit)

@router.get(
    "/{shipment_id}",
    response_model=ShipmentResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get shipment by ID",
    dependencies=[Depends(require_authenticated)]
)
@inject
async def get_shipment_by_id(
    shipment_id: uuid.UUID,
    shipment_service: ShipmentService = Depends(Provide[APIContainer.shipment_service])
):
    return await shipment_service.get_by_id(shipment_id)

@router.patch(
    "/{shipment_id}",
    response_model=ShipmentResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update shipment (tracking)",
    dependencies=[Depends(require_authenticated)]
)
@inject
async def update_shipment(
    shipment_id: uuid.UUID,
    payload: ShipmentUpdateDTO,
    shipment_service: ShipmentService = Depends(Provide[APIContainer.shipment_service])
):
    return await shipment_service.update(shipment_id, payload)

@router.delete(
    "/{shipment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete shipment",
    dependencies=[Depends(require_authenticated), Depends(require_roles(GlobalRole.ADMIN))]
)
@inject
async def delete_shipment(
    shipment_id: uuid.UUID,
    shipment_service: ShipmentService = Depends(Provide[APIContainer.shipment_service])
):
    await shipment_service.delete(shipment_id)

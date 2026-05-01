import uuid
from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from dependency_injector.wiring import Provide, inject

from app.v1_0.v1_containers import APIContainer
from app.v1_0.modules.shipment.service import ShipmentService
from app.v1_0.modules.shipment.dto.schemas import (
    ShipmentCreateDTO,
    ShipmentUpdateDTO,
    ShipmentResponseDTO,
    ShipmentListResponseDTO,
    ShipmentStatusLogResponseDTO,
    ShipmentAdminUpdateDTO,
    ShipmentAdminStatsDTO
)
from app.middlewares.auth import require_authenticated
from app.middlewares.roles import require_roles
from app.infraestructure.models.user import GlobalRole
from app.infraestructure.models.shipment import ShippingType, ShippingStatus

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
    customer_id: Optional[uuid.UUID] = Query(None),
    dispatch_location: Optional[str] = Query(None),
    destination_country: Optional[str] = Query(None),
    shipping_type: Optional[ShippingType] = Query(None),
    shipping_status: Optional[ShippingStatus] = Query(None),
    guide_number: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    shipment_service: ShipmentService = Depends(Provide[APIContainer.shipment_service])
):
    return await shipment_service.get_all(
        skip=skip, 
        limit=limit,
        customer_id=customer_id,
        dispatch_location=dispatch_location,
        destination_country=destination_country,
        shipping_type=shipping_type,
        shipping_status=shipping_status,
        guide_number=guide_number,
        start_date=start_date,
        end_date=end_date
    )

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

# --- ADMIN ENDPOINTS ---

@router.get(
    "/admin/stats",
    response_model=ShipmentAdminStatsDTO,
    status_code=status.HTTP_200_OK,
    summary="[ADMIN] Get logistics statistics",
    dependencies=[Depends(require_roles(GlobalRole.ADMIN))]
)
@inject
async def get_admin_stats(
    shipment_service: ShipmentService = Depends(Provide[APIContainer.shipment_service])
):
    return await shipment_service.get_admin_stats()

@router.get(
    "/admin/{shipment_id}/history",
    response_model=list[ShipmentStatusLogResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="[ADMIN] Get status history for a shipment",
    dependencies=[Depends(require_roles(GlobalRole.ADMIN))]
)
@inject
async def get_shipment_history(
    shipment_id: uuid.UUID,
    shipment_service: ShipmentService = Depends(Provide[APIContainer.shipment_service])
):
    return await shipment_service.get_status_history(shipment_id)

@router.patch(
    "/admin/{shipment_id}/status",
    response_model=ShipmentResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="[ADMIN] Override shipment status",
    dependencies=[Depends(require_roles(GlobalRole.ADMIN))]
)
@inject
async def admin_update_shipment_status(
    shipment_id: uuid.UUID,
    payload: ShipmentAdminUpdateDTO,
    shipment_service: ShipmentService = Depends(Provide[APIContainer.shipment_service])
):
    return await shipment_service.admin_update_status(shipment_id, payload)

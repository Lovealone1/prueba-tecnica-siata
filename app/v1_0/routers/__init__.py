from typing import List
from fastapi import APIRouter

from app.v1_0.modules.auth.router import router as auth_router
from app.v1_0.modules.customer.router import router as customer_router
from app.v1_0.modules.product.router import router as product_router
from app.v1_0.modules.logistics.warehouse_router import router as warehouse_router
from app.v1_0.modules.logistics.seaport_router import router as seaport_router
from app.v1_0.modules.shipment.router import router as shipment_router
from app.v1_0.modules.user.router import router as user_router
from app.v1_0.modules.report.router import router as report_router

defined_routers: List[APIRouter] = [
    auth_router,
    customer_router,
    product_router,
    warehouse_router,
    seaport_router,
    shipment_router,
    user_router,
    report_router,
]

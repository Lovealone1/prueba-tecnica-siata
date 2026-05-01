from typing import List
from fastapi import APIRouter

from app.v1_0.modules.auth.router import router as auth_router
from app.v1_0.modules.customer.router import router as customer_router

defined_routers: List[APIRouter] = [
    auth_router,
    customer_router,
]

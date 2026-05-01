from typing import List
from fastapi import APIRouter

from app.v1_0.modules.auth.router import router as auth_router

defined_routers: List[APIRouter] = [
    auth_router,
]

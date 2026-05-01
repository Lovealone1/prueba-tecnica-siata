from typing import List
from fastapi import APIRouter

from app.v1_0.auth.router import router as auth_router

defined_routers: List[APIRouter] = [
    auth_router,
]

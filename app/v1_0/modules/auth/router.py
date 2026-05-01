from fastapi import APIRouter, Depends, Request, status
from dependency_injector.wiring import Provide, inject
import uuid
from typing import List

from typing import List
from .dto.schemas import (
    OTPRequest, OTPVerifyRequest, AuthResponse, SessionResponse, AuthMeResponse
)
from .service import AuthService
from .dependencies import get_current_user, get_current_sid
from app.infraestructure.models.user import User

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/otp", status_code=status.HTTP_200_OK)
@inject
async def request_otp(
    payload: OTPRequest,
    auth_service: AuthService = Depends(Provide["auth_service"])
):
    await auth_service.request_otp(payload.email, payload.intent)
    return {"message": "OTP sent to email"}

@router.post("/otp/verify", response_model=AuthResponse)
@inject
async def verify_otp(
    payload: OTPVerifyRequest,
    request: Request,
    auth_service: AuthService = Depends(Provide["auth_service"])
):
    """
    Verify the OTP provided by the user.
    - If intent is REGISTER, registration_data is REQUIRED.
    - If intent is LOGIN, registration_data is ignored.
    """
    ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    return await auth_service.verify_otp(
        email=payload.email,
        intent=payload.intent,
        otp=payload.otp,
        registration_data=payload.registration_data,
        ip=ip,
        user_agent=user_agent
    )


@router.get("/sessions", response_model=List[SessionResponse])
@inject
async def get_sessions(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(Provide["auth_service"])
):
    return await auth_service.get_sessions(current_user.id)

@router.post("/logout")
@inject
async def logout(
    current_user: User = Depends(get_current_user),
    sid: str = Depends(get_current_sid),
    auth_service: AuthService = Depends(Provide["auth_service"])
):
    await auth_service.revoke_session(current_user.id, sid)
    return {"message": "Logged out successfully"}

@router.post("/logout-all")
@inject
async def logout_all(
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(Provide["auth_service"])
):
    await auth_service.revoke_all_sessions(current_user.id)
    return {"message": "All sessions revoked"}

@router.delete("/sessions/{sid}")
@inject
async def revoke_session(
    sid: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(Provide["auth_service"])
):
    await auth_service.revoke_session(current_user.id, sid)
    return {"message": "Session revoked"}

@router.get("/me", response_model=AuthMeResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Check if the user is logged in and return their profile and role.
    """
    return {
        "is_logged_in": True,
        "role": current_user.global_role.value if hasattr(current_user.global_role, 'value') else current_user.global_role,
        "user": current_user
    }


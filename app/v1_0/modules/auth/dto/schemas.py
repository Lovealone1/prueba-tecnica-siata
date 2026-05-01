from pydantic import BaseModel, EmailStr, Field
from typing import Literal, Optional
from datetime import datetime
import uuid

class OTPRequest(BaseModel):
    email: EmailStr
    intent: Literal["LOGIN", "REGISTER"]

class RegistrationData(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=255)

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    intent: Literal["LOGIN", "REGISTER"]
    otp: str = Field(..., min_length=6, max_length=6)
    registration_data: Optional[RegistrationData] = Field(
        None, 
        description="Required if intent is REGISTER. Contains user profile information."
    )

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    phone_number: Optional[str]
    is_active: bool
    global_role: str

class AuthResponse(BaseModel):
    message: str
    accessToken: str
    user: UserResponse

class SessionResponse(BaseModel):
    sid: str
    ip: Optional[str] = None
    userAgent: Optional[str] = None
    created_at: datetime

class AuthMeResponse(BaseModel):
    is_logged_in: bool
    role: str
    user: UserResponse



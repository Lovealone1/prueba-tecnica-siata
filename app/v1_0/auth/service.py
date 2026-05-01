import random
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from app.core.settings import settings
from app.infraestructure.models.user import User, GlobalRole
from app.infraestructure.redis.redis_cache_service import RedisCacheService
from .dto.schemas import UserResponse, SessionResponse
from .repository import UserRepository
from .otp import OtpSender
from fastapi import HTTPException, status

class AuthService:
    """
    Service responsible for handling authentication logic, including OTP generation,
    verification, session management, and JWT issuance.
    """
    def __init__(
        self,
        user_repository: UserRepository,
        redis_cache: RedisCacheService,
        otp_sender: OtpSender
    ):
        self.user_repository = user_repository
        self.redis = redis_cache
        self.otp_sender = otp_sender
        self.otp_ttl = 300
        self.max_attempts = 3
        self.jwt_secret = settings.JWT_SECRET
        self.jwt_expires = settings.JWT_EXPIRES_IN_MINUTES

    async def request_otp(self, email: str, intent: str) -> None:
        """
        Generates and sends a One-Time Password (OTP) to the specified email.
        If a valid OTP already exists in the cache, it is reused.
        """
        email = email.lower().strip()
        otp_key = f"otp:{email}"
        attempts_key = f"otp_attempts:{email}"

        existing_otp = await self.redis.get(otp_key)
        if existing_otp:
            otp = existing_otp
        else:
            otp = f"{random.randint(0, 999999):06d}"
            await self.redis.set(otp_key, otp, ttl_seconds=self.otp_ttl)
            await self.redis.delete(attempts_key)
            
        await self.otp_sender.send(email, otp, intent)

    async def verify_otp(
        self, 
        email: str, 
        intent: str, 
        otp: str, 
        registration_data: Optional[Any] = None,
        ip: str = None, 
        user_agent: str = None
    ) -> dict:
        """
        Verifies the provided OTP and completes the authentication flow.
        For REGISTER intent, it creates the user profile.
        For LOGIN intent, it validates the existing user.
        On success, it creates a stateful session in Redis and returns a JWT.
        """
        email = email.lower().strip()
        otp_key = f"otp:{email}"
        attempts_key = f"otp_attempts:{email}"

        stored_otp = await self.redis.get(otp_key)
        if not stored_otp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired or not requested")

        attempts = await self.redis.incr(attempts_key, ttl_seconds=self.otp_ttl)
        if attempts > self.max_attempts:
            await self.redis.delete(otp_key)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many failed attempts. Request a new OTP.")

        if str(stored_otp) != otp:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

        await self.redis.delete(otp_key)
        await self.redis.delete(attempts_key)

        user = await self.user_repository.get_by_email(email)

        if intent == "LOGIN":
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            if not user.is_active:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
        elif intent == "REGISTER":
            if user:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already exists")
            
            if not registration_data:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration data is required for REGISTER intent")
                
            user = User(
                email=email,
                first_name=registration_data.first_name,
                last_name=registration_data.last_name,
                phone_number=registration_data.phone_number
            )
            user = await self.user_repository.create(user)

        user.last_login_at = datetime.now(timezone.utc)
        await self.user_repository.commit_user(user)

        sid = str(uuid.uuid4())
        session_key = f"session:{user.id}:{sid}"
        session_data = {
            "sid": sid,
            "ip": ip,
            "userAgent": user_agent,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await self.redis.set(session_key, session_data, ttl_seconds=self.jwt_expires * 60)
        await self.redis.sadd(f"user_sessions:{user.id}", sid)

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.global_role.value if hasattr(user.global_role, 'value') else user.global_role,
            "sid": sid,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=self.jwt_expires)
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")

        user_dict = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "is_active": user.is_active,
            "global_role": user.global_role.value if hasattr(user.global_role, 'value') else user.global_role
        }

        return {
            "message": "Authenticated successfully",
            "accessToken": token,
            "user": user_dict
        }

    async def get_sessions(self, user_id: uuid.UUID) -> List[SessionResponse]:
        """
        Retrieves all active sessions for a specific user from Redis.
        Cleans up orphaned session identifiers if the session data is no longer present.
        """
        sids = await self.redis.smembers(f"user_sessions:{user_id}")
        sessions = []
        for sid in sids:
            session_data = await self.redis.get(f"session:{user_id}:{sid}")
            if session_data:
                sessions.append(SessionResponse(**session_data))
            else:
                await self.redis.srem(f"user_sessions:{user_id}", sid)
        return sessions

    async def revoke_session(self, user_id: uuid.UUID, sid: str) -> None:
        """
        Revokes a specific session for a user by deleting its data and removing it from the user's session set.
        """
        await self.redis.delete(f"session:{user_id}:{sid}")
        await self.redis.srem(f"user_sessions:{user_id}", sid)

    async def revoke_all_sessions(self, user_id: uuid.UUID) -> None:
        """
        Revokes all active sessions for a user, effectively logging them out from all devices.
        """
        sids = await self.redis.smembers(f"user_sessions:{user_id}")
        for sid in sids:
            await self.redis.delete(f"session:{user_id}:{sid}")
        await self.redis.delete(f"user_sessions:{user_id}")


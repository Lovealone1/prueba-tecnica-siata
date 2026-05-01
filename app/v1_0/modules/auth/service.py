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
        """
        Initializes the service with security settings and required infrastructure.

        Args:
            user_repository: Data access layer for user persistence.
            redis_cache: Redis service for OTP storage and session management.
            otp_sender: Notification service for delivering OTPs.
        """
        self.user_repository = user_repository
        self.redis = redis_cache
        self.otp_sender = otp_sender
        self.otp_ttl = 300
        self.max_attempts = 3
        self.jwt_secret = settings.JWT_SECRET
        self.jwt_expires = settings.JWT_EXPIRES_IN_MINUTES

    async def request_otp(self, email: str, intent: str) -> None:
        """
        Generates and dispatches a One-Time Password (OTP) for authentication.

        Workflow:
        1. Normalizes the email address.
        2. Checks for an existing unexpired OTP in Redis to avoid redundant generation.
        3. If none exists, generates a random 6-digit OTP and stores it with a TTL.
        4. Invokes the OtpSender to deliver the code to the user.

        Args:
            email: The recipient's email address.
            intent: The purpose of the OTP (e.g., LOGIN, REGISTER).
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
        Verifies an OTP and establishes an authenticated session.

        Workflow:
        1. Validates the existence and correctness of the OTP in Redis.
        2. Enforces a maximum attempt limit to prevent brute-force attacks.
        3. For REGISTER: Creates a new User profile with the provided metadata.
        4. For LOGIN: Verifies the existing user is active and eligible to sign in.
        5. Generates a unique Session ID (SID) and persists session metadata in Redis.
        6. Issues a signed JWT containing user identity and session context.

        Args:
            email: The user's email address.
            intent: The authentication purpose (LOGIN/REGISTER).
            otp: The 6-digit code provided by the user.
            registration_data: Metadata required only for new user registration.
            ip: Client's IP address for session tracking.
            user_agent: Client's browser/device info for session tracking.

        Returns:
            A dictionary containing the access token and user profile summary.

        Raises:
            HTTPException:
                - 400: If OTP is invalid, expired, or failed attempts are exceeded.
                - 404: If the user is not found during LOGIN.
                - 403: If the user account is disabled.
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

        # Cache user profile for high-performance retrieval in dependencies
        await self._cache_user_profile(user)

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
        Retrieves all active authentication sessions for a specific user.

        Workflow:
        1. Queries Redis for the set of active session IDs associated with the user.
        2. Iterates through each session ID to fetch detailed metadata.
        3. Performs self-healing by removing session IDs from the set if their underlying data has expired.

        Args:
            user_id: The unique identifier of the user.

        Returns:
            A list of SessionResponse objects containing IP, user agent, and creation date.
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
        Invalidates a specific active session.

        Args:
            user_id: The unique identifier of the user.
            sid: The unique identifier of the session to revoke.
        """
        await self.redis.delete(f"session:{user_id}:{sid}")
        await self.redis.srem(f"user_sessions:{user_id}", sid)

    async def revoke_all_sessions(self, user_id: uuid.UUID) -> None:
        """
        Logs out a user from all devices by invalidating all active sessions.

        Args:
            user_id: The unique identifier of the user to log out globally.
        """
        sids = await self.redis.smembers(f"user_sessions:{user_id}")
        for sid in sids:
            await self.redis.delete(f"session:{user_id}:{sid}")
        await self.redis.delete(f"user_sessions:{user_id}")
        await self.redis.delete(f"user:profile:{user_id}")

    async def _cache_user_profile(self, user: User) -> None:
        """
        Stores a serialized version of the user profile in Redis.
        Used to avoid redundant database lookups during request authentication.
        """
        profile_data = {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "is_active": user.is_active,
            "global_role": user.global_role.value if hasattr(user.global_role, 'value') else user.global_role
        }
        await self.redis.set(
            f"user:profile:{user.id}", 
            profile_data, 
            ttl_seconds=3600 # Cache for 1 hour
        )


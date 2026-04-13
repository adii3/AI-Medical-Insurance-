from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from core.config import settings
from core.security import (
    create_access_token,
    generate_opaque_token,
    generate_otp_code,
    get_password_hash,
    hash_token,
    verify_password,
)
from models.models import MfaChallenge, PasswordResetToken, SessionToken, User
from schemas.schemas import (
    AuthTokensResponse,
    LoginChallengeResponse,
    MfaVerifyRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    SignupResponse,
    UserLogin,
    UserSignup,
    UserSummary,
)
from services.analytics_service import AnalyticsService


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.analytics = AnalyticsService(db)

    def ensure_bootstrap_admin(self) -> None:
        if not settings.admin_bootstrap_email or not settings.admin_bootstrap_password:
            return

        existing = self.db.query(User).filter(User.email == settings.admin_bootstrap_email).first()
        if existing:
            if existing.role != "admin":
                existing.role = "admin"
                self.db.commit()
            return

        admin = User(
            email=settings.admin_bootstrap_email,
            hashed_password=get_password_hash(settings.admin_bootstrap_password),
            role="admin",
            tenant_name=settings.admin_bootstrap_tenant,
            onboarded=True,
        )
        self.db.add(admin)
        self.db.commit()

    def signup(self, payload: UserSignup) -> SignupResponse:
        existing = self.db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            role="user",
            tenant_name=payload.tenant_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        self.analytics.record_event(
            event_name="auth.signup",
            feature_type="auth",
            endpoint="/api/v1/auth/signup",
            method="POST",
            user=user,
            status_code=201,
            success=True,
            latency_ms=0.0,
        )
        return SignupResponse(message="Account created successfully.", user=UserSummary.model_validate(user))

    def login(self, payload: UserLogin) -> LoginChallengeResponse:
        user = self.db.query(User).filter(User.email == payload.email).first()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status_code=400, detail="Inactive user")

        challenge = MfaChallenge(
            user_id=user.id,
            purpose="login",
            otp_code=generate_otp_code(),
            expires_at=_utcnow() + timedelta(minutes=settings.mfa_code_expire_minutes),
        )
        self.db.add(challenge)
        self.db.commit()
        self.db.refresh(challenge)
        self.analytics.record_event(
            event_name="auth.login.challenge",
            feature_type="auth",
            endpoint="/api/v1/auth/login",
            method="POST",
            user=user,
            status_code=200,
            success=True,
            latency_ms=0.0,
        )
        return LoginChallengeResponse(
            challenge_id=challenge.id,
            challenge_expires_at=challenge.expires_at,
            otp_code_preview=challenge.otp_code if settings.debug_token_previews or settings.testing else None,
            message="Credentials verified. Complete MFA to receive tokens.",
        )

    def verify_mfa(self, payload: MfaVerifyRequest) -> AuthTokensResponse:
        challenge = self.db.query(MfaChallenge).filter(MfaChallenge.id == payload.challenge_id).first()
        if challenge is None:
            raise HTTPException(status_code=404, detail="MFA challenge not found")
        if challenge.consumed_at is not None or challenge.verified_at is not None:
            raise HTTPException(status_code=400, detail="MFA challenge already used")
        if _coerce_utc(challenge.expires_at) <= _utcnow():
            raise HTTPException(status_code=400, detail="MFA challenge expired")
        if challenge.otp_code != payload.otp:
            raise HTTPException(status_code=400, detail="Invalid OTP code")

        user = self.db.query(User).filter(User.id == challenge.user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        challenge.verified_at = _utcnow()
        challenge.consumed_at = _utcnow()
        refresh_token = generate_opaque_token()
        session = SessionToken(
            user_id=user.id,
            refresh_token_hash=hash_token(refresh_token),
            expires_at=_utcnow() + timedelta(minutes=settings.refresh_token_expire_minutes),
            last_seen_at=_utcnow(),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        access_token = create_access_token(subject=user.email, role=user.role, session_id=session.id)
        self.analytics.record_event(
            event_name="auth.login.verify",
            feature_type="auth",
            endpoint="/api/v1/auth/mfa/verify",
            method="POST",
            user=user,
            status_code=200,
            success=True,
            latency_ms=0.0,
        )
        return AuthTokensResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in_seconds=settings.access_token_expire_minutes * 60,
            user=UserSummary.model_validate(user),
        )

    def refresh(self, refresh_token: str) -> AuthTokensResponse:
        hashed = hash_token(refresh_token)
        session = (
            self.db.query(SessionToken)
            .filter(SessionToken.refresh_token_hash == hashed, SessionToken.revoked_at.is_(None))
            .first()
        )
        if session is None or _coerce_utc(session.expires_at) <= _utcnow():
            raise HTTPException(status_code=401, detail="Refresh token is invalid or expired")

        user = self.db.query(User).filter(User.id == session.user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        new_refresh_token = generate_opaque_token()
        session.refresh_token_hash = hash_token(new_refresh_token)
        session.last_seen_at = _utcnow()
        self.db.commit()
        access_token = create_access_token(subject=user.email, role=user.role, session_id=session.id)
        return AuthTokensResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in_seconds=settings.access_token_expire_minutes * 60,
            user=UserSummary.model_validate(user),
        )

    def logout(self, session_id: str, user: User) -> None:
        session = (
            self.db.query(SessionToken)
            .filter(SessionToken.id == session_id, SessionToken.user_id == user.id, SessionToken.revoked_at.is_(None))
            .first()
        )
        if session:
            session.revoked_at = _utcnow()
            self.db.commit()
        self.analytics.record_event(
            event_name="auth.logout",
            feature_type="auth",
            endpoint="/api/v1/auth/logout",
            method="POST",
            user=user,
            status_code=200,
            success=True,
            latency_ms=0.0,
        )

    def request_password_reset(self, payload: PasswordResetRequest) -> PasswordResetRequestResponse:
        user = self.db.query(User).filter(User.email == payload.email).first()
        reset_token_preview = None
        if user:
            raw_token = generate_opaque_token()
            token = PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=_utcnow() + timedelta(minutes=settings.password_reset_expire_minutes),
            )
            self.db.add(token)
            self.db.commit()
            reset_token_preview = raw_token if settings.debug_token_previews or settings.testing else None
            self.analytics.record_event(
                event_name="auth.password_reset.request",
                feature_type="auth",
                endpoint="/api/v1/auth/password-reset/request",
                method="POST",
                user=user,
                status_code=200,
                success=True,
                latency_ms=0.0,
            )

        return PasswordResetRequestResponse(
            message="If that account exists, a reset token has been issued.",
            reset_token_preview=reset_token_preview,
        )

    def confirm_password_reset(self, payload: PasswordResetConfirm) -> None:
        token = (
            self.db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.token_hash == hash_token(payload.reset_token),
                PasswordResetToken.used_at.is_(None),
            )
            .first()
        )
        if token is None or _coerce_utc(token.expires_at) <= _utcnow():
            raise HTTPException(status_code=400, detail="Reset token is invalid or expired")

        user = self.db.query(User).filter(User.id == token.user_id).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        user.hashed_password = get_password_hash(payload.new_password)
        token.used_at = _utcnow()
        self.db.commit()
        self.analytics.record_event(
            event_name="auth.password_reset.confirm",
            feature_type="auth",
            endpoint="/api/v1/auth/password-reset/confirm",
            method="POST",
            user=user,
            status_code=200,
            success=True,
            latency_ms=0.0,
        )

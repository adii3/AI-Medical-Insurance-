from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_active_user, get_current_token_payload
from models.models import User
from schemas.schemas import (
    AuthTokensResponse,
    LoginChallengeResponse,
    LogoutResponse,
    MfaVerifyRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RefreshTokenRequest,
    SignupResponse,
    UserLogin,
    UserSignup,
)
from services.auth_service import AuthService


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
def signup(user: UserSignup, db: Session = Depends(get_db)):
    return AuthService(db).signup(user)


@router.post("/login", response_model=LoginChallengeResponse)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    return AuthService(db).login(user_data)


@router.post("/mfa/verify", response_model=AuthTokensResponse)
def verify_mfa(payload: MfaVerifyRequest, db: Session = Depends(get_db)):
    return AuthService(db).verify_mfa(payload)


@router.post("/refresh", response_model=AuthTokensResponse)
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    return AuthService(db).refresh(payload.refresh_token)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    current_user: User = Depends(get_current_active_user),
    token_payload: dict = Depends(get_current_token_payload),
    db: Session = Depends(get_db),
):
    AuthService(db).logout(token_payload["sid"], current_user)
    return LogoutResponse(message="Session logged out successfully.")


@router.post("/password-reset/request", response_model=PasswordResetRequestResponse)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    return AuthService(db).request_password_reset(payload)


@router.post("/password-reset/confirm", response_model=LogoutResponse)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    AuthService(db).confirm_password_reset(payload)
    return LogoutResponse(message="Password reset successfully.")

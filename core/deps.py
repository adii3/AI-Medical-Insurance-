from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import decode_token
from models.models import SessionToken, User


bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def get_current_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise _unauthorized() from exc
    return payload


def get_current_user(
    payload: dict = Depends(get_current_token_payload),
    db: Session = Depends(get_db),
):
    email = payload.get("sub")
    session_id = payload.get("sid")
    if not email or not session_id:
        raise _unauthorized()

    session = (
        db.query(SessionToken)
        .filter(SessionToken.id == session_id, SessionToken.revoked_at.is_(None))
        .first()
    )
    if session is None or _coerce_utc(session.expires_at) <= datetime.now(timezone.utc):
        raise _unauthorized("Session is no longer active")

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise _unauthorized()

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

import os

from pydantic_settings import BaseSettings


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class _Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    jwt_secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 14
    mfa_code_expire_minutes: int = 10
    password_reset_expire_minutes: int = 30
    database_url: str = "sqlite:///./medical_ai.db"
    redis_url: str = "redis://redis:6379/0"
    app_environment: str = "development"
    model_name: str = "medical-insurance-xgboost"
    model_version: str = "v2"
    testing: bool = False
    disable_model_training: bool = False
    debug_token_previews: bool = True
    admin_bootstrap_email: str = "admin@example.com"
    admin_bootstrap_password: str = "ChangeMe123!"
    admin_bootstrap_tenant: str = "Northern Shield"

    model_config = {"extra": "ignore", "protected_namespaces": ()}


def _build_settings() -> _Settings:
    """Build settings, mapping docker-compose env var names to our field names."""
    overrides = {
        "testing": _env_bool("TESTING", False),
        "disable_model_training": _env_bool("DISABLE_MODEL_TRAINING", False),
        "debug_token_previews": _env_bool("DEBUG_TOKEN_PREVIEWS", True),
    }
    if os.getenv("SECRET_KEY"):
        overrides["jwt_secret_key"] = os.getenv("SECRET_KEY")
    if os.getenv("ALGORITHM"):
        overrides["jwt_algorithm"] = os.getenv("ALGORITHM")
    if os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"):
        overrides["access_token_expire_minutes"] = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    if os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"):
        overrides["refresh_token_expire_minutes"] = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES"))
    if os.getenv("MFA_CODE_EXPIRE_MINUTES"):
        overrides["mfa_code_expire_minutes"] = int(os.getenv("MFA_CODE_EXPIRE_MINUTES"))
    if os.getenv("PASSWORD_RESET_EXPIRE_MINUTES"):
        overrides["password_reset_expire_minutes"] = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES"))
    if os.getenv("DATABASE_URL"):
        overrides["database_url"] = os.getenv("DATABASE_URL")
    if os.getenv("REDIS_URL"):
        overrides["redis_url"] = os.getenv("REDIS_URL")
    if os.getenv("APP_ENVIRONMENT"):
        overrides["app_environment"] = os.getenv("APP_ENVIRONMENT")
    if os.getenv("MODEL_NAME"):
        overrides["model_name"] = os.getenv("MODEL_NAME")
    if os.getenv("MODEL_VERSION"):
        overrides["model_version"] = os.getenv("MODEL_VERSION")
    if os.getenv("ADMIN_BOOTSTRAP_EMAIL"):
        overrides["admin_bootstrap_email"] = os.getenv("ADMIN_BOOTSTRAP_EMAIL")
    if os.getenv("ADMIN_BOOTSTRAP_PASSWORD"):
        overrides["admin_bootstrap_password"] = os.getenv("ADMIN_BOOTSTRAP_PASSWORD")
    if os.getenv("ADMIN_BOOTSTRAP_TENANT"):
        overrides["admin_bootstrap_tenant"] = os.getenv("ADMIN_BOOTSTRAP_TENANT")
    return _Settings(**overrides)


settings = _build_settings()

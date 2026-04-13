from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from constants import REGIONS, SEXES, TIERS


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ErrorResponse(BaseModel):
    detail: str
    status: str = "error"


class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    tenant_name: str = Field(default="Northern Shield", min_length=2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class MfaVerifyRequest(BaseModel):
    challenge_id: str
    otp: str = Field(..., min_length=6, max_length=6)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=20)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    reset_token: str = Field(..., min_length=20)
    new_password: str = Field(..., min_length=8)


class LogoutResponse(BaseModel):
    message: str
    status: str = "ok"


class UserSummary(BaseModel):
    id: int
    email: EmailStr
    role: str
    tenant_name: str
    onboarded: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SignupResponse(BaseModel):
    message: str
    user: UserSummary


class LoginChallengeResponse(BaseModel):
    challenge_id: str
    mfa_required: bool = True
    challenge_expires_at: datetime
    otp_code_preview: Optional[str] = None
    message: str


class AuthTokensResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: UserSummary


class PasswordResetRequestResponse(BaseModel):
    message: str
    reset_token_preview: Optional[str] = None


class OnboardingRequest(BaseModel):
    consent_version: str = Field(default="2026-03")
    consent_accepted: bool
    platform_purpose_seen: bool
    data_use_summary_seen: bool


class OnboardingResponse(BaseModel):
    message: str
    onboarded: bool
    consent_version: str


class PatientProfileInput(BaseModel):
    age: int = Field(..., ge=18, le=90)
    bmi: float = Field(..., ge=15.0, le=55.0)
    smoker_status: bool
    dependents: int = Field(..., ge=0, le=10)
    region: str
    sex: str
    recent_hospitalizations: int = Field(default=0, ge=0, le=10)
    base_risk_score: float = Field(default=20.0, ge=0.0, le=100.0)
    subscription_tier: str = Field(default="Standard")
    tenant_company: Optional[str] = None
    consent_to_model_improvement: bool = True

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: str) -> str:
        if value not in REGIONS:
            raise ValueError(f"region must be one of: {', '.join(REGIONS)}")
        return value

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, value: str) -> str:
        if value not in SEXES:
            raise ValueError(f"sex must be one of: {', '.join(SEXES)}")
        return value

    @field_validator("subscription_tier")
    @classmethod
    def validate_tier(cls, value: str) -> str:
        if value not in TIERS:
            raise ValueError(f"subscription_tier must be one of: {', '.join(TIERS)}")
        return value


class PatientProfileResponse(PatientProfileInput):
    id: int
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpsertResponse(BaseModel):
    message: str
    profile: PatientProfileResponse


class PredictionRequest(BaseModel):
    profile: PatientProfileInput
    persist_profile: bool = True


class WhatIfOverrides(BaseModel):
    bmi: Optional[float] = Field(default=None, ge=15.0, le=55.0)
    smoker_status: Optional[bool] = None
    dependents: Optional[int] = Field(default=None, ge=0, le=10)
    region: Optional[str] = None
    recent_hospitalizations: Optional[int] = Field(default=None, ge=0, le=10)
    base_risk_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    subscription_tier: Optional[str] = None

    @field_validator("region")
    @classmethod
    def validate_region(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in REGIONS:
            raise ValueError(f"region must be one of: {', '.join(REGIONS)}")
        return value

    @field_validator("subscription_tier")
    @classmethod
    def validate_tier(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in TIERS:
            raise ValueError(f"subscription_tier must be one of: {', '.join(TIERS)}")
        return value


class WhatIfRequest(BaseModel):
    overrides: WhatIfOverrides
    profile: Optional[PatientProfileInput] = None


class ExplainabilityFactor(BaseModel):
    feature_name: str
    value: float
    direction: str
    plain_language: str


class PredictionResponse(BaseModel):
    premium_estimate_monthly: float
    risk_probability: float
    risk_level: str
    confidence_indicator: str
    explanation_method: str
    top_driver: str
    top_factors: List[ExplainabilityFactor]
    explanation_markdown: str
    status: str = "ok"
    profile_version: Optional[int] = None


class ForecastResponse(BaseModel):
    current_premium_estimate: float
    months: List[str]
    historical_premiums: List[float]
    forecast_premiums: List[float]
    trend_summary: str
    status: str = "ok"


class ComingSoonResponse(BaseModel):
    status: str = "coming_soon"
    feature: str
    message: str


class AdminFilterEcho(BaseModel):
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    tenant: Optional[str] = None
    environment: Optional[str] = None
    feature_type: Optional[str] = None


class AccountsKpi(BaseModel):
    accounts_created: int
    active_users: int


class FeatureUsageMetric(BaseModel):
    feature_type: str
    request_volume: int


class ModelUsageMetric(BaseModel):
    prediction_runs: int
    forecast_runs: int
    average_risk_probability: float
    model_name: str
    model_version: str
    model_config = {"protected_namespaces": ()}


class WorkflowSplitItem(BaseModel):
    feature_type: str
    count: int
    percentage: float


class UsageFunnel(BaseModel):
    prediction_views: int
    forecast_views: int
    recommendation_views: int


class SaaSMetrics(BaseModel):
    api_calls: int
    per_feature_request_volume: Dict[str, int]
    adoption_by_tenant: Dict[str, int]


class OperationsSummary(BaseModel):
    avg_latency_ms: float
    p95_latency_ms: float
    error_rate: float
    availability: float
    slo_summary: Dict[str, Any]


class TrendPoint(BaseModel):
    bucket: str
    total_events: int
    prediction_events: int
    forecast_events: int
    recommendation_events: int


class AdminDashboardResponse(BaseModel):
    filters: AdminFilterEcho
    accounts: AccountsKpi
    feature_usage: List[FeatureUsageMetric]
    model_usage: ModelUsageMetric
    workflow_split: List[WorkflowSplitItem]
    usage_funnel: UsageFunnel
    saas_metrics: SaaSMetrics
    operations: OperationsSummary
    trends: List[TrendPoint]
    model_config = {"protected_namespaces": ()}


class AdminMetricsResponse(BaseModel):
    total_users: int
    active_users: int
    avg_response_time_ms: float
    error_rate: float


class TrainingExportResponse(BaseModel):
    job_id: str
    row_count: int
    output_path: str
    created_at: datetime = Field(default_factory=_utcnow)

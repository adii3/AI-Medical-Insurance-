import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False)
    tenant_name = Column(String, default="Northern Shield", nullable=False)
    is_active = Column(Boolean, default=True)
    onboarded = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class SessionToken(Base):
    __tablename__ = "session_tokens"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    refresh_token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MfaChallenge(Base):
    __tablename__ = "mfa_challenges"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    purpose = Column(String, default="login", nullable=False)
    otp_code = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    consumed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    consent_version = Column(String, nullable=False)
    consent_accepted = Column(Boolean, default=False)
    platform_purpose_seen = Column(Boolean, default=False)
    data_use_summary_seen = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PatientProfile(Base):
    __tablename__ = "patient_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True)
    age = Column(Integer, nullable=False)
    bmi = Column(Float, nullable=False)
    smoker_status = Column(Boolean, nullable=False)
    dependents = Column(Integer, nullable=False)
    region = Column(String, nullable=False)
    sex = Column(String, nullable=False)
    recent_hospitalizations = Column(Integer, default=0, nullable=False)
    base_risk_score = Column(Float, default=20.0, nullable=False)
    subscription_tier = Column(String, default="Standard", nullable=False)
    tenant_company = Column(String, default="Northern Shield", nullable=False)
    consent_to_model_improvement = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False, index=True)
    premium_estimate_monthly = Column(Float, nullable=False)
    risk_probability = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)
    confidence_indicator = Column(String, nullable=False)
    top_driver = Column(String, nullable=False)
    explanation_markdown = Column(Text, nullable=False)
    model_name = Column(String, nullable=False)
    model_version = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ForecastRecord(Base):
    __tablename__ = "forecast_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False, index=True)
    current_premium_estimate = Column(Float, nullable=False)
    months = Column(JSON, nullable=False)
    historical_premiums = Column(JSON, nullable=False)
    forecast_premiums = Column(JSON, nullable=False)
    trend_summary = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, nullable=False, index=True, default=_uuid)
    event_name = Column(String, nullable=False, index=True)
    feature_type = Column(String, nullable=False, index=True)
    endpoint = Column(String, nullable=True, index=True)
    method = Column(String, nullable=True)
    role = Column(String, nullable=True, index=True)
    environment = Column(String, nullable=False, index=True)
    tenant_name = Column(String, nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    success = Column(Boolean, default=True, nullable=False)
    status_code = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    model_name = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TrainingExportJob(Base):
    __tablename__ = "training_export_jobs"

    id = Column(String, primary_key=True, default=_uuid)
    requested_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    row_count = Column(Integer, default=0, nullable=False)
    output_path = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SanitizedTrainingRecord(Base):
    __tablename__ = "sanitized_training_records"

    id = Column(Integer, primary_key=True, index=True)
    export_job_id = Column(String, ForeignKey("training_export_jobs.id"), nullable=False, index=True)
    source_profile_id = Column(Integer, ForeignKey("patient_profiles.id"), nullable=False, index=True)
    patient_pseudonym = Column(String, nullable=False, index=True)
    tenant_company = Column(String, nullable=False)
    subscription_tier = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    sex = Column(String, nullable=False)
    bmi = Column(Float, nullable=False)
    smoker_status = Column(Boolean, nullable=False)
    dependents = Column(Integer, nullable=False)
    recent_hospitalizations = Column(Integer, nullable=False)
    base_risk_score = Column(Float, nullable=False)
    region = Column(String, nullable=False)
    high_risk_proxy = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

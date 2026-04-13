"""reconcile schema with current backend models

Revision ID: 20260401_01
Revises:
Create Date: 2026-04-01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_01"
down_revision = None
branch_labels = None
depends_on = None


def _column_names(inspector, table_name: str) -> set[str]:
    return {column["name"] for column in inspector.get_columns(table_name)}


def _add_column_if_missing(inspector, table_name: str, column: sa.Column) -> None:
    if column.name not in _column_names(inspector, table_name):
        op.add_column(table_name, column)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("email", sa.String(), nullable=False, unique=True),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=False, server_default="user"),
            sa.Column("tenant_name", sa.String(), nullable=False, server_default="Northern Shield"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("onboarded", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    else:
        _add_column_if_missing(inspector, "users", sa.Column("tenant_name", sa.String(), nullable=False, server_default="Northern Shield"))
        _add_column_if_missing(inspector, "users", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
        _add_column_if_missing(inspector, "users", sa.Column("onboarded", sa.Boolean(), nullable=False, server_default=sa.text("false")))
        _add_column_if_missing(inspector, "users", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))

    if not inspector.has_table("session_tokens"):
        op.create_table(
            "session_tokens",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("refresh_token_hash", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True)),
            sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not inspector.has_table("mfa_challenges"):
        op.create_table(
            "mfa_challenges",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("purpose", sa.String(), nullable=False, server_default="login"),
            sa.Column("otp_code", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("verified_at", sa.DateTime(timezone=True)),
            sa.Column("consumed_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not inspector.has_table("password_reset_tokens"):
        op.create_table(
            "password_reset_tokens",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("token_hash", sa.String(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True)),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not inspector.has_table("consent_records"):
        op.create_table(
            "consent_records",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("consent_version", sa.String(), nullable=False),
            sa.Column("consent_accepted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("platform_purpose_seen", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("data_use_summary_seen", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not inspector.has_table("patient_profiles"):
        op.create_table(
            "patient_profiles",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("age", sa.Integer(), nullable=False),
            sa.Column("bmi", sa.Float(), nullable=False),
            sa.Column("smoker_status", sa.Boolean(), nullable=False),
            sa.Column("dependents", sa.Integer(), nullable=False),
            sa.Column("region", sa.String(), nullable=False),
            sa.Column("sex", sa.String(), nullable=False, server_default="Male"),
            sa.Column("recent_hospitalizations", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("base_risk_score", sa.Float(), nullable=False, server_default="20"),
            sa.Column("subscription_tier", sa.String(), nullable=False, server_default="Standard"),
            sa.Column("tenant_company", sa.String(), nullable=False, server_default="Northern Shield"),
            sa.Column("consent_to_model_improvement", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    else:
        _add_column_if_missing(inspector, "patient_profiles", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
        _add_column_if_missing(inspector, "patient_profiles", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
        _add_column_if_missing(inspector, "patient_profiles", sa.Column("sex", sa.String(), nullable=False, server_default="Male"))
        _add_column_if_missing(inspector, "patient_profiles", sa.Column("recent_hospitalizations", sa.Integer(), nullable=False, server_default="0"))
        _add_column_if_missing(inspector, "patient_profiles", sa.Column("subscription_tier", sa.String(), nullable=False, server_default="Standard"))
        _add_column_if_missing(inspector, "patient_profiles", sa.Column("tenant_company", sa.String(), nullable=False, server_default="Northern Shield"))
        _add_column_if_missing(inspector, "patient_profiles", sa.Column("consent_to_model_improvement", sa.Boolean(), nullable=False, server_default=sa.text("true")))
        _add_column_if_missing(inspector, "patient_profiles", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()))

    if not inspector.has_table("prediction_records"):
        op.create_table(
            "prediction_records",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("profile_id", sa.Integer(), sa.ForeignKey("patient_profiles.id"), nullable=False, index=True),
            sa.Column("premium_estimate_monthly", sa.Float(), nullable=False),
            sa.Column("risk_probability", sa.Float(), nullable=False),
            sa.Column("risk_level", sa.String(), nullable=False),
            sa.Column("confidence_indicator", sa.String(), nullable=False),
            sa.Column("top_driver", sa.String(), nullable=False),
            sa.Column("explanation_markdown", sa.Text(), nullable=False),
            sa.Column("model_name", sa.String(), nullable=False),
            sa.Column("model_version", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not inspector.has_table("forecast_records"):
        op.create_table(
            "forecast_records",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("profile_id", sa.Integer(), sa.ForeignKey("patient_profiles.id"), nullable=False, index=True),
            sa.Column("current_premium_estimate", sa.Float(), nullable=False),
            sa.Column("months", sa.JSON(), nullable=False),
            sa.Column("historical_premiums", sa.JSON(), nullable=False),
            sa.Column("forecast_premiums", sa.JSON(), nullable=False),
            sa.Column("trend_summary", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not inspector.has_table("analytics_events"):
        op.create_table(
            "analytics_events",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("request_id", sa.String(), nullable=False, index=True),
            sa.Column("event_name", sa.String(), nullable=False, index=True),
            sa.Column("feature_type", sa.String(), nullable=False, index=True),
            sa.Column("endpoint", sa.String(), index=True),
            sa.Column("method", sa.String()),
            sa.Column("role", sa.String(), index=True),
            sa.Column("environment", sa.String(), nullable=False, index=True),
            sa.Column("tenant_name", sa.String(), index=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True),
            sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("status_code", sa.Integer()),
            sa.Column("latency_ms", sa.Float()),
            sa.Column("model_name", sa.String()),
            sa.Column("model_version", sa.String()),
            sa.Column("metadata_json", sa.JSON()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not inspector.has_table("training_export_jobs"):
        op.create_table(
            "training_export_jobs",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("requested_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
            sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("output_path", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    if not inspector.has_table("sanitized_training_records"):
        op.create_table(
            "sanitized_training_records",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column("export_job_id", sa.String(), sa.ForeignKey("training_export_jobs.id"), nullable=False, index=True),
            sa.Column("source_profile_id", sa.Integer(), sa.ForeignKey("patient_profiles.id"), nullable=False, index=True),
            sa.Column("patient_pseudonym", sa.String(), nullable=False, index=True),
            sa.Column("tenant_company", sa.String(), nullable=False),
            sa.Column("subscription_tier", sa.String(), nullable=False),
            sa.Column("age", sa.Integer(), nullable=False),
            sa.Column("sex", sa.String(), nullable=False),
            sa.Column("bmi", sa.Float(), nullable=False),
            sa.Column("smoker_status", sa.Boolean(), nullable=False),
            sa.Column("dependents", sa.Integer(), nullable=False),
            sa.Column("recent_hospitalizations", sa.Integer(), nullable=False),
            sa.Column("base_risk_score", sa.Float(), nullable=False),
            sa.Column("region", sa.String(), nullable=False),
            sa.Column("high_risk_proxy", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )


def downgrade() -> None:
    pass

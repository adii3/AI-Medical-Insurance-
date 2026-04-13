from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_admin_user
from models.models import User
from schemas.schemas import AdminDashboardResponse, AdminMetricsResponse, TrainingExportResponse, UsageFunnel
from services.analytics_service import AnalyticsService
from services.training_dataset_service import TrainingDatasetService


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_dashboard(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    tenant: str | None = None,
    environment: str | None = None,
    feature_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    analytics = AnalyticsService(db)
    analytics.record_event(
        event_name="admin.dashboard.view",
        feature_type="admin",
        endpoint="/api/v1/admin/dashboard",
        method="GET",
        user=current_user,
        status_code=200,
        success=True,
        latency_ms=0.0,
    )
    return analytics.build_dashboard(
        date_from=date_from,
        date_to=date_to,
        tenant=tenant,
        environment=environment,
        feature_type=feature_type,
    )


@router.get("/metrics", response_model=AdminMetricsResponse)
def get_metrics(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    tenant: str | None = None,
    environment: str | None = None,
    feature_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    analytics = AnalyticsService(db)
    analytics.record_event(
        event_name="admin.metrics.view",
        feature_type="admin",
        endpoint="/api/v1/admin/metrics",
        method="GET",
        user=current_user,
        status_code=200,
        success=True,
        latency_ms=0.0,
    )
    return analytics.build_metrics(
        date_from=date_from,
        date_to=date_to,
        tenant=tenant,
        environment=environment,
        feature_type=feature_type,
    )


@router.get("/funnel", response_model=UsageFunnel)
def get_funnel(
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    tenant: str | None = None,
    environment: str | None = None,
    feature_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    analytics = AnalyticsService(db)
    analytics.record_event(
        event_name="admin.funnel.view",
        feature_type="admin",
        endpoint="/api/v1/admin/funnel",
        method="GET",
        user=current_user,
        status_code=200,
        success=True,
        latency_ms=0.0,
    )
    dashboard = analytics.build_dashboard(
        date_from=date_from,
        date_to=date_to,
        tenant=tenant,
        environment=environment,
        feature_type=feature_type,
    )
    return dashboard.usage_funnel


@router.post("/training-data/export", response_model=TrainingExportResponse)
def export_training_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    AnalyticsService(db).record_event(
        event_name="admin.training_export",
        feature_type="admin",
        endpoint="/api/v1/admin/training-data/export",
        method="POST",
        user=current_user,
        status_code=200,
        success=True,
        latency_ms=0.0,
    )
    job = TrainingDatasetService(db).export_sanitized_profiles(current_user)
    return TrainingExportResponse(job_id=job.id, row_count=job.row_count, output_path=job.output_path, created_at=job.created_at)

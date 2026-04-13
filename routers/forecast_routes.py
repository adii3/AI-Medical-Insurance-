from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_active_user
from models.models import User
from schemas.schemas import ComingSoonResponse, ForecastResponse, PredictionRequest
from services.analytics_service import AnalyticsService
from services.inference_service import InferenceService


router = APIRouter(prefix="/api/v1/forecast", tags=["forecasting"])
plan_router = APIRouter(prefix="/api/v1/plans", tags=["plan-finder"])


def _model_artifacts() -> dict:
    try:
        from main import ml_artifacts
    except Exception:
        return {}
    return ml_artifacts


@router.post("", response_model=ForecastResponse)
def get_premium_forecast(
    request: PredictionRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = InferenceService(db, _model_artifacts())
    payload = request.profile if request else None
    persist = request.persist_profile if request else False
    forecast_data = service.forecast(current_user, profile=payload, persist_profile=persist)
    return ForecastResponse(**forecast_data)


@plan_router.post("/recommend", response_model=ComingSoonResponse)
def recommend_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    AnalyticsService(db).record_event(
        event_name="recommendation.view",
        feature_type="recommendation",
        endpoint="/api/v1/plans/recommend",
        method="POST",
        user=current_user,
        status_code=200,
        success=True,
        latency_ms=0.0,
    )
    return ComingSoonResponse(
        feature="smart_plan_finder",
        message="Smart Plan Finder is coming soon and not part of current development.",
    )

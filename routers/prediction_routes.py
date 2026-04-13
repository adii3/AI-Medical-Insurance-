from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_active_user
from models.models import User
from schemas.schemas import PredictionRequest, PredictionResponse, WhatIfRequest
from services.inference_service import InferenceService


router = APIRouter(prefix="/api/v1/predict", tags=["prediction"])


def _model_artifacts() -> dict:
    try:
        from main import ml_artifacts
    except Exception:
        return {}
    return ml_artifacts


@router.post("", response_model=PredictionResponse)
def predict_premium(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = InferenceService(db, _model_artifacts())
    return service.predict(current_user, request.profile, persist_profile=request.persist_profile)


@router.post("/what-if", response_model=PredictionResponse)
def what_if_prediction(
    request: WhatIfRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    service = InferenceService(db, _model_artifacts())
    return service.what_if(current_user, request.overrides, profile=request.profile)

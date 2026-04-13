from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from constants import FEATURE_COLS
from core.config import settings
from core.database import SessionLocal, engine
from models import models
from routers import admin_routes, auth_routes, forecast_routes, prediction_routes, profile_routes
from services.auth_service import AuthService


ml_artifacts: Dict[str, Any] = {}
model_boot_status = {"loaded": False, "mode": "heuristic", "error": None}


def _load_ml_artifacts() -> None:
    if settings.testing or settings.disable_model_training:
        model_boot_status.update({"loaded": False, "mode": "heuristic", "error": None})
        ml_artifacts.clear()
        return

    try:
        from model import train_model

        artifacts = train_model()
        artifacts["feature_cols"] = FEATURE_COLS
        ml_artifacts.clear()
        ml_artifacts.update(artifacts)
        model_boot_status.update({"loaded": True, "mode": "xgboost", "error": None})
    except Exception as exc:  # pragma: no cover - fallback path for environments without ML deps
        ml_artifacts.clear()
        model_boot_status.update({"loaded": False, "mode": "heuristic", "error": str(exc)})


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        AuthService(db).ensure_bootstrap_admin()
    finally:
        db.close()

    _load_ml_artifacts()
    yield
    ml_artifacts.clear()


app = FastAPI(
    title="AI Medical Insurance Platform API",
    description="Backend API for secure user onboarding, explainable premium prediction, forecasting, and admin analytics.",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(profile_routes.router)
app.include_router(prediction_routes.router)
app.include_router(forecast_routes.router)
app.include_router(forecast_routes.plan_router)
app.include_router(admin_routes.router)


@app.get("/api/v1/health", tags=["system"])
def health_check():
    return {
        "status": "ok",
        "message": "API is ready.",
        "model_runtime": model_boot_status,
    }

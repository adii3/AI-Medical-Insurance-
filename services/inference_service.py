import math
import time
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from constants import APPROVED_WHAT_IF_FIELDS, REGIONS, SEXES, TENANTS, TIERS
from core.config import settings
from models.models import ForecastRecord, PatientProfile, PredictionRecord, User
from rag import build_rag_narrative
from schemas.schemas import ExplainabilityFactor, PatientProfileInput, PredictionResponse, WhatIfOverrides
from services.analytics_service import AnalyticsService
from services.business_logic import generate_forecast
from services.user_profile_service import UserProfileService


FEATURE_HELP = {
    "age": "age increases long-term utilization exposure",
    "bmi": "BMI shifts expected metabolic and cardiovascular risk",
    "smoker_status": "smoking raises expected care costs",
    "dependents": "household dependency changes expected plan usage",
    "recent_hospitalizations": "recent hospitalizations indicate near-term cost volatility",
    "base_risk_score": "existing risk score raises the actuarial baseline",
    "subscription_tier": "richer coverage tiers cost more each month",
    "region": "regional healthcare costs differ across provinces",
    "sex": "demographic mix affects model segmentation",
    "tenant_company": "tenant context is used for product-level segmentation",
}


class InferenceService:
    def __init__(self, db: Session, model_artifacts: Optional[dict] = None):
        self.db = db
        self.model_artifacts = model_artifacts or {}
        self.analytics = AnalyticsService(db)
        self.profile_service = UserProfileService(db)

    def _profile_to_dict(self, profile: PatientProfile | PatientProfileInput | dict, user: Optional[User] = None) -> dict:
        if isinstance(profile, dict):
            data = profile.copy()
        elif hasattr(profile, "model_dump"):
            data = profile.model_dump()
        else:
            data = {
                "age": profile.age,
                "bmi": profile.bmi,
                "smoker_status": profile.smoker_status,
                "dependents": profile.dependents,
                "region": profile.region,
                "sex": profile.sex,
                "recent_hospitalizations": profile.recent_hospitalizations,
                "base_risk_score": profile.base_risk_score,
                "subscription_tier": profile.subscription_tier,
                "tenant_company": profile.tenant_company,
                "consent_to_model_improvement": profile.consent_to_model_improvement,
            }

        data["tenant_company"] = data.get("tenant_company") or (user.tenant_name if user else TENANTS[0])
        data.setdefault("subscription_tier", TIERS[0])
        data.setdefault("sex", SEXES[0])
        data.setdefault("region", REGIONS[0])
        data.setdefault("recent_hospitalizations", 0)
        data.setdefault("base_risk_score", 20.0)
        return data

    def _premium_estimate(self, profile: dict, risk_probability: float) -> float:
        regional_adjustment = {
            "Ontario": 40,
            "Quebec": 30,
            "British Columbia": 35,
            "Alberta": 32,
            "Manitoba": 25,
            "Saskatchewan": 24,
            "Nova Scotia": 22,
            "New Brunswick": 20,
        }.get(profile["region"], 25)
        tier_multiplier = {
            "Standard": 1.0,
            "Premium": 1.15,
            "Enterprise": 1.25,
        }.get(profile["subscription_tier"], 1.0)
        base = (
            85
            + profile["age"] * 1.4
            + profile["bmi"] * 1.2
            + profile["dependents"] * 12
            + profile["recent_hospitalizations"] * 28
            + profile["base_risk_score"] * 3.4
            + (55 if profile["smoker_status"] else 0)
            + regional_adjustment
        )
        estimate = base * tier_multiplier * (0.9 + risk_probability * 0.7)
        return round(estimate, 2)

    def _heuristic_prediction(self, profile: dict) -> tuple[float, list[tuple[str, float]]]:
        contributions = {
            "age": profile["age"] / 120,
            "bmi": profile["bmi"] / 70,
            "smoker_status": 0.20 if profile["smoker_status"] else -0.03,
            "dependents": profile["dependents"] * 0.015,
            "recent_hospitalizations": profile["recent_hospitalizations"] * 0.08,
            "base_risk_score": profile["base_risk_score"] / 130,
            "subscription_tier": {"Standard": 0.01, "Premium": 0.04, "Enterprise": 0.06}.get(profile["subscription_tier"], 0.01),
            "region": {"Ontario": 0.02, "Quebec": 0.0, "British Columbia": 0.01}.get(profile["region"], 0.005),
        }
        raw_score = sum(contributions.values()) - 0.45
        probability = 1 / (1 + math.exp(-raw_score))
        ranked = sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)
        return probability, ranked

    def _ml_prediction(self, profile: dict) -> Optional[tuple[float, list[tuple[str, float]], str]]:
        if not self.model_artifacts:
            return None
        try:
            from shap_utils import predict_patient
        except Exception:
            return None

        probability, shap_row, _ = predict_patient(profile, self.model_artifacts)
        ranked = sorted(
            [(name, float(shap_row[idx])) for idx, name in enumerate(self.model_artifacts.get("feature_cols", []))],
            key=lambda item: abs(item[1]),
            reverse=True,
        )
        explanation_method = "shap_tree_explainer" if self.model_artifacts.get("explainer") is not None else "xgboost_pred_contrib"
        return probability, ranked, explanation_method

    def _build_factors(self, ranked_contributions: list[tuple[str, float]]) -> list[ExplainabilityFactor]:
        factors = []
        for feature_name, value in ranked_contributions[:5]:
            direction = "increases risk" if value >= 0 else "decreases risk"
            factors.append(
                ExplainabilityFactor(
                    feature_name=feature_name,
                    value=round(float(value), 4),
                    direction=direction,
                    plain_language=FEATURE_HELP.get(feature_name, "this feature affected the result"),
                )
            )
        return factors

    def _predict_from_profile_dict(self, profile_data: dict) -> PredictionResponse:
        ml_result = self._ml_prediction(profile_data)
        if ml_result is not None:
            probability, ranked, explanation_method = ml_result
            confidence = "high" if abs(probability - 0.5) >= 0.2 else "moderate"
        else:
            probability, ranked = self._heuristic_prediction(profile_data)
            confidence = "estimated"
            explanation_method = "heuristic"

        premium_estimate = self._premium_estimate(profile_data, probability)
        factors = self._build_factors(ranked)
        explanation = build_rag_narrative(
            profile_data,
            risk_probability=probability,
            premium_estimate_monthly=premium_estimate,
            factors=[factor.model_dump() for factor in factors],
        )
        risk_level = "HIGH" if probability >= 0.65 else "MODERATE" if probability >= 0.4 else "LOW"
        return PredictionResponse(
            premium_estimate_monthly=premium_estimate,
            risk_probability=round(probability, 4),
            risk_level=risk_level,
            confidence_indicator=confidence,
            explanation_method=explanation_method,
            top_driver=factors[0].feature_name if factors else "n/a",
            top_factors=factors,
            explanation_markdown=explanation,
        )

    def predict(self, user: User, payload: PatientProfileInput, persist_profile: bool = True) -> PredictionResponse:
        profile_record = None
        profile_data = self._profile_to_dict(payload, user=user)
        if persist_profile:
            profile_record = self.profile_service.upsert_profile(user, payload)
            profile_data = self._profile_to_dict(profile_record, user=user)

        start = time.perf_counter()
        response = self._predict_from_profile_dict(profile_data)
        latency_ms = (time.perf_counter() - start) * 1000

        if profile_record is not None:
            response.profile_version = profile_record.version
            prediction_record = PredictionRecord(
                user_id=user.id,
                profile_id=profile_record.id,
                premium_estimate_monthly=response.premium_estimate_monthly,
                risk_probability=response.risk_probability,
                risk_level=response.risk_level,
                confidence_indicator=response.confidence_indicator,
                top_driver=response.top_driver,
                explanation_markdown=response.explanation_markdown,
                model_name=settings.model_name,
                model_version=settings.model_version,
            )
            self.db.add(prediction_record)
            self.db.commit()

        self.analytics.record_event(
            event_name="prediction.run",
            feature_type="prediction",
            endpoint="/api/v1/predict",
            method="POST",
            user=user,
            status_code=200,
            success=True,
            latency_ms=latency_ms,
            metadata={"risk_level": response.risk_level},
            model_name=settings.model_name,
            model_version=settings.model_version,
        )
        return response

    def what_if(self, user: User, overrides: WhatIfOverrides, profile: Optional[PatientProfileInput] = None) -> PredictionResponse:
        if profile is not None:
            base_profile = self._profile_to_dict(profile, user=user)
        else:
            base_profile = self._profile_to_dict(self.profile_service.get_active_profile(user), user=user)

        override_data = overrides.model_dump(exclude_none=True)
        disallowed = set(override_data) - APPROVED_WHAT_IF_FIELDS
        if disallowed:
            raise HTTPException(status_code=400, detail=f"Unsupported what-if fields: {sorted(disallowed)}")
        base_profile.update(override_data)

        start = time.perf_counter()
        response = self._predict_from_profile_dict(base_profile)
        latency_ms = (time.perf_counter() - start) * 1000
        self.analytics.record_event(
            event_name="prediction.what_if",
            feature_type="prediction",
            endpoint="/api/v1/predict/what-if",
            method="POST",
            user=user,
            status_code=200,
            success=True,
            latency_ms=latency_ms,
            metadata={"overrides": list(override_data.keys())},
            model_name=settings.model_name,
            model_version=settings.model_version,
        )
        return response

    def forecast(self, user: User, profile: Optional[PatientProfileInput] = None, persist_profile: bool = False):
        profile_record = None
        if profile is not None:
            if persist_profile:
                profile_record = self.profile_service.upsert_profile(user, profile)
                profile_data = self._profile_to_dict(profile_record, user=user)
            else:
                profile_data = self._profile_to_dict(profile, user=user)
        else:
            profile_record = self.profile_service.get_active_profile(user)
            profile_data = self._profile_to_dict(profile_record, user=user)

        prediction = self._predict_from_profile_dict(profile_data)
        start = time.perf_counter()
        forecast_data = generate_forecast(profile_data, prediction.premium_estimate_monthly)
        latency_ms = (time.perf_counter() - start) * 1000

        if profile_record is None:
            profile_record = self.profile_service.get_active_profile(user)

        record = ForecastRecord(
            user_id=user.id,
            profile_id=profile_record.id,
            current_premium_estimate=prediction.premium_estimate_monthly,
            months=forecast_data["forecast_labels"],
            historical_premiums=forecast_data["historical_premiums"],
            forecast_premiums=forecast_data["forecast_premiums"],
            trend_summary=forecast_data["trend_summary"],
        )
        self.db.add(record)
        self.db.commit()

        self.analytics.record_event(
            event_name="forecast.run",
            feature_type="forecast",
            endpoint="/api/v1/forecast",
            method="POST",
            user=user,
            status_code=200,
            success=True,
            latency_ms=latency_ms,
            metadata={"profile_version": profile_record.version},
            model_name=settings.model_name,
            model_version=settings.model_version,
        )

        return {
            "current_premium_estimate": prediction.premium_estimate_monthly,
            "months": forecast_data["forecast_labels"],
            "historical_premiums": forecast_data["historical_premiums"],
            "forecast_premiums": forecast_data["forecast_premiums"],
            "trend_summary": forecast_data["trend_summary"],
        }

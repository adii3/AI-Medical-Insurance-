from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import get_current_active_user
from models.models import User
from schemas.schemas import OnboardingRequest, OnboardingResponse, PatientProfileInput, ProfileUpsertResponse, UserSummary
from services.analytics_service import AnalyticsService
from services.user_profile_service import UserProfileService


router = APIRouter(prefix="/api/v1/me", tags=["me"])


@router.get("", response_model=UserSummary)
def get_me(current_user: User = Depends(get_current_active_user)):
    return UserSummary.model_validate(current_user)


@router.post("/onboarding", response_model=OnboardingResponse)
def complete_onboarding(
    payload: OnboardingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    consent = UserProfileService(db).complete_onboarding(current_user, payload)
    AnalyticsService(db).record_event(
        event_name="user.onboarding.complete",
        feature_type="onboarding",
        endpoint="/api/v1/me/onboarding",
        method="POST",
        user=current_user,
        status_code=200,
        success=True,
        latency_ms=0.0,
    )
    return OnboardingResponse(
        message="Onboarding state saved successfully.",
        onboarded=current_user.onboarded,
        consent_version=consent.consent_version,
    )


@router.get("/profile", response_model=ProfileUpsertResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    profile = UserProfileService(db).get_active_profile(current_user)
    return ProfileUpsertResponse(message="Profile retrieved successfully.", profile=profile)


@router.post("/profile", response_model=ProfileUpsertResponse)
def save_profile(
    payload: PatientProfileInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    profile = UserProfileService(db).upsert_profile(current_user, payload)
    AnalyticsService(db).record_event(
        event_name="user.profile.upsert",
        feature_type="profile",
        endpoint="/api/v1/me/profile",
        method="POST",
        user=current_user,
        status_code=200,
        success=True,
        latency_ms=0.0,
        tenant_name=profile.tenant_company,
    )
    return ProfileUpsertResponse(message="Profile saved successfully.", profile=profile)

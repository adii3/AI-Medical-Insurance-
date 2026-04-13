from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.models import ConsentRecord, PatientProfile, User
from schemas.schemas import OnboardingRequest, PatientProfileInput


class UserProfileService:
    def __init__(self, db: Session):
        self.db = db

    def complete_onboarding(self, user: User, payload: OnboardingRequest) -> ConsentRecord:
        consent = self.db.query(ConsentRecord).filter(ConsentRecord.user_id == user.id).first()
        if consent is None:
            consent = ConsentRecord(
                user_id=user.id,
                consent_version=payload.consent_version,
            )
            self.db.add(consent)

        consent.consent_version = payload.consent_version
        consent.consent_accepted = payload.consent_accepted
        consent.platform_purpose_seen = payload.platform_purpose_seen
        consent.data_use_summary_seen = payload.data_use_summary_seen
        user.onboarded = (
            payload.consent_accepted
            and payload.platform_purpose_seen
            and payload.data_use_summary_seen
        )
        self.db.commit()
        self.db.refresh(consent)
        return consent

    def get_active_profile(self, user: User) -> PatientProfile:
        profile = (
            self.db.query(PatientProfile)
            .filter(PatientProfile.user_id == user.id, PatientProfile.is_active.is_(True))
            .order_by(PatientProfile.version.desc())
            .first()
        )
        if profile is None:
            raise HTTPException(status_code=404, detail="No active profile found")
        return profile

    def upsert_profile(self, user: User, payload: PatientProfileInput) -> PatientProfile:
        existing = (
            self.db.query(PatientProfile)
            .filter(PatientProfile.user_id == user.id, PatientProfile.is_active.is_(True))
            .order_by(PatientProfile.version.desc())
            .first()
        )
        next_version = 1
        if existing:
            existing.is_active = False
            next_version = existing.version + 1

        profile = PatientProfile(
            user_id=user.id,
            version=next_version,
            age=payload.age,
            bmi=payload.bmi,
            smoker_status=payload.smoker_status,
            dependents=payload.dependents,
            region=payload.region,
            sex=payload.sex,
            recent_hospitalizations=payload.recent_hospitalizations,
            base_risk_score=payload.base_risk_score,
            subscription_tier=payload.subscription_tier,
            tenant_company=payload.tenant_company or user.tenant_name,
            consent_to_model_improvement=payload.consent_to_model_improvement,
            is_active=True,
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

import csv
import os
import uuid

from sqlalchemy.orm import Session

from models.models import PatientProfile, PredictionRecord, SanitizedTrainingRecord, TrainingExportJob, User


class TrainingDatasetService:
    def __init__(self, db: Session):
        self.db = db

    def export_sanitized_profiles(self, requested_by: User) -> TrainingExportJob:
        export_dir = os.path.join(os.getcwd(), "exports")
        os.makedirs(export_dir, exist_ok=True)

        profiles = (
            self.db.query(PatientProfile)
            .filter(
                PatientProfile.is_active.is_(True),
                PatientProfile.consent_to_model_improvement.is_(True),
            )
            .all()
        )

        output_path = os.path.join(export_dir, "sanitized_training_export.csv")
        job = TrainingExportJob(
            requested_by_user_id=requested_by.id,
            row_count=0,
            output_path=output_path,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        records = []
        fieldnames = [
            "patient_pseudonym",
            "tenant_company",
            "subscription_tier",
            "age",
            "sex",
            "bmi",
            "smoker_status",
            "dependents",
            "recent_hospitalizations",
            "base_risk_score",
            "region",
            "high_risk_proxy",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for profile in profiles:
                latest_prediction = (
                    self.db.query(PredictionRecord)
                    .filter(PredictionRecord.profile_id == profile.id)
                    .order_by(PredictionRecord.created_at.desc())
                    .first()
                )
                high_risk_proxy = (
                    latest_prediction.risk_probability >= 0.5
                    if latest_prediction else profile.base_risk_score >= 50
                )
                row = {
                    "patient_pseudonym": f"Patient_{uuid.uuid4().hex[:10]}",
                    "tenant_company": profile.tenant_company,
                    "subscription_tier": profile.subscription_tier,
                    "age": profile.age,
                    "sex": profile.sex,
                    "bmi": profile.bmi,
                    "smoker_status": profile.smoker_status,
                    "dependents": profile.dependents,
                    "recent_hospitalizations": profile.recent_hospitalizations,
                    "base_risk_score": profile.base_risk_score,
                    "region": profile.region,
                    "high_risk_proxy": high_risk_proxy,
                }
                writer.writerow(row)
                records.append(
                    SanitizedTrainingRecord(
                        export_job_id=job.id,
                        source_profile_id=profile.id,
                        **row,
                    )
                )

        if records:
            self.db.add_all(records)
        job.row_count = len(records)
        self.db.commit()
        self.db.refresh(job)
        return job

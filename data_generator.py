#imported libraries
import os
import random
import uuid
import numpy as np
import pandas as pd
from faker import Faker

from constants import REGIONS, SEXES, TENANTS, TIERS


def generate_pii_data(n=10_000, seed=42):
    np.random.seed(seed)
    random.seed(seed)
    fake = Faker("en_CA")
    Faker.seed(seed)
    rows = []

    for _ in range(n):
        age = int(np.clip(np.random.normal(45, 15), 18, 90))
        bmi = round(float(np.clip(np.random.normal(27, 5), 15.0, 55.0)), 1)
        smoker_status = bool(np.random.binomial(1, 0.22))
        dependents = int(np.clip(np.random.poisson(1.5), 0, 8))
        recent_hospitalizations = int(np.clip(np.random.poisson(0.4), 0, 5))
        base_risk_score = round(float(np.random.uniform(5, 40)), 2)
        sex = random.choice(SEXES)
        region = random.choice(REGIONS)
        tenant_company = random.choice(TENANTS)
        subscription_tier = random.choice(TIERS)

        risk_score = (
            (age / 90) * 30
            + (bmi / 55) * 20
            + (20 if smoker_status else 0)
            + recent_hospitalizations * 10
            + (base_risk_score / 40) * 15
            + np.random.normal(0, 5)
        )
        high_risk = bool(risk_score > 50)

        rows.append(
            {
                "user_id": str(uuid.uuid4()),
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "phone_number": fake.phone_number(),
                "address": fake.address().replace("\n", ", "),
                "tenant_company": tenant_company,
                "subscription_tier": subscription_tier,
                "age": age,
                "sex": sex,
                "bmi": bmi,
                "smoker_status": smoker_status,
                "dependents": dependents,
                "recent_hospitalizations": recent_hospitalizations,
                "base_risk_score": base_risk_score,
                "region": region,
                "high_risk": high_risk,
            }
        )

    return pd.DataFrame(rows)


def load_or_generate_data():
    raw_path = "raw_dataset.csv"
    sanitized_path = "sanitized_dataset.csv"

    if os.path.exists(sanitized_path):
        return pd.read_csv(sanitized_path)

    df = generate_pii_data()
    df.to_csv(raw_path, index=False)

    pii_columns = ["first_name", "last_name", "phone_number", "address", "user_id"]
    sanitized_df = df.drop(columns=pii_columns, errors="ignore")
    sanitized_df["patient_pseudonym"] = [
        f"Patient_{str(uuid.uuid4())[:8]}" for _ in range(len(sanitized_df))
    ]
    sanitized_df.to_csv(sanitized_path, index=False)
    return sanitized_df


if __name__ == "__main__":
    _ = load_or_generate_data()

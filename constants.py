TENANTS = [
    "Northern Shield",
    "Oshawa Health",
    "Prairie Life",
    "Pacific Care",
    "Atlantic Blue",
]

TIERS = ["Standard", "Premium", "Enterprise"]
REGIONS = [
    "Ontario",
    "Quebec",
    "British Columbia",
    "Alberta",
    "Manitoba",
    "Saskatchewan",
    "Nova Scotia",
    "New Brunswick",
]
SEXES = ["Male", "Female", "Non-binary"]

FEATURE_COLS = [
    "age",
    "bmi",
    "smoker_status",
    "dependents",
    "recent_hospitalizations",
    "base_risk_score",
    "sex_enc",
    "region_enc",
    "subscription_tier_enc",
    "tenant_company_enc",
    "Age_x_BMI",
    "Smoker_x_Hosp",
    "BMI_Category",
    "Age_Group",
]

APPROVED_WHAT_IF_FIELDS = {
    "bmi",
    "smoker_status",
    "region",
    "dependents",
    "recent_hospitalizations",
    "base_risk_score",
    "subscription_tier",
}

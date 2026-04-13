# AI-Powered Medical Insurance Platform - API Contract
**Version 2.0 - Headless REST Backend Refactor**

## 1. Authentication Endpoints
**Base Path:** `/api/v1/auth`

| Method | Endpoint | Description | Payload | Returns |
|--------|----------|-------------|---------|---------|
| `POST` | `/signup`| Create new account | `{email, password, role}` | `UserResponse` |
| `POST` | `/login` | Obtain JWT token | `{email, password}` | `Token` |
| `POST` | `/verify-otp` | MFA validation | `{email, otp}` | `Success Msg` |
| `POST` | `/reset-password` | Update Pw | `{email, new_password}` | `Success Msg` |

---

## 2. Core AI Modules
**Base Path:** `/api/v1/predict` and `/api/v1/forecast`

### What-If & Premium Prediction
- **POST** `/api/v1/predict`
- **Requires Auth:** Yes (Bearer Token)
- **Purpose:** Submit user profile attributes and receive ML-driven risk scores and SHAP explainability matrices.
- **Payload:** `WhatIfRequest`
  ```json
  {
      "profile": {
          "age": 45,
          "bmi": 28.5,
          "smoker_status": true,
          "dependents": 2,
          "region": "Ontario",
          "base_risk_score": 15.0
      }
  }
  ```
- **Returns:** Risk probability, string risk level ("HIGH", "LOW"), top driver feature name, SHAP feature matrix, and the RAG-generated explanation.

### Holt-Winters Forecasting
- **POST** `/api/v1/forecast`
- **Requires Auth:** Yes
- **Purpose:** Outputs a 36-month trend array based on the `predict` profile to visualize the projected cost changes.
- **Returns:** Arrays of `months`, `historical_premiums`, `forecast_premiums`, and `trend_summary`.

---

## 3. Smart Plan Finder
**Base Path:** `/api/v1/plans`

- **POST** `/api/v1/plans/recommend`
- **Purpose:** Dynamically ranks 3 insurance catalog tiers (Bronze, Silver, Gold) based on the input risk score.
- **Returns:** An array of `PlanCard` nodes sorted by relevance matching the patient profile.

---

## 4. Admin SaaS Analytics
**Base Path:** `/api/v1/admin`

- **GET** `/api/v1/admin/metrics` -> Summarizes API volume, Prediction percentages, avg response times.
- **GET** `/api/v1/admin/funnel` -> Returns event counts across predictions, forecast views, and plan finder clicks.
- **Note:** Only accessible to tokens bearing the `admin` role claim.

---

## Summary of Completed Refactor
1. **Removed Streamlit:** The `app.py` and `ui_components.py` artifacts were completely purged from the codebase.
2. **PostgreSQL + Redis Integration:** The API was wrapped around an async SQLAlchemy schema ready for GCP Cloud Run / Cloud SQL deployment.
3. **GDPR/PIPEDA Sanitization:** The Data Generator no longer leaks PII to the training module; it explicitly obfuscates fields and produces a `sanitized_dataset.csv`.
4. **Holt-Winters Extrapolation Added:** The forecast backend synthetically expands a patient's trajectory and projects 3 years ahead using the `statsmodels` library.
5. **Admin RBAC:** FastAPI dependency injection explicitly enforces `user` vs `admin` segmentation across the endpoints.

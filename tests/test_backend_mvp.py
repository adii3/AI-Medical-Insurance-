import csv
import os
from pathlib import Path
import unittest


DB_PATH = Path("test_medical_ai.db")
if DB_PATH.exists():
    DB_PATH.unlink()

os.environ["TESTING"] = "1"
os.environ["DISABLE_MODEL_TRAINING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///./test_medical_ai.db"
os.environ["ADMIN_BOOTSTRAP_EMAIL"] = "admin@example.com"
os.environ["ADMIN_BOOTSTRAP_PASSWORD"] = "AdminPass123!"
os.environ["ADMIN_BOOTSTRAP_TENANT"] = "Northern Shield"
os.environ["DEBUG_TOKEN_PREVIEWS"] = "1"

from fastapi.testclient import TestClient

from core.database import SessionLocal, engine
from main import app
from models import models
from services.auth_service import AuthService


class BackendMvpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_cm = TestClient(app)
        cls.client = cls.client_cm.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_cm.__exit__(None, None, None)
        engine.dispose()
        if DB_PATH.exists():
            DB_PATH.unlink()

    def setUp(self):
        models.Base.metadata.drop_all(bind=engine)
        models.Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            AuthService(db).ensure_bootstrap_admin()
        finally:
            db.close()

    def _signup(self, email: str, password: str = "UserPass123!", tenant_name: str = "Pacific Care"):
        return self.client.post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": password,
                "tenant_name": tenant_name,
                "role": "admin",
            },
        )

    def _login_tokens(self, email: str, password: str):
        login_response = self.client.post("/api/v1/auth/login", json={"email": email, "password": password})
        self.assertEqual(login_response.status_code, 200, login_response.text)
        challenge = login_response.json()
        verify_response = self.client.post(
            "/api/v1/auth/mfa/verify",
            json={"challenge_id": challenge["challenge_id"], "otp": challenge["otp_code_preview"]},
        )
        self.assertEqual(verify_response.status_code, 200, verify_response.text)
        return verify_response.json()

    def test_public_signup_cannot_create_admin(self):
        response = self._signup("user1@example.com")
        self.assertEqual(response.status_code, 201, response.text)
        body = response.json()
        self.assertEqual(body["user"]["role"], "user")

        admin_tokens = self._login_tokens("admin@example.com", "AdminPass123!")
        me = self.client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
        )
        self.assertEqual(me.status_code, 200, me.text)
        self.assertEqual(me.json()["role"], "admin")

    def test_login_mfa_and_admin_guard(self):
        self._signup("guarded@example.com")
        user_tokens = self._login_tokens("guarded@example.com", "UserPass123!")

        forbidden = self.client.get(
            "/api/v1/admin/metrics",
            headers={"Authorization": f"Bearer {user_tokens['access_token']}"},
        )
        self.assertEqual(forbidden.status_code, 403, forbidden.text)

        admin_tokens = self._login_tokens("admin@example.com", "AdminPass123!")
        allowed = self.client.get(
            "/api/v1/admin/metrics",
            headers={"Authorization": f"Bearer {admin_tokens['access_token']}"},
        )
        self.assertEqual(allowed.status_code, 200, allowed.text)

    def test_password_reset_requires_valid_token_flow(self):
        self._signup("reset@example.com")
        invalid = self.client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"reset_token": "invalid-token-value-1234567890", "new_password": "NewPass123!"},
        )
        self.assertEqual(invalid.status_code, 400, invalid.text)

        request_response = self.client.post(
            "/api/v1/auth/password-reset/request",
            json={"email": "reset@example.com"},
        )
        self.assertEqual(request_response.status_code, 200, request_response.text)
        reset_token = request_response.json()["reset_token_preview"]
        self.assertTrue(reset_token)

        confirm = self.client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"reset_token": reset_token, "new_password": "NewPass123!"},
        )
        self.assertEqual(confirm.status_code, 200, confirm.text)

        old_login = self.client.post(
            "/api/v1/auth/login",
            json={"email": "reset@example.com", "password": "UserPass123!"},
        )
        self.assertEqual(old_login.status_code, 401, old_login.text)

        new_login = self.client.post(
            "/api/v1/auth/login",
            json={"email": "reset@example.com", "password": "NewPass123!"},
        )
        self.assertEqual(new_login.status_code, 200, new_login.text)

    def test_user_flow_admin_dashboard_and_sanitized_export(self):
        self._signup("flow@example.com", tenant_name="Atlantic Blue")
        tokens = self._login_tokens("flow@example.com", "UserPass123!")
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        onboarding = self.client.post(
            "/api/v1/me/onboarding",
            json={
                "consent_version": "2026-03",
                "consent_accepted": True,
                "platform_purpose_seen": True,
                "data_use_summary_seen": True,
            },
            headers=headers,
        )
        self.assertEqual(onboarding.status_code, 200, onboarding.text)
        self.assertTrue(onboarding.json()["onboarded"])

        profile_payload = {
            "age": 42,
            "bmi": 27.6,
            "smoker_status": False,
            "dependents": 2,
            "region": "Ontario",
            "sex": "Female",
            "recent_hospitalizations": 1,
            "base_risk_score": 18.0,
            "subscription_tier": "Premium",
            "tenant_company": "Atlantic Blue",
            "consent_to_model_improvement": True,
        }
        save_profile = self.client.post("/api/v1/me/profile", json=profile_payload, headers=headers)
        self.assertEqual(save_profile.status_code, 200, save_profile.text)
        profile_version = save_profile.json()["profile"]["version"]
        self.assertEqual(profile_version, 1)

        prediction = self.client.post(
            "/api/v1/predict",
            json={"profile": profile_payload, "persist_profile": True},
            headers=headers,
        )
        self.assertEqual(prediction.status_code, 200, prediction.text)
        prediction_body = prediction.json()
        self.assertIn("premium_estimate_monthly", prediction_body)
        self.assertIn("top_factors", prediction_body)
        self.assertEqual(prediction_body["explanation_method"], "heuristic")

        what_if = self.client.post(
            "/api/v1/predict/what-if",
            json={"overrides": {"smoker_status": True, "bmi": 31.2}},
            headers=headers,
        )
        self.assertEqual(what_if.status_code, 200, what_if.text)
        self.assertNotEqual(
            what_if.json()["premium_estimate_monthly"],
            prediction_body["premium_estimate_monthly"],
        )

        forecast = self.client.post(
            "/api/v1/forecast",
            json={"profile": profile_payload, "persist_profile": False},
            headers=headers,
        )
        self.assertEqual(forecast.status_code, 200, forecast.text)
        self.assertEqual(len(forecast.json()["forecast_premiums"]), 36)

        plans = self.client.post("/api/v1/plans/recommend", headers=headers)
        self.assertEqual(plans.status_code, 200, plans.text)
        self.assertEqual(plans.json()["status"], "coming_soon")

        admin_tokens = self._login_tokens("admin@example.com", "AdminPass123!")
        admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}

        dashboard = self.client.get("/api/v1/admin/dashboard?tenant=Atlantic%20Blue", headers=admin_headers)
        self.assertEqual(dashboard.status_code, 200, dashboard.text)
        dashboard_body = dashboard.json()
        self.assertGreaterEqual(dashboard_body["accounts"]["accounts_created"], 1)
        self.assertGreaterEqual(dashboard_body["usage_funnel"]["prediction_views"], 1)
        self.assertGreaterEqual(dashboard_body["usage_funnel"]["forecast_views"], 1)
        self.assertGreaterEqual(dashboard_body["usage_funnel"]["recommendation_views"], 1)

        export = self.client.post("/api/v1/admin/training-data/export", headers=admin_headers)
        self.assertEqual(export.status_code, 200, export.text)
        export_body = export.json()
        self.assertGreaterEqual(export_body["row_count"], 1)
        self.assertTrue(Path(export_body["output_path"]).exists())

        with open(export_body["output_path"], newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            headers_row = reader.fieldnames or []
            self.assertNotIn("email", headers_row)
            first_row = next(reader)
            self.assertIn("patient_pseudonym", first_row)


if __name__ == "__main__":
    unittest.main()

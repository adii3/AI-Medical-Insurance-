# AI Medical Insurance Platform

This repository now ships as a full MVP stack:

- `medical-ai-frontend`: Next.js 16 app for signup, MFA login, onboarding, assessment, results, forecast, simulator, password reset, and admin analytics.
- `medical-ai-backend`: FastAPI API for auth, profile storage, explainable prediction, forecast generation, admin analytics, and sanitized training-data export.
- `postgres` and `redis`: local support services for state, analytics, and session infrastructure.

## Architecture Choice

The deployment shape was normalized to **two application containers**:

1. `medical-ai-frontend` for the web experience.
2. `medical-ai-backend` for API + AI inference.

This is the better MVP tradeoff for GCP because frontend and backend can scale independently, and the frontend now proxies API traffic through its own `/api/proxy/[...path]` route using the runtime `API_BASE_URL`.

## Local Run

Start the entire stack:

```bash
docker compose up --build
```

Endpoints:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

Default local admin credentials:

- Email: `admin@example.com`
- Password: `ChangeMe123!`

## Verified Flows

User-facing:

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/mfa/verify`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/password-reset/request`
- `POST /api/v1/auth/password-reset/confirm`
- `GET /api/v1/me`
- `POST /api/v1/me/onboarding`
- `GET /api/v1/me/profile`
- `POST /api/v1/predict`
- `POST /api/v1/predict/what-if`
- `POST /api/v1/forecast`

Admin-facing:

- `GET /api/v1/admin/dashboard`
- `GET /api/v1/admin/metrics`
- `GET /api/v1/admin/funnel`
- `POST /api/v1/admin/training-data/export`

Roadmap surface:

- `POST /api/v1/plans/recommend` intentionally returns `coming_soon`, and the frontend now reflects that honestly.

## Frontend Development

The frontend can also run separately:

```bash
cd Frontend-Capstone
npm install
npm run lint
npx tsc --noEmit
npm run build
```

For local non-Docker development, the route proxy defaults to `http://localhost:8000/api/v1`. Inside Docker and Cloud Run, set `API_BASE_URL` for the frontend service.

## Backend Verification

Run the backend MVP test suite from the project virtualenv:

```bash
.venv\Scripts\python.exe -m unittest tests.test_backend_mvp
```

## Deploying to GCP

Deploy this repository as **two Cloud Run services**:

1. `medical-ai-backend` from the root `Dockerfile`
2. `medical-ai-frontend` from `Frontend-Capstone/Dockerfile`

`docker-compose.yml` is **not** used by Cloud Run. It is only for local development. On GCP:

- the backend container is reused
- the frontend container is reused
- the local Postgres container is replaced with **Cloud SQL for PostgreSQL**
- the local Redis container can be skipped for now because the current runtime code does not actively use Redis-backed features

### 1. Prerequisites

Install and authenticate the Google Cloud CLI:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud config set run/region us-central1
```

Enable the required APIs:

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com
```

### 2. Create Artifact Registry

Create one Docker repository for both images:

```bash
gcloud artifacts repositories create medical-ai \
  --repository-format=docker \
  --location=us-central1
```

### 3. Create Cloud SQL PostgreSQL

Create the managed Postgres instance, database, and application user:

```bash
gcloud sql instances create medical-ai-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

gcloud sql databases create medical_ai_db \
  --instance=medical-ai-db

gcloud sql users create admin \
  --instance=medical-ai-db \
  --password=YOUR_DB_PASSWORD
```

Your Cloud SQL connection name will be:

```text
YOUR_PROJECT_ID:us-central1:medical-ai-db
```

### 4. Build and Push the Backend Image

From the repository root:

```bash
gcloud builds submit \
  --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/medical-ai/medical-ai-backend:latest
```

### 5. Deploy the Backend to Cloud Run

Deploy the backend and attach Cloud SQL:

```bash
gcloud run deploy medical-ai-backend \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/medical-ai/medical-ai-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --add-cloudsql-instances YOUR_PROJECT_ID:us-central1:medical-ai-db \
  --set-env-vars APP_ENVIRONMENT=production,SECRET_KEY=YOUR_LONG_RANDOM_SECRET,ADMIN_BOOTSTRAP_EMAIL=YOUR_ADMIN_EMAIL,ADMIN_BOOTSTRAP_PASSWORD=YOUR_ADMIN_PASSWORD,ADMIN_BOOTSTRAP_TENANT=Northern\ Shield,DEBUG_TOKEN_PREVIEWS=true,DATABASE_URL='postgresql+psycopg2://admin:YOUR_DB_PASSWORD@/medical_ai_db?host=/cloudsql/YOUR_PROJECT_ID:us-central1:medical-ai-db'
```

Notes:

- `DEBUG_TOKEN_PREVIEWS=true` is recommended temporarily because OTP delivery is not yet wired to email or SMS. If you set it to `false`, users will not receive MFA codes.
- The backend trains the model during startup. The first cold start can take longer than a normal API service.
- The generated `raw_dataset.csv` and `sanitized_dataset.csv` files are ephemeral in Cloud Run and should not be treated as persistent storage.

After deploy, save the backend URL:

```text
https://medical-ai-backend-xxxxx-uc.a.run.app
```

### 6. Build and Push the Frontend Image

Build from the `Frontend-Capstone` directory:

```bash
gcloud builds submit Frontend-Capstone \
  --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/medical-ai/medical-ai-frontend:latest
```

### 7. Deploy the Frontend to Cloud Run

Point the frontend at the deployed backend:

```bash
gcloud run deploy medical-ai-frontend \
  --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/medical-ai/medical-ai-frontend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars API_BASE_URL=https://medical-ai-backend-xxxxx-uc.a.run.app/api/v1
```

The frontend proxy will forward browser requests to the backend without exposing internal service names in the client bundle.

### 8. Verify the Deployment

Check backend health:

```bash
curl https://medical-ai-backend-xxxxx-uc.a.run.app/api/v1/health
```

Confirm that:

- `status` is `ok`
- `model_runtime.loaded` is `true`
- `model_runtime.mode` is `xgboost`

Then open the frontend URL and test:

- signup
- login + MFA
- onboarding
- assessment
- results
- forecast
- admin dashboard

### 9. Mapping from docker-compose to GCP

These values in `docker-compose.yml` map to Cloud Run or Cloud SQL:

- `DATABASE_URL` -> backend Cloud Run environment variable
- `SECRET_KEY` -> backend Cloud Run environment variable or Secret Manager
- `ADMIN_BOOTSTRAP_EMAIL` -> backend Cloud Run environment variable
- `ADMIN_BOOTSTRAP_PASSWORD` -> backend Cloud Run environment variable or Secret Manager
- `ADMIN_BOOTSTRAP_TENANT` -> backend Cloud Run environment variable
- `API_BASE_URL` -> frontend Cloud Run environment variable

These local-only compose features do **not** carry over to Cloud Run:

- `container_name`
- `depends_on`
- local Docker networking such as `postgres` and `redis` hostnames
- exposed local ports like `5432:5432`
- container healthcheck orchestration

### 10. Recommended Next Hardening Steps

Before treating this as production-ready, complete these follow-ups:

1. Move secrets from plain env vars to Secret Manager.
2. Replace demo bootstrap credentials.
3. Restrict CORS in `main.py`.
4. Implement real OTP delivery before setting `DEBUG_TOKEN_PREVIEWS=false`.
5. Persist trained model artifacts instead of retraining on every backend startup.

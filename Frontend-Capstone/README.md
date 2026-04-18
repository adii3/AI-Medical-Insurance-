# Frontend Capstone

Next.js frontend for the AI Medical Insurance Platform.

## Features

- Signup and MFA login aligned to the FastAPI auth contract
- Consent onboarding
- Assessment form aligned to the backend profile schema
- Explainable results view
- 36-month premium forecast
- What-if simulator using `/predict/what-if`
- Admin analytics + sanitized export UI
- Password reset flow

## Local Development

```bash
npm install
npm run lint
npx tsc --noEmit
npm run build
```

For local development outside Docker, API calls proxy to `http://localhost:8000/api/v1` by default.

For container or Cloud Run deployment, set:

```bash
API_BASE_URL=<backend-base-url>/api/v1
```

The app proxies browser requests through `src/app/api/proxy/[...path]/route.ts`, so the client stays same-origin while the server forwards requests to the backend.

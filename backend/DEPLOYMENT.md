# FixIt backend deployment (Google Cloud Run)

This repository is prepared to run the FastAPI backend on Google Cloud Run. Cloud Run is selected because it scales to zero when idle and does not use Render's fixed 15-minute idle-sleep policy. A cold start can still occur after scaling to zero. Usage is not guaranteed to be free; attach a billing account, set a budget alert, and monitor actual usage.

## Before deployment

Create or select a Google Cloud project in the Google Cloud Console. Enable billing for that project, then enable the Cloud Run and Cloud Build APIs. Choose the `asia-south1` region (Mumbai) for a nearby India region.

Create a MongoDB Atlas M0 cluster and a dedicated database user. In Atlas Network Access, allow the Cloud Run egress approach you choose. For a first test, Atlas can allow broad access only if the database user has a strong, unique password; restrict network access before production. Copy the MongoDB connection string privately.

Configure an SMTP provider that supports authenticated SMTP. Keep its username and password private. These values must be entered in Cloud Run's environment/secret configuration, never committed to GitHub or pasted into chat.

## Deploy

From the repository root, with the Google Cloud CLI authenticated and the project selected:

```bash
gcloud config set project YOUR_GOOGLE_CLOUD_PROJECT_ID
gcloud run deploy fixit-api --source backend --region asia-south1 --allow-unauthenticated
```

The deployment command builds from `backend/Dockerfile`. The container listens on Cloud Run's injected `PORT`.

After the first deploy, copy the service URL, for example `https://fixit-api-xxxxx-uc.a.run.app`. The API root is that URL plus `/api`.

## Required Cloud Run environment variables

Set these in Cloud Run > fixit-api > Edit and deploy new revision. Use Secret Manager for `SECRET_KEY`, `MONGODB_URI`, and `SMTP_PASSWORD`.

| Variable | Value |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `SECRET_KEY` | Unique random secret, at least 64 characters |
| `MONGODB_URI` | Private Atlas connection URI with database credentials |
| `DATABASE_NAME` | `fixit_db` |
| `FALLBACK_TO_MOCK_DB` | `false` |
| `SEED_DEMO_DATA` | `false` |
| `PUBLIC_REGISTRATION_ENABLED` | `true` |
| `DOCS_ENABLED` | `false` |
| `ALLOWED_HOSTS` | `fixit-api-xxxxx-uc.a.run.app` (the exact backend hostname) |
| `BACKEND_CORS_ORIGINS` | JSON array containing the exact public Vercel frontend origin, e.g. `["https://fixit-roy952027-7769.vercel.app"]` |
| `APP_BASE_URL` | Exact public frontend URL, e.g. `https://fixit-roy952027-7769.vercel.app` |
| `COOKIE_SECURE` | `true` |
| `COOKIE_SAMESITE` | `none` |
| `SMTP_HOST` | SMTP provider host |
| `SMTP_PORT` | `587` |
| `SMTP_USERNAME` | SMTP username |
| `SMTP_PASSWORD` | SMTP password (Secret Manager) |
| `SMTP_FROM_EMAIL` | Verified sender email |
| `SMTP_STARTTLS` | `true` |

Use JSON array syntax for list variables. If you use a custom frontend domain, use that exact HTTPS origin instead. Do not include a trailing path in CORS origins.

## Connect Vercel

In Vercel > Project `fixit` > Settings > Environment Variables, set:

- `VITE_API_BASE_URL` = `https://YOUR-CLOUD-RUN-SERVICE-URL/api`
- `VITE_PUBLIC_REGISTRATION_ENABLED` = `true`
- `VITE_DEMO_MODE_ENABLED` = `false`

Apply to Production and Preview only where appropriate, then redeploy the frontend. Vite variables are embedded at build time; adding/changing them requires a new deployment.

## Verify after deployment

1. Open `https://YOUR-CLOUD-RUN-SERVICE-URL/health`. It must return HTTP 200 and `mongodb_connected`.
2. Open `https://YOUR-CLOUD-RUN-SERVICE-URL/api/institutions`. It should return the active institution list.
3. Open the FixIt frontend and verify the college selector loads.
4. Register using a college email and confirm OTP delivery.
5. Test login, password reset, ticket creation, and role/tenant isolation.

Do not announce public launch until these checks pass. A successful container deployment alone does not prove that database, SMTP, CORS, or authentication are configured correctly.

## Cost and safety

Cloud Run has a monthly free usage allowance for eligible usage, but billing must be enabled and excess usage can incur charges. Configure a billing budget alert before deployment; budget alerts notify you but do not automatically cap spending. Avoid adding a payment-dependent minimum instance count if the goal is to minimize cost. Keep database backups and review Atlas limits before onboarding real colleges.

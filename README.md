# FixIt — Campus Support Platform

FixIt is a flexible issue-intake and resolution platform for students, faculty, staff, and administrators. It starts with campus IT helpdesk workflows and also supports academic, administrative, facilities, student-support, community, and other requests.

## Supported request domains

The ticket workflow supports these request domains:

- **Technical:** devices, software, accounts, connectivity, and IT services.
- **Academic:** learning support, subject guidance, project support, and academic resources.
- **Administrative:** forms, documentation, campus processes, and service enquiries.
- **Facilities:** maintenance, utilities, classroom equipment, and campus infrastructure.
- **Student support:** guidance and requests that should be routed to an appropriate, authorized support team.
- **Community:** shared concerns and community assistance.
- **Other:** requests that do not fit a listed domain.

Each request can be associated with a campus location, an online/remote context, or no specific location. Campus-located tickets continue to use the configured campus/building/floor/room hierarchy. Remote and location-independent tickets use the same authentication, assignment, status, notification, audit, and SLA workflow without requiring campus coordinates.

The domain is a routing classification, not a promise that FixIt itself can provide every specialist service. Sensitive or high-risk requests must be routed to trained, authorized people; the platform should not present automated responses as medical, legal, financial, or emergency advice.

## Included user-facing features

- **Notifications:** authenticated in-app alerts, read/unread state, and per-user notification preferences. Email delivery is optional and requires SMTP configuration.
- **Profiles:** editable name, department, phone, HTTPS profile-image URL or uploaded profile picture; password changes revoke existing sessions.
- **Preferences:** light/dark appearance, saved English, Hindi, Kannada, Tamil, Telugu, Malayalam, Marathi and Bengali language preference, and in-app/email notification toggles. Translation coverage is currently partial: shared navigation and profile/security preferences have translations across the supported languages, while many page-specific labels and workflows remain in English.
- **Ticket conversations:** ticket-specific replies, staff-only internal notes, chronological history, and up to five uploaded attachments per message. Authenticated uploads support JPG, PNG, WEBP, GIF, PDF and TXT files up to 5 MB each. Files are stored in MongoDB and downloads are authorized against the user's ticket access; profile images are restricted to their owner and administrators. For larger deployments, use dedicated object storage rather than growing MongoDB documents.
- **Knowledge base:** searchable articles, FAQs, categories, helpfulness feedback, staff/admin article creation and editing, draft publishing, and admin-only deletion with audit records.

### Optional email delivery

Configure these environment variables on the backend to enable email notifications. If SMTP is not configured, in-app notifications continue to work and email is skipped.

```env
APP_BASE_URL=https://your-fixit-domain.example
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_STARTTLS=true
```

## Project structure

- `backend/` — FastAPI API, MongoDB integration, authentication, ticket workflows, and automated tests.
- `frontend/` — React + Vite web application.
- `docker-compose.production.yml` — production container orchestration for the frontend and backend.
- `.env.production.example` — template only; it contains no real credentials.

## Run locally on Windows

Use two terminals.

**Terminal 1 — backend**

```powershell
cd .\backend
# Activate your existing Python virtual environment first.
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
```

**Terminal 2 — frontend**

```powershell
cd .\frontend
npm ci
npm run dev
```

Open `http://localhost:5173`.

The Vite development proxy targets `http://127.0.0.1:8002` by default. To use another backend port, set `VITE_DEV_API_PROXY_TARGET` in `frontend/.env.local`, for example:

```env
VITE_DEV_API_PROXY_TARGET=http://127.0.0.1:8001
```

## Verification

```powershell
# Backend
cd .\backend
python -m pytest -q

# Frontend
cd ..\frontend
npm ci
npm run test
npm run build
```

## Production deployment

1. Provision a MongoDB database (MongoDB Atlas is suitable) and create a dedicated application database user with only the permissions the app needs.
2. Copy `.env.production.example` to `.env.production` in the project root.
3. Replace every placeholder. Use a unique `SECRET_KEY` of at least 64 characters, a MongoDB URI with a URL-encoded password, the actual public hostname in `ALLOWED_HOSTS`, and the matching HTTPS origin in `BACKEND_CORS_ORIGINS`.
4. Keep public registration, demo seeding, mock-database fallback, and API docs disabled for production.
5. Run `docker compose -f docker-compose.production.yml up --build -d`.
6. Put the frontend behind a TLS-enabled reverse proxy or hosting platform. The included frontend container listens on port 8080 on the host; configure HTTPS and DNS at your hosting provider.
7. Confirm `/health` reports `mongodb_connected` and test login, ticket creation, assignment, comments, notifications, and role permissions before opening access to users.

The deployment template deliberately does not create a database, seed demo users, or invent credentials. Do not upload `.env.production` to source control or share it in chat.

## Data safety

- Back up the database before deploying any application update.
- Do not drop the database or collections to apply code updates.
- The seed routine is insert-only and skips existing matching records.
- The supplied archive does not contain your private `.env`, live MongoDB database, or production account credentials.
- Demo account shortcuts and public registration controls are development-only. Production backend settings independently disable public registration and demo seeding.
- Use a unique administrator password. Do not use demo credentials for a real deployment.

See `backend/README_QA.md` for backend setup and first-administrator bootstrap details.

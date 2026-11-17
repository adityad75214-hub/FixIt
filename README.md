# FixIt — College IT Helpdesk & Campus Issue Management System

FixIt is a single-college issue and IT helpdesk platform for students, faculty, IT staff, and administrators.

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

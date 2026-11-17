# FixIt — Backend setup and QA notes

This is the single-college FixIt backend. It uses FastAPI and MongoDB. The seed process is now insert-only: it skips records that already exist and does not update or replace existing users, campus hierarchy, categories, SLA policies, articles, tickets, comments, or feedback.

## 1. Configure the backend

Create `backend/.env` from `.env.example` and set the MongoDB connection details. Keep this file private and do not commit it.

```powershell
cd E:\FixIt_Complete\backend
Copy-Item .env.example .env
notepad .env
```

For an existing installation, preserve your current `.env`; do not replace it with the example. The backend reads this file from the `backend` directory.

## 2. Run the backend

Use your existing Python environment and dependencies:

```powershell
cd E:\FixIt_Complete\backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Health check: `http://127.0.0.1:8001/health`

## 3. Create the first administrator (optional)

If this database does not already contain an administrator, set these values in `backend/.env`:

```env
FIRST_ADMIN_EMAIL=admin@your-college-domain.edu
FIRST_ADMIN_PASSWORD=use-a-unique-password-of-at-least-12-characters
FIRST_ADMIN_NAME=College IT Administrator
```

Then run:

```powershell
cd E:\FixIt_Complete\backend
python -m app.bootstrap_admin
```

The bootstrap command creates an admin only when the configured email is unused. It does not promote an existing non-admin account, reset an existing admin password, or overwrite an existing account. Never use the demo password as a real administrator password.

## 4. Run automated backend tests

```powershell
cd E:\FixIt_Complete\backend
python -m pytest -q
```

The tests use an in-memory mock database and do not modify the live MongoDB database.

## 5. Data-safety notes

- Do not delete the MongoDB database or collections to apply these fixes.
- Do not run a destructive migration or reseed against an existing database.
- Demo records are development-only. Production configuration rejects demo seeding, mock-database fallback, and public registration.
- The seed routine uses insert-only behavior to avoid overwriting existing records.

## QA baseline supplied by the project owner

Before this update, the owner ran the existing backend test suite locally and reported **62 passed, 0 failed** in 32.72 seconds. The run emitted 296 deprecation warnings from Python/FastAPI/Starlette/mongomock dependencies. These are baseline results, not a claim that the modified copy has already passed the suite.

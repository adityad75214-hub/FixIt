from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection, db_manager

# Import all API routers
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.tickets import router as tickets_router
from app.api.assignments import router as assignments_router
from app.api.comments import router as comments_router
from app.api.notifications import router as notifications_router
from app.api.categories import router as categories_router
from app.api.campus import router as campus_router
from app.api.sla import router as sla_router
from app.api.knowledge_base import router as kb_router
from app.api.feedback import router as feedback_router
from app.api.analytics import router as analytics_router
from app.api.reports import router as reports_router
from app.api.audit_logs import router as audit_logs_router
from app.api.incidents import router as incidents_router
from app.api.feature_requests import router as feature_requests_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to DB
    await connect_to_mongo()
    if settings.is_production:
        # Provision only generic categories and SLA defaults; never insert demo users/tickets.
        from app.seed_reference_data import seed_reference_data
        await seed_reference_data()
    elif settings.SEED_DEMO_DATA:
        from app.seed import seed_data
        await seed_data()

    yield
    # Shutdown: Close DB
    await close_mongo_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Centralized College IT Helpdesk and Campus Issue Management System REST API",
    version="1.0.0",
    docs_url="/api/docs" if settings.DOCS_ENABLED and not settings.is_production else None,
    redoc_url="/api/redoc" if settings.DOCS_ENABLED and not settings.is_production else None,
    openapi_url="/api/openapi.json" if settings.DOCS_ENABLED and not settings.is_production else None,
    lifespan=lifespan
)

# Reject unexpected Host headers (helps prevent Host-header based attacks).
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# Global health check
@app.get("/health", tags=["Health"])
async def health_check():
    if db_manager.is_mock:
        ready = not settings.is_production
        database_status = "mock_in_memory"
    elif db_manager.client is not None and db_manager.db is not None:
        try:
            await db_manager.client.admin.command("ping")
            ready = True
            database_status = "mongodb_connected"
        except Exception:
            ready = False
            database_status = "unavailable"
    else:
        ready = False
        database_status = "unavailable"

    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "healthy" if ready else "not_ready",
            "service": settings.PROJECT_NAME,
            "database": database_status,
        },
    )

# Register all Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(tickets_router, prefix=settings.API_V1_STR)
app.include_router(assignments_router, prefix=settings.API_V1_STR)
app.include_router(comments_router, prefix=settings.API_V1_STR)
app.include_router(notifications_router, prefix=settings.API_V1_STR)
app.include_router(categories_router, prefix=settings.API_V1_STR)
app.include_router(campus_router, prefix=settings.API_V1_STR)
app.include_router(sla_router, prefix=settings.API_V1_STR)
app.include_router(kb_router, prefix=settings.API_V1_STR)
app.include_router(feedback_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(audit_logs_router, prefix=settings.API_V1_STR)
app.include_router(incidents_router, prefix=settings.API_V1_STR)
app.include_router(feature_requests_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

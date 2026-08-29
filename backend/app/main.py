from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.app.api import dev
from backend.app.api.activities import router as activities_router
from backend.app.api.admin import router as admin_router
from backend.app.api.auth import router as auth_router
from backend.app.api.contact import router as contact_router
from backend.app.api.events import router as events_router
from backend.app.api.members import router as members_router
from backend.app.api.news import router as news_router
from backend.app.api.notifications import router as notifications_router
from backend.app.api.statistics import router as statistics_router
from backend.app.core.config import get_settings
from backend.app.core.database import engine


from backend.app.ai.router import router as ai_router

settings = get_settings()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for Knights of Bizertin Rise",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router)
app.include_router(members_router)
app.include_router(admin_router)
app.include_router(statistics_router)
app.include_router(events_router)
app.include_router(news_router)
app.include_router(activities_router)
app.include_router(contact_router)
app.include_router(notifications_router)
app.include_router(dev.router)

app.include_router(
    ai_router,
)

@app.get(
    "/",
    summary="API information",
)
def root() -> dict[str, str]:
    return {
        "message": "KBR API is running",
        "version": settings.app_version,
    }


@app.get(
    "/health",
    summary="Application health check",
)
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@app.get(
    "/health/db",
    summary="Database health check",
)
def database_health_check() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception:
        return {
            "status": "unhealthy",
            "database": "disconnected",
        }
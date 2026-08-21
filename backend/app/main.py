from fastapi import FastAPI

from backend.app.api.admin import router as admin_router
from backend.app.api.auth import router as auth_router
from backend.app.api import dev
from backend.app.api.members import router as members_router
from backend.app.core.config import get_settings
from backend.app.core.database import engine


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for Knights of Bizertin Rise",
)


app.include_router(auth_router)
app.include_router(members_router)
app.include_router(admin_router)
app.include_router(dev.router)


@app.get("/")
def root():
    return {
        "message": "KBR API is running",
        "version": settings.app_version,
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
    }


@app.get("/health/db")
def database_health_check():
    from sqlalchemy import text

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
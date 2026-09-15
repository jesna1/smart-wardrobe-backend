import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.orm import configure_mappers
import app.models
configure_mappers()
from app.core.config import settings
from app.core.database import get_db
from app.schemas.health import HealthCheckResponse
from app.api.v1.api import api_router

os.makedirs("uploads", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for Flutter mobile and web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mount
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Single entry point for all API v1 routes
app.include_router(api_router, prefix="/api/v1")

# Base / Health Endpoints
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health",
    }

@app.get("/health", response_model=HealthCheckResponse, tags=["Health Check"])
async def health_check(db: AsyncSession = Depends(get_db)):
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"

    return HealthCheckResponse(
        status=f"healthy (Database: {db_status})",
        app_name=settings.PROJECT_NAME,
        version=settings.VERSION,
    )
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db, engine, Base
from app.schemas.health import HealthCheckResponse
from app.api.v1.endpoints import wardrobe, outfits, seed, auth

os.makedirs("uploads", exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        # 1. Create pgvector extension if running on PostgreSQL
        if engine.dialect.name == "postgresql":
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        # 2. Create tables FIRST before altering columns
        await conn.run_sync(Base.metadata.create_all)

        # 3. Alter tables to add new columns if necessary
        if engine.dialect.name == "postgresql":
            await conn.execute(text("ALTER TABLE wardrobe_items ADD COLUMN IF NOT EXISTS occasion VARCHAR(50);"))
            await conn.execute(text("ALTER TABLE wardrobe_items ADD COLUMN IF NOT EXISTS category_id INTEGER;"))
        elif engine.dialect.name == "sqlite":
            try:
                await conn.execute(text("ALTER TABLE wardrobe_items ADD COLUMN occasion VARCHAR(50);"))
            except Exception:
                pass
            try:
                await conn.execute(text("ALTER TABLE wardrobe_items ADD COLUMN category_id INTEGER;"))
            except Exception:
                pass

    yield

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

# Enable CORS for Flutter mobile and web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(wardrobe.router, prefix="/api/v1/wardrobe", tags=["Wardrobe"])
app.include_router(outfits.router, prefix="/api/v1/outfits", tags=["Outfits"])
app.include_router(seed.router, prefix="/api/v1/dev", tags=["Developer Services"])

@app.get("/health", response_model=HealthCheckResponse)
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
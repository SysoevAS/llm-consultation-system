from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.infra.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "env": settings.env,
        "auth_service_url": settings.auth_service_url,
    }
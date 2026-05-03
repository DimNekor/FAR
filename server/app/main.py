from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.app.core.config import settings
from server.app.core.database import engine, Base
from server.app.api.v1.endpoints import health, sync

import server.app.models


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

# CORS для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(sync.router, prefix="/api/v1", tags=["sync"])


@app.get("/")
async def root():
    return {"message": "FAR API", "version": settings.VERSION}

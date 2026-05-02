from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.app.core.config import settings
from server.app.api.v1.endpoints import health

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
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


@app.get("/")
async def root():
    return {"message": "FAR API", "version": settings.VERSION}

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from server.app.core.config import settings

# Асинхронный движок
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)

# Асинхронная фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Асинхронная зависимость FastAPI"""
    async with AsyncSessionLocal() as session:
        yield session

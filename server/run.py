import uvicorn
from server.app.core.config import settings


def start():
    uvicorn.run(
        "server.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    uvicorn.run(
        "server.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )

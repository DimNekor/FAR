from fastapi import HTTPException, Header
from server.app.core.config import settings


async def verify_api_key(x_api_key: str = Header(...)):
    """Проверяет API-ключ в заголовке X-API-Key."""
    if x_api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

import asyncio
import aiohttp
from client.utils.config import config


class APIClient:
    def __init__(self):
        self.base_url = config.server_url.rstrip("/")
        self._session = None

    async def _get_session(self):
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def _check_health_async(self):
        """Проверка доступности сервера"""
        session = await self._get_session()
        try:
            async with session.get(f"{self.base_url}/api/v1/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return True, data.get("version", "unknown")
                return False, f"HTTP {resp.status}"
        except aiohttp.ClientConnectorError:
            return False, "Сервер недоступен"
        except asyncio.TimeoutError:
            return False, "Таймаут соединения"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"

    def check_health(self):
        return asyncio.run(self._check_health_async())

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


api_client = APIClient()

import asyncio
import requests
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

    def sync_database(self) -> dict:
        """Отправить локальную БД на сервер и получить обновлённые данные."""
        from client.models.database import Database

        db = Database()

        # Собираем локальные данные
        local_data = db.get_all_data_for_sync()

        try:
            resp = requests.post(
                f"{self.base_url}/api/v1/sync",
                json=local_data,
                timeout=30,
            )
            if resp.status_code == 200:
                result = resp.json()
                server_data = result.get("server_data", {})

                # Сохраняем то, что пришло с сервера
                save_result = db.save_synced_data(server_data)

                return {
                    "success": True,
                    "sent_to_server": result.get("saved", {}),
                    "saved_from_server": save_result,
                }
            else:
                return {"success": False, "message": f"HTTP {resp.status_code}"}
        except requests.ConnectionError:
            return {"success": False, "message": "Сервер недоступен"}
        except Exception as e:
            return {"success": False, "message": str(e)}


api_client = APIClient()

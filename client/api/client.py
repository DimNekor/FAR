import asyncio
import requests
import aiohttp
import sys
from datetime import datetime
from pathlib import Path
from client.utils.config.config import config


class APIClient:
    def __init__(self):
        self.base_url = config.server_url.rstrip("/")
        self._session = None
        self._loop = None

    def _get_loop(self):
        """Получить или создать event loop для потока"""
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    def _headers(self):
        return {"X-API-Key": config.api_key}

    def _platform(self) -> str:
        if sys.platform.startswith("win"):
            return "windows"
        elif sys.platform.startswith("linux"):
            return "linux"
        elif sys.platform.startswith("darwin"):
            return "macos"
        return "unknown"

    async def _get_session(self):
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def _check_health_async(self):
        session = await self._get_session()
        try:
            async with session.get(
                f"{self.base_url}/api/v1/health", headers=self._headers()
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return True, data.get("version", "unknown")
                return False, f"HTTP {resp.status_code}"
        except aiohttp.ClientConnectorError:
            return False, "Сервер недоступен"
        except asyncio.TimeoutError:
            return False, "Таймаут соединения"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"

    def check_health(self):
        """Синхронная обёртка — можно вызывать из любого потока"""
        loop = self._get_loop()
        return loop.run_until_complete(self._check_health_async())

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    # def check_health(self):
    #     """Проверка доступности сервера"""
    #     try:
    #         resp = requests.get(
    #             f"{self.base_url}/api/v1/health",
    #             headers=self._headers(),
    #             timeout=5,
    #         )
    #         print(f"DEBUG: Response status: {resp.status_code}")
    #         if resp.status_code == 200:
    #             data = resp.json()
    #             return True, data.get("version", "unknown")
    #         return False, f"HTTP {resp.status_code}"
    #     except requests.ConnectionError:
    #         print("DEBUG: Connection error")
    #         return False, "Сервер недоступен"
    #     except requests.Timeout:
    #         print("DEBUG: Timeout")
    #         return False, "Таймаут соединения"
    #     except Exception as e:
    #         print(f"DEBUG: Error: {e}")
    #         return False, f"Ошибка: {str(e)}"

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
                headers=self._headers(),
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

    def sync_images(self) -> dict:
        """
        Синхронизация изображений с сервером.
        """
        from client.models.database import Database
        import os
        from pathlib import Path

        # Получаем список локальных файлов с датами
        images_dir = Path(__file__).parent.parent / "static" / "images"
        local_files = {}

        if images_dir.exists():
            for filepath in images_dir.iterdir():
                if filepath.is_file() and filepath.suffix.lower() in (
                    ".png",
                    ".jpg",
                    ".jpeg",
                ):
                    mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
                    local_files[filepath.name] = mtime.isoformat()

        try:
            # Шаг 1: Сравниваем списки
            resp = requests.post(
                f"{self.base_url}/api/v1/sync-images/compare",
                json=local_files,
                headers=self._headers(),
                timeout=30,
            )
            if resp.status_code != 200:
                return {"success": False, "message": f"HTTP {resp.status_code}"}

            result = resp.json()
            client_needs = result.get("client_needs", [])
            server_needs = result.get("server_needs", [])

            downloaded = 0
            uploaded = 0

            # Шаг 2: Скачиваем файлы, которых нет у клиента
            for filename in client_needs:
                resp = requests.get(
                    f"{self.base_url}/api/v1/sync-images/download/{filename}",
                    headers=self._headers(),
                    timeout=60,
                )
                if resp.status_code == 200:
                    filepath = images_dir / filename
                    with open(filepath, "wb") as f:
                        f.write(resp.content)
                    downloaded += 1

            # Шаг 3: Загружаем файлы, которых нет у сервера
            for filename in server_needs:
                filepath = images_dir / filename
                if filepath.exists():
                    with open(filepath, "rb") as f:
                        files = {"file": (filename, f, "image/png")}
                        resp = requests.post(
                            f"{self.base_url}/api/v1/sync-images/upload/{filename}",
                            files=files,
                            headers=self._headers(),
                            timeout=60,
                        )
                        if resp.status_code == 200:
                            uploaded += 1

            return {
                "success": True,
                "downloaded": downloaded,
                "uploaded": uploaded,
            }

        except Exception as e:
            return {"success": False, "message": str(e)}

    def _platform(self) -> str:
        """Определить текущую платформу"""
        if sys.platform.startswith("win"):
            return "windows"
        elif sys.platform.startswith("linux"):
            return "linux"
        elif sys.platform.startswith("darwin"):
            return "macos"
        return "unknown"

    def check_updates(self, current_version: str) -> dict:
        """Проверить обновления на сервере"""
        try:
            resp = requests.get(
                f"{self.base_url}/api/v1/updates/check",
                params={
                    "current_version": current_version,
                    "platform": self._platform(),
                },
                headers=self._headers(),
                timeout=5,
            )
            if resp.status_code == 200:
                return resp.json()
            return {"update_available": False, "message": f"HTTP {resp.status_code}"}
        except Exception as e:
            return {"update_available": False, "message": str(e)}


api_client = APIClient()

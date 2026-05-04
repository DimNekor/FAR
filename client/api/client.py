import sys
import os
import requests
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from client.utils.config.config import config


class APIClient:
    def __init__(self):
        self.base_url = config.server_url.rstrip("/")
        self._session = None

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

    # --- Health ---
    def check_health(self):
        try:
            resp = requests.get(
                f"{self.base_url}/api/v1/health",
                headers=self._headers(),
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                return True, data.get("version", "unknown")
            return False, f"HTTP {resp.status_code}"
        except requests.ConnectionError:
            return False, "Сервер недоступен"
        except requests.Timeout:
            return False, "Таймаут соединения"
        except Exception as e:
            return False, f"Ошибка: {str(e)}"

    # --- Updates ---
    def check_updates(self, current_version: str) -> dict:
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

    def download_update(self, update_info: dict, progress_callback=None) -> str | None:
        download_url = update_info.get("download_url")
        if not download_url:
            return None

        if getattr(sys, "frozen", False):
            if sys.platform == "win32":
                save_dir = Path(os.environ.get("APPDATA", ".")) / "FAR" / "updates"
            elif sys.platform == "darwin":
                save_dir = (
                    Path.home() / "Library" / "Application Support" / "FAR" / "updates"
                )
            else:
                save_dir = Path.home() / ".config" / "FAR" / "updates"
        else:
            save_dir = Path(__file__).parent.parent / "updates"

        save_dir.mkdir(parents=True, exist_ok=True)

        version = update_info.get("version", "unknown")
        ext = ".zip" if self._platform() == "windows" else ".tar.gz"
        filename = f"FAR_{self._platform()}_{version}{ext}"
        filepath = save_dir / filename

        try:
            resp = requests.get(
                f"{self.base_url}{download_url}",
                headers=self._headers(),
                stream=True,
                timeout=300,
            )
            resp.raise_for_status()

            total_size = int(resp.headers.get("content-length", 0))
            downloaded = 0

            with open(filepath, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0 and progress_callback:
                            percent = int(downloaded / total_size * 100)
                            progress_callback(percent)

            return str(filepath)
        except Exception as e:
            print(f"Download error: {e}")
            return None

    # --- Sync DB ---
    def sync_database(self) -> dict:
        from client.models.database import Database

        db = Database()
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

    # --- Sync Images ---
    def sync_images(self) -> dict:
        from pathlib import Path

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


api_client = APIClient()

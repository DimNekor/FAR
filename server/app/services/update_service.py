import json
import os
from pathlib import Path
from datetime import datetime


class UpdateService:
    def __init__(self):
        self.builds_dir = (
            Path(__file__).parent.parent.parent / "static" / "app" / "builds"
        )
        self.metadata_file = self.builds_dir / "metadata.json"
        self.builds_dir.mkdir(parents=True, exist_ok=True)

    def _load_metadata(self):
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                return json.load(f)
        return {}

    def _save_metadata(self, data):
        with open(self.metadata_file, "w") as f:
            json.dump(data, f, indent=2)

    async def check_update(self, current_version: str, platform: str):
        metadata = self._load_metadata()
        builds = metadata.get("builds", {}).get(platform, {})

        if not builds:
            return {
                "update_available": False,
                "message": "Нет сборок для этой платформы",
            }

        # Ищем последнюю версию
        latest_version = max(builds.keys())

        if latest_version > current_version:
            info = builds[latest_version]
            return {
                "update_available": True,
                "version": latest_version,
                "download_url": f"/api/v1/updates/download/{platform}/{latest_version}",
                "file_size": info.get("size", 0),
                "changelog": info.get("changelog", ""),
                "mandatory": info.get("mandatory", False),
            }

        return {"update_available": False, "message": "У вас последняя версия"}

    async def add_build(
        self,
        platform: str,
        version: str,
        file_path: Path,
        changelog: str = "",
        mandatory: bool = False,
    ):
        """Добавить новую сборку"""
        metadata = self._load_metadata()

        if "builds" not in metadata:
            metadata["builds"] = {}
        if platform not in metadata["builds"]:
            metadata["builds"][platform] = {}

        # Копируем файл
        dest = self.builds_dir / f"{platform}_{version}.tar.gz"
        import shutil

        shutil.copy(file_path, dest)

        metadata["builds"][platform][version] = {
            "size": dest.stat().st_size,
            "changelog": changelog,
            "mandatory": mandatory,
            "uploaded_at": datetime.utcnow().isoformat(),
        }

        self._save_metadata(metadata)
        return {"status": "ok", "version": version}

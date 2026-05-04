import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class ImageSyncService:
    def __init__(self, images_dir: str = None):
        if images_dir is None:
            # Относительно этого файла: server/app/services/ -> server/static/images/
            self.images_dir = Path(__file__).parent.parent.parent / "static" / "images"
        else:
            self.images_dir = Path(images_dir)

        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.images_dir / "metadata.json"

    def _get_file_info(self, filepath: Path) -> dict:
        """Получить информацию о файле."""
        stat = filepath.stat()
        return {
            "filename": filepath.name,
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

    def scan_directory(self) -> Dict[str, dict]:
        """Сканирует папку и возвращает словарь {имя_файла: информация}."""
        files = {}
        if self.images_dir.exists():
            for filepath in self.images_dir.iterdir():
                if filepath.is_file() and filepath.suffix.lower() in (
                    ".png",
                    ".jpg",
                    ".jpeg",
                ):
                    files[filepath.name] = self._get_file_info(filepath)
        return files

    def save_metadata(self):
        """Сохраняет текущее состояние папки в metadata.json."""
        files = self.scan_directory()
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(files, f, indent=2, ensure_ascii=False)

    def load_metadata(self) -> Dict[str, dict]:
        """Загружает metadata.json."""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def compare(self, client_files: Dict[str, str]) -> dict:
        """
        Сравнивает файлы клиента с серверными.
        client_files: {имя_файла: "2026-05-03T12:00:00"}

        Возвращает:
        {
            "client_needs": [имя_файла, ...],  # файлы, которых нет у клиента или новее на сервере
            "server_needs": [имя_файла, ...],  # файлы, которых нет на сервере или новее у клиента
        }
        """
        server_files = self.load_metadata()

        client_needs = []
        server_needs = []

        # Что нужно клиенту (есть на сервере, нет у клиента или серверная новее)
        for filename, server_info in server_files.items():
            if filename not in client_files:
                client_needs.append(filename)
            else:
                server_date = datetime.fromisoformat(server_info["modified"])
                client_date = datetime.fromisoformat(client_files[filename])
                if server_date > client_date:
                    client_needs.append(filename)

        # Что нужно серверу (есть у клиента, нет на сервере или клиентская новее)
        for filename, client_date_str in client_files.items():
            if filename not in server_files:
                server_needs.append(filename)
            else:
                client_date = datetime.fromisoformat(client_date_str)
                server_date = datetime.fromisoformat(server_files[filename]["modified"])
                if client_date > server_date:
                    server_needs.append(filename)

        return {
            "client_needs": client_needs,
            "server_needs": server_needs,
        }

    def get_file_path(self, filename: str) -> Path:
        """Получить полный путь к файлу в папке images."""
        return self.images_dir / filename

    def save_uploaded_file(self, filename: str, content: bytes):
        """Сохранить загруженный клиентом файл."""
        filepath = self.images_dir / filename
        with open(filepath, "wb") as f:
            f.write(content)
        # Обновить метаданные
        self.save_metadata()

import json
import os
import sys
from pathlib import Path


class Config:
    def __init__(self):
        self._config = {}
        self._load()

    def _get_config_dir(self):
        """Где хранить пользовательский конфиг"""
        if getattr(sys, "frozen", False):
            app_name = "FAR"
            if sys.platform == "win32":
                base = Path(os.environ.get("APPDATA", "."))
            elif sys.platform == "darwin":
                base = Path.home() / "Library" / "Application Support"
            else:
                base = Path.home() / ".config"
            return base / app_name
        else:
            return Path(__file__).parent

    def _get_default_config_path(self):
        """Путь к default_config.json"""
        if getattr(sys, "frozen", False):
            # В собранном приложении — рядом с бинарником в папке config/
            return Path(sys._MEIPASS) / "config" / "default_config.json"
        else:
            # При разработке
            return (
                Path(__file__).parent.parent.parent / "config" / "default_config.json"
            )

    def _load(self):
        config_dir = self._get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)

        user_config = config_dir / "config.json"
        default_config = self._get_default_config_path()

        if not user_config.exists():
            if default_config.exists():
                with open(default_config, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                with open(user_config, "w", encoding="utf-8") as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
            else:
                self._config = {"server_url": "http://localhost:8000"}
        else:
            with open(user_config, "r", encoding="utf-8") as f:
                self._config = json.load(f)

    @property
    def server_url(self):
        return self._config.get("server_url", "http://localhost:8000")

    @server_url.setter
    def server_url(self, value):
        self._config["server_url"] = value
        self._save()

    @property
    def api_key(self):
        return self._config.get("api_key", "")

    @api_key.setter
    def api_key(self, value):
        self._config["api_key"] = value
        self._save()

    def _save(self):
        config_dir = self._get_config_dir()
        user_config = config_dir / "config.json"
        with open(user_config, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)


config = Config()

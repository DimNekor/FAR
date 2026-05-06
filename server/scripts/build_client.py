import subprocess
import sys
from pathlib import Path
import zipfile
import os

def build(platform: str, version: str):
    """Собрать клиент и добавить в обновления"""
    sep = ";" if os.name == "nt" else ":"

    project_root = Path(__file__).parent.parent.parent  # ~/FAR
    dist_path = project_root / "builds"
    dist_path.mkdir(exist_ok=True)

    # Создать папки, если их нет (в .gitignore)
    (project_root / "client" / "static" / "images").mkdir(parents=True, exist_ok=True)
    (project_root / "client" / "config").mkdir(parents=True, exist_ok=True)

    config_file = project_root / "client" / "config" / "default_config.json"
    if not config_file.exists():
        config_file.write_text(
        '{"server_url": "localhost", "api_key": "my_secret_key"}'
        )

    exe_name = "FAR.exe" if platform == "windows" else "FAR"

    # Обновить версию
    version_file = project_root / "client" / "version.py"
    with open(version_file, "w") as f:
        f.write(f'__version__ = "{version}"\n')

    # PyInstaller
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name",
        exe_name,
        "--distpath",
        str(dist_path),
        "--workpath",
        str(dist_path / "temp"),
        "--specpath",
        str(dist_path),
        "--add-data",
        f"{project_root / 'client' / 'kv'}:kv",
        "--add-data",
        f"{project_root / 'client' / 'static'}:static",
        "--add-data",
        f"{project_root / 'client' / 'config'}:config",
        "--hidden-import", "win32timezone",
        str(project_root / "client" / "main.py"),
    ]

    subprocess.run(cmd, check=True, cwd=str(project_root))

    # Упаковать
    if platform == "windows":
        archive_name = f"FAR_{platform}_{version}.zip"
        archive_path = dist_path / archive_name
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(dist_path / exe_name, exe_name)
    else:
        archive_name = f"FAR_{platform}_{version}.tar.gz"
        archive_path = dist_path / archive_name
        subprocess.run(
            ["tar", "-czf", str(archive_path), exe_name],
            check=True,
            cwd=str(dist_path),
        )

    size_kb = archive_path.stat().st_size / 1024
    print(f"[OK] Build: {archive_path} ({size_kb:.1f} KB)")

    # Добавить в сервис обновлений
    import asyncio

    sys.path.insert(0, str(Path(__file__).parent.parent))
    from app.services.update_service import UpdateService

    async def add():
        service = UpdateService()
        result = await service.add_build(
            platform=platform,
            version=version,
            file_path=archive_path,
            changelog="",
            mandatory=False,
        )
        print(result)

    asyncio.run(add())


if __name__ == "__main__":
    platform = sys.argv[1]
    version = sys.argv[2]
    build(platform, version)

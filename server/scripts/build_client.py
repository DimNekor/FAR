import subprocess
import sys
from pathlib import Path


def build(platform: str, version: str):
    """Собрать клиент и добавить в обновления"""

    project_root = Path(__file__).parent.parent.parent  # ~/FAR
    dist_path = project_root / "builds"
    dist_path.mkdir(exist_ok=True)

    # Определяем имя файла
    if platform == "windows":
        exe_name = "FAR.exe"
    else:
        exe_name = "FAR"

    # Обновляем версию в client/version.py
    version_file = project_root / "client" / "version.py"
    with open(version_file, "w") as f:
        f.write(f'__version__ = "{version}"\n')

    # Запускаем PyInstaller
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
        str(project_root / "client" / "main.py"),
    ]

    subprocess.run(cmd, check=True, cwd=str(project_root))

    # Упаковываем в tar.gz
    archive_name = f"FAR_{platform}_{version}.tar.gz"
    archive_path = dist_path / archive_name

    subprocess.run(
        ["tar", "-czf", str(archive_path), exe_name],
        check=True,
        cwd=str(dist_path),
    )

    print(f"Сборка готова: {archive_path}")

    # Добавляем в сервис обновлений
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
    platform = sys.argv[1]  # linux, windows
    version = sys.argv[2]  # 1.0.1

    build(platform, version)

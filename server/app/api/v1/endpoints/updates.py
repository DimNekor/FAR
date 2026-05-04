from fastapi import APIRouter, Query
from fastapi.responses import FileResponse
from server.app.services.update_service import UpdateService

router = APIRouter()
update_service = UpdateService()


@router.get("/updates/check")
async def check_update(
    current_version: str = Query(...),
    platform: str = Query("windows"),
):
    return await update_service.check_update(current_version, platform)


@router.get("/updates/download/{platform}/{version}")
async def download_update(platform: str, version: str):
    # Ищем файл — .zip для windows, .tar.gz для остальных
    ext = ".zip" if platform == "windows" else ".tar.gz"
    filename = f"FAR_{platform}_{version}{ext}"
    filepath = update_service.builds_dir / filename

    if not filepath.exists():
        return {"error": "Сборка не найдена"}

    media_type = "application/zip" if platform == "windows" else "application/gzip"
    return FileResponse(filepath, filename=filename, media_type=media_type)

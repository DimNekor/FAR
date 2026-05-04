from fastapi import APIRouter, Query
from server.app.services.update_service import UpdateService

router = APIRouter()
update_service = UpdateService()


@router.get("/updates/check")
async def check_update(
    current_version: str = Query(...),
    platform: str = Query("windows"),
):
    """Проверка обновлений"""
    return await update_service.check_update(current_version, platform)


from fastapi.responses import FileResponse


@router.get("/updates/download/{platform}/{version}")
async def download_update(platform: str, version: str):
    filepath = update_service.builds_dir / f"{platform}_{version}.tar.gz"
    if not filepath.exists():
        return {"error": "Сборка не найдена"}
    return FileResponse(filepath, filename=f"far_{platform}_{version}.tar.gz")

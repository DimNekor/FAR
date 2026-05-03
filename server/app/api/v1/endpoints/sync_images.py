from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import os

from server.app.core.database import get_db
from server.app.services.image_sync_service import ImageSyncService

router = APIRouter()


@router.post("/sync-images/compare")
async def compare_images(client_files: dict):
    """
    Клиент отправляет {имя_файла: "дата_модификации"}.
    Сервер сравнивает и отвечает, кому что нужно.
    """
    service = ImageSyncService()
    result = service.compare(client_files)
    return {"status": "ok", **result}


@router.get("/sync-images/download/{filename}")
async def download_image(filename: str):
    """Клиент скачивает файл с сервера."""
    service = ImageSyncService()
    filepath = service.get_file_path(filename)
    if filepath.exists():
        return FileResponse(filepath, filename=filename)
    return {"error": "File not found"}


@router.post("/sync-images/upload/{filename}")
async def upload_image(filename: str, file: UploadFile = File(...)):
    """Клиент загружает файл на сервер."""
    service = ImageSyncService()
    content = await file.read()
    service.save_uploaded_file(filename, content)
    return {"status": "ok", "filename": filename}

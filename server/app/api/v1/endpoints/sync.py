from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.app.core.database import get_db
from server.app.services.sync_service import SyncService

router = APIRouter()


@router.post("/sync")
async def sync_data(data: dict, db: Session = Depends(get_db)):
    """
    Принимает все данные клиента, сохраняет недостающее,
    отдаёт все данные сервера.
    """
    service = SyncService(db)

    # Сохраняем то, чего нет на сервере
    save_result = await service.save_client_data(data)

    # Получаем все данные сервера для клиента
    server_data = await service.get_all_data()

    return {
        "status": "ok",
        "saved": save_result,
        "server_data": server_data,
    }

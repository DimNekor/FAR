from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.app.models.user import User
from server.app.models.session import Session as SessionModel
from server.app.models.image import ImageResponse


class SyncService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _parse_datetime(value):
        """Преобразует строку в datetime, если нужно."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        # Пробуем разные форматы
        for fmt in [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return datetime.utcnow()

    async def save_client_data(self, data: dict) -> dict:
        saved_users = 0
        saved_sessions = 0
        saved_images = 0

        for user_data in data.get("users", []):
            stmt = select(User).filter(User.id_user == user_data["id_user"])
            result = await self.db.execute(stmt)
            exists = result.scalar_one_or_none()
            if not exists:
                user = User(
                    id_user=user_data["id_user"],
                    name=user_data["name"],
                    sex=user_data["sex"],
                    created_at=self._parse_datetime(user_data.get("created_at")),
                )
                self.db.add(user)
                saved_users += 1

        for session_data in data.get("sessions", []):
            stmt = select(SessionModel).filter(
                SessionModel.id_session == session_data["id_session"]
            )
            result = await self.db.execute(stmt)
            exists = result.scalar_one_or_none()
            if not exists:
                session = SessionModel(
                    id_session=session_data["id_session"],
                    user_id=session_data["user_id"],
                    timing=session_data["timing"],
                    created_at=self._parse_datetime(session_data.get("created_at")),
                )
                self.db.add(session)
                saved_sessions += 1

        for image_data in data.get("images", []):
            stmt = select(ImageResponse).filter(
                ImageResponse.id_image == image_data["id_image"]
            )
            result = await self.db.execute(stmt)
            exists = result.scalar_one_or_none()
            if not exists:
                image = ImageResponse(
                    id_image=image_data["id_image"],
                    session_id=image_data["session_id"],
                    image_name=image_data["image_name"],
                    reaction_time=image_data["reaction_time"],
                    true_class=image_data["true_class"],
                    predicted_class=image_data["predicted_class"],
                    created_at=self._parse_datetime(image_data.get("created_at")),
                )
                self.db.add(image)
                saved_images += 1

        await self.db.commit()

        return {
            "saved_users": saved_users,
            "saved_sessions": saved_sessions,
            "saved_images": saved_images,
        }

    async def get_all_data(self) -> dict:
        users_result = await self.db.execute(select(User))
        users = users_result.scalars().all()

        sessions_result = await self.db.execute(select(SessionModel))
        sessions = sessions_result.scalars().all()

        images_result = await self.db.execute(select(ImageResponse))
        images = images_result.scalars().all()

        return {
            "users": [
                {
                    "id_user": u.id_user,
                    "name": u.name,
                    "sex": u.sex,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in users
            ],
            "sessions": [
                {
                    "id_session": s.id_session,
                    "user_id": s.user_id,
                    "timing": s.timing,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in sessions
            ],
            "images": [
                {
                    "id_image": i.id_image,
                    "session_id": i.session_id,
                    "image_name": i.image_name,
                    "reaction_time": i.reaction_time,
                    "true_class": i.true_class,
                    "predicted_class": i.predicted_class,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                }
                for i in images
            ],
        }

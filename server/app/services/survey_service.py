import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.session import Session as SessionModel
from app.models.image import ImageResponse


class SurveyService:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, name: str, sex: str) -> str:
        user = User(name=name, sex=sex)
        self.db.add(user)
        self.db.commit()
        return user.id_user

    def create_session(self, user_id: str, timing: str) -> str:
        session = SessionModel(user_id=user_id, timing=timing)
        self.db.add(session)
        self.db.commit()
        return session.id_session

    def add_image_response(
        self,
        session_id: str,
        image_name: str,
        reaction_time: float,
        true_class: int,
        predicted_class: int,
    ) -> str:
        image = ImageResponse(
            session_id=session_id,
            image_name=image_name,
            reaction_time=reaction_time,
            true_class=true_class,
            predicted_class=predicted_class,
        )
        self.db.add(image)
        self.db.commit()
        return image.id_image

    def get_all_results(self):
        """Все результаты с JOIN трёх таблиц"""
        return (
            self.db.query(
                User.id_user,
                User.name.label("participant_name"),
                User.sex,
                User.created_at.label("registration_date"),
                SessionModel.id_session,
                SessionModel.timing,
                ImageResponse.id_image,
                ImageResponse.image_name,
                ImageResponse.reaction_time,
                ImageResponse.true_class,
                ImageResponse.predicted_class,
            )
            .join(SessionModel, User.id_user == SessionModel.user_id)
            .join(ImageResponse, SessionModel.id_session == ImageResponse.session_id)
            .all()
        )

    def get_statistics(self):
        """Статистика по сессиям"""
        return (
            self.db.query(
                User.id_user,
                User.name,
                User.sex,
                SessionModel.timing,
                func.count(ImageResponse.id_image).label("total_images"),
                func.sum(
                    func.case(
                        (ImageResponse.true_class == ImageResponse.predicted_class, 1),
                        else_=0,
                    )
                ).label("correct_answers"),
                func.avg(ImageResponse.reaction_time).label("avg_reaction_time"),
                func.sum(
                    func.case(
                        (ImageResponse.predicted_class == -1, 1),
                        else_=0,
                    )
                ).label("timeouts"),
            )
            .join(SessionModel, User.id_user == SessionModel.user_id)
            .join(ImageResponse, SessionModel.id_session == ImageResponse.session_id)
            .group_by(User.id_user, SessionModel.id_session)
            .all()
        )

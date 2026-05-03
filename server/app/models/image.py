import uuid
from datetime import datetime

from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from server.app.core.database import Base


class ImageResponse(Base):
    __tablename__ = "images"

    id_image: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id_session", ondelete="CASCADE"),
        nullable=False,
    )
    image_name: Mapped[str] = mapped_column(String(255), nullable=False)
    reaction_time: Mapped[float] = mapped_column(Float, nullable=False)
    true_class: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_class: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Связь
    session: Mapped["Session"] = relationship(back_populates="images")

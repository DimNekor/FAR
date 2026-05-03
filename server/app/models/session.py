import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from server.app.core.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id_session: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id_user", ondelete="CASCADE"), nullable=False
    )
    timing: Mapped[str] = mapped_column(String(10), nullable=False)

    # Связи
    user: Mapped["User"] = relationship(back_populates="sessions")
    images: Mapped[list["ImageResponse"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

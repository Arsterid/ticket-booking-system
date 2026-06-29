from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.core.infra.database.orm import AbstractORMModel


class ViewLog(AbstractORMModel):
    object_type: Mapped[str] = mapped_column(String(255))
    object_id: Mapped[int] = mapped_column(Integer())

    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True,
                                                   index=True)

    __table_args__ = (
        UniqueConstraint("object_type", "object_id", "user_id", name="uq_view_logs_object_user"),
    )

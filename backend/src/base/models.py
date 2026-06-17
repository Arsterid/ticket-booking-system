from datetime import datetime

from sqlalchemy import Integer, func
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase


class BaseModel(DeclarativeBase):
    __abstract__ = True


class AbstractModel(BaseModel):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

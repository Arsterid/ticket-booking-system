from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import select, func, inspect


class SQLFunction(ABC):
    @abstractmethod
    def resolve(self, current_model: Any) -> Any:
        pass


class Count(SQLFunction):
    def __init__(self, relationship: Any):
        self.relationship = relationship

    def resolve(self, current_model: Any) -> Any:
        prop = inspect(self.relationship).property
        target_model = prop.mapper.class_
        return (
            select(func.count())
            .select_from(target_model)
            .where(prop.primaryjoin)
            .correlate(current_model)
            .scalar_subquery()
        )

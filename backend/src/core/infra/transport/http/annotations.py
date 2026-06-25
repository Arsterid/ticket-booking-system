from __future__ import annotations

from typing import TypeVar, Annotated

from fastapi.params import Path
from pydantic import BaseModel as PydanticBaseModel

from src.core.infra.database.constants import DB_INT_MAX

PYDANTIC_MODEL_T = TypeVar("PYDANTIC_MODEL_T", bound=PydanticBaseModel)
Int32Path = Annotated[int, Path(..., ge=1, le=DB_INT_MAX)]

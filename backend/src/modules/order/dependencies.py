from typing import Annotated

from fastapi import Depends

from src.core.infra.database.uow_factory import get_uow_factory
from .schemas import OrderFilterParamsSchema, OrderItemFilterParamsSchema
from .services import OrderService

OrderServiceDep = Annotated[OrderService, Depends(get_uow_factory(OrderService))]

OrderFilterParamsSchemaDep = Annotated[OrderFilterParamsSchema, Depends(OrderFilterParamsSchema)]
OrderItemFilterParamsSchemaDep = Annotated[OrderItemFilterParamsSchema, Depends(OrderItemFilterParamsSchema)]

from typing import Annotated

from fastapi import Depends

from src.core.infra.database.uow_factory import get_uow_factory
from src.modules.orders.services import OrderService

OrderServiceDep = Annotated[OrderService, Depends(get_uow_factory(OrderService))]

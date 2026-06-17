from typing import Type, Callable

from src.base.annotations import S, U


class UoWServiceFactory:
    def __init__(
        self,
        service_cls: Type[S],
        uow_factory: Callable[[], U]
    ):
        self.service_cls = service_cls
        self.uow_factory = uow_factory

    async def __call__(self) -> S:
        uow = self.uow_factory()
        return self.service_cls(uow=uow)

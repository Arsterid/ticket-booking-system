from typing import Generic

from src.base.annotations import U


class GenericService(Generic[U]):
    def __init__(self, uow: U):
        self.uow = uow

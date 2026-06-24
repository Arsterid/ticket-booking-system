from typing import Protocol


class AbstractModelProtocol(Protocol):
    id: int
    __tablename__: str

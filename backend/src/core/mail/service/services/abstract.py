from abc import ABC, abstractmethod
from typing import Optional, Any


class BaseEmailService(ABC):
    @abstractmethod
    async def send(
        self,
        to_email: str,
        subject: str,
        body: str,
        template_name: Optional[str] = None,
        lang: Optional[str] = None,
        context: Optional[dict[str, Any]] = None
    ) -> None:
        pass

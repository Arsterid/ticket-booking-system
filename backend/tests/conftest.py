from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport

from src.app import app
from src.common.orm.models import AbstractModel
from src.core.database import engine
from src.core.security.jwt_tokens import JWTManager
from src.core.settings import settings
from src.core.uow import AppUnitOfWork, create_sqlalchemy_uow

from src.modules.event.repositories import EventCategoryRepository

jwt_manager = JWTManager(
    secret_key=settings.jwt_secret_key,
    algorithm=settings.jwt_algorithm,
    expire_seconds=settings.jwt_expires_in,
)


@pytest.fixture(autouse=True)
async def clean_db():
    async with engine.begin() as conn:
        for table in reversed(AbstractModel.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
def get_auth_headers():
    def _get_headers(user_id: int, role: str) -> dict:
        token = jwt_manager.create_access_token(
            data={"sub": str(user_id), "role": role}
        )
        return {"Authorization": f"Bearer {token}"}
    return _get_headers


@pytest.fixture
def setup_uow() -> AppUnitOfWork:
    test_uow = create_sqlalchemy_uow()
    app.dependency_overrides[create_sqlalchemy_uow] = lambda: test_uow
    yield test_uow
    app.dependency_overrides.clear()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api/v1") as ac:
        yield ac

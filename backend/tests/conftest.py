import pytest
from httpx import AsyncClient, ASGITransport
from taskiq import InMemoryBroker

from src.app import app
from src.common.dependencies import get_password_manager
from src.common.orm.models import AbstractModel
from src.core.database import engine
from src.core.security.jwt_tokens import JWTManager
from src.core.settings import settings
from src.core.tiq import broker
from src.core.uow import create_sqlalchemy_uow


from src.modules.user import tasks
from src.modules.ticket import tasks


jwt_manager = JWTManager(
    secret_key=settings.jwt_secret_key,
    algorithm=settings.jwt_algorithm,
    expire_seconds=settings.jwt_expires_in,
)


@pytest.fixture(autouse=True)
def setup_taskiq():
    if isinstance(broker, InMemoryBroker):
        broker.await_inplace = True
    yield
    if isinstance(broker, InMemoryBroker):
        broker.await_inplace = False
        broker.dependency_overrides.clear()


@pytest.fixture(autouse=True)
async def clean_db():
    async with engine.begin() as conn:
        for table in reversed(AbstractModel.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture(scope="session")
def get_auth_headers():
    def _get_headers(user_id, role):
        token = jwt_manager.create_access_token(
            data={"sub": str(user_id), "role": role}
        )
        return {"Authorization": f"Bearer {token}"}

    return _get_headers


@pytest.fixture
def setup_uow():
    test_uow = create_sqlalchemy_uow()
    app.dependency_overrides[create_sqlalchemy_uow] = lambda: test_uow
    if isinstance(broker, InMemoryBroker):
        broker.dependency_overrides[create_sqlalchemy_uow] = lambda: test_uow
    yield test_uow
    app.dependency_overrides.clear()
    if isinstance(broker, InMemoryBroker):
        broker.dependency_overrides.clear()


@pytest.fixture(scope="session")
def pwd_manager():
    return get_password_manager(settings)


@pytest.fixture(scope="session")
def api_transport():
    return ASGITransport(app=app)


@pytest.fixture
async def client(api_transport):
    async with AsyncClient(transport=api_transport, base_url="http://test/api/v1") as ac:
        yield ac


@pytest.fixture
def create_model_factory():
    async def _create(uow, repo_attr, **kwargs):
        repo = getattr(uow, repo_attr)
        obj = await repo.create(**kwargs)
        await uow.session.flush()
        return obj

    return _create

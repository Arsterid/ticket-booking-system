import importlib
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from taskiq import InMemoryBroker

from src.core.settings import get_settings, AppConfig
from src.core.infra.tasks.config import broker
from src.app.uow import create_app_uow
from src.core.infra.transport.http.dependencies import get_jwt_manager, get_password_manager
from src.core.infra.cache.factory import get_cache_manager
from src.core.infra.database.orm.base import AbstractORMModel
from src.core.database import db_factory
from src.core.security import JWTManager

BASE_DIR = Path(__file__).parent.parent
SRC_DIR = BASE_DIR / "src"


def import_all_tasks() -> None:
    modules_dir = SRC_DIR / "modules"

    for tasks_file in modules_dir.glob("**/tasks.py"):
        relative_path = tasks_file.relative_to(BASE_DIR)
        module_name = ".".join(relative_path.with_suffix("").parts)
        importlib.import_module(module_name)


import_all_tasks()

test_config = AppConfig(
    testing=True,
    jwt_secret_key="test_secret_key_for_jwt_token_validation_32_chars",
    metrics_token="test_metrics_token_for_prometheus_monitoring"
)

jwt_manager = JWTManager(
    secret_key=test_config.jwt_secret_key,
    algorithm=test_config.jwt_algorithm,
    expire_seconds=test_config.jwt_expires_in,
)

shared_test_cache = get_cache_manager()
get_cache_manager._instance = shared_test_cache


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
    await shared_test_cache.clear()

    engine = db_factory.get_engine()
    async with engine.begin() as conn:
        for table in reversed(AbstractORMModel.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture(scope="session")
def get_auth_headers():
    def _get_headers(user_id, role):
        token = jwt_manager.create_access_token(data={"sub": str(user_id), "role": role})
        return {"Authorization": f"Bearer {token}"}

    return _get_headers


@pytest.fixture(autouse=True)
def setup_global_overrides():
    from src.app.main import app

    app.dependency_overrides[get_settings] = lambda: test_config
    app.dependency_overrides[get_cache_manager] = lambda: shared_test_cache
    app.dependency_overrides[get_jwt_manager] = lambda: jwt_manager
    app.dependency_overrides[get_password_manager] = lambda: get_password_manager(test_config)

    yield

    app.dependency_overrides.clear()


@pytest.fixture
def setup_uow(setup_global_overrides):
    from src.app.main import app
    test_uow = create_app_uow()

    app.dependency_overrides[create_app_uow] = lambda: test_uow
    if isinstance(broker, InMemoryBroker):
        broker.dependency_overrides[create_app_uow] = lambda: test_uow

    yield test_uow

    app.dependency_overrides[get_settings] = lambda: test_config
    app.dependency_overrides[get_cache_manager] = lambda: shared_test_cache
    app.dependency_overrides[get_jwt_manager] = lambda: jwt_manager
    app.dependency_overrides[get_password_manager] = lambda: get_password_manager(test_config)


@pytest.fixture(scope="session")
def pwd_manager():
    return get_password_manager(test_config)


@pytest.fixture(scope="session")
def api_transport():
    from src.app.main import app
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
        await uow.flush()
        return obj

    return _create


@pytest.fixture
async def api_client(client, request, get_auth_headers):
    user_role = getattr(request.cls, "user_role", None) or getattr(request.function, "user_role", None)
    user_id = getattr(request.cls, "user_id", 1)

    if user_role:
        headers = get_auth_headers(user_id=user_id, role=user_role)
        client.headers.update(headers)
    else:
        client.headers.pop("Authorization", None)

    return client


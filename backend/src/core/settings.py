from typing import Optional

from pydantic import RedisDsn
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    branch: str = "development"

    db_user: str = "user"
    db_password: Optional[str] = None
    db_name: str = "database"
    db_host: str = "localhost"
    db_port: str = "5432"
    db_driver: str = "asyncpg"
    db: str = "postgresql"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_user: Optional[str] = None
    redis_password: Optional[str] = None
    redis_db: int = 0

    jwt_secret_key: str = "<KEY>"
    jwt_algorithm: str = "HS256"
    jwt_expires_in: int = 3600

    password_algorithm: str = "sha256"
    password_iterations: int = 600000

    @property
    def redis_url(self) -> str:
        dsn = RedisDsn.build(
            scheme="redis",
            username=self.redis_user,
            password=self.redis_password,
            host=self.redis_host,
            port=self.redis_port,
            path=f"/{self.redis_db}"
        )
        return str(dsn)

    @property
    def db_url(self) -> str:
        auth = f"{self.db_user}"
        if self.db_password:
            auth += f":{self.db_password}"

        return (f"{self.db}+{self.db_driver}://{auth}@"
                f"{self.db_host}:{self.db_port}/{self.db_name}")


settings = AppConfig()

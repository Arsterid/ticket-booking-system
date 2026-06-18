from typing import Optional

from pydantic import RedisDsn
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    db_user: str = "user"
    db_password: Optional[str] = None
    db_name: str = "database"
    db_host: str = "localhost"
    db_port: str = "5432"
    db_driver: str = "asyncpg"
    db: str = "postgresql"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_user: str = "user"
    redis_password: Optional[str] = None
    redis_db: str = 0

    jwt_secret_key: str = "<KEY>"
    jwt_algorithm: str = "HS256"
    jwt_expires_in: int = 3600

    password_algorithm: str = "HS256"
    password_iterations: int = 600000

    @property
    def redis_url(self) -> str:
        dsn = RedisDsn.build(
            scheme="redis",
            username=self.REDIS_USER,
            password=self.REDIS_PASSWORD,
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            path=f"{self.REDIS_DB}"
        )
        return str(dsn)

    @property
    def db_url(self) -> str:
        return (f"{self.db}+{self.db_driver}://{self.db_user}:{self.db_password}@"
                f"{self.db_host}:{self.db_port}/{self.db_name}")


settings = AppConfig()

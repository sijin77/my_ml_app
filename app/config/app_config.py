from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional
import yaml
from pathlib import Path


class DatabaseConfig(BaseSettings):
    host: str = Field("localhost", env="POSTGRES_HOST")
    port: int = 5432
    name: str = "myapp"
    user: str = "user"
    password: str = Field(..., env="POSTGRES_PASSWORD")

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RabbitMQConfig(BaseSettings):
    host: str = Field("localhost", env="RABBITMQ_HOST")
    port: int = 5672
    user: str = "user"
    password: str = Field(..., env="RABBITMQ_DEFAULT_PASS")


class AppConfig(BaseSettings):
    db: DatabaseConfig = DatabaseConfig()
    rabbit: RabbitMQConfig = RabbitMQConfig()
    debug: bool = False
    feature_flags: dict = {}

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @classmethod
    def from_yaml(cls, path: str = "config/settings.yaml"):
        yaml_data = yaml.safe_load(Path(path).read_text())
        return cls.parse_obj(yaml_data)


# Глобальный экземпляр конфига
settings = AppConfig.from_yaml()

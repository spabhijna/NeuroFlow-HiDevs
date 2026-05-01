from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # App
    app_name: str = "NeuroFlow"
    environment: str = "development"

    # Postgres
    postgres_user: str = Field(..., env="POSTGRES_USER")
    postgres_password: str = Field(..., env="POSTGRES_PASSWORD")
    postgres_host: str = Field("postgres", env="POSTGRES_HOST")
    postgres_port: int = Field(5432, env="POSTGRES_PORT")
    postgres_db: str = Field("neuroflow", env="POSTGRES_DB")

    # Redis
    redis_host: str = Field("redis", env="REDIS_HOST")
    redis_port: int = Field(6379, env="REDIS_PORT")
    redis_password: str = Field(..., env="REDIS_PASSWORD")

    # MLflow
    mlflow_host: str = Field("mlflow", env="MLFLOW_HOST")
    mlflow_port: int = Field(5000, env="MLFLOW_PORT")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return (
            f"redis://:{self.redis_password}"
            f"@{self.redis_host}:{self.redis_port}/0"
        )

    @property
    def mlflow_url(self) -> str:
        return f"http://{self.mlflow_host}:{self.mlflow_port}"


settings = Settings()
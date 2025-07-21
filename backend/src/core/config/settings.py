""" SETTINGS & CONSTANTS FILE """

from pydantic_settings import BaseSettings

from src.core.config.constants import ROOT_PATH



# Env vars
class Settings(BaseSettings):
    database_name: str
    database_user: str
    database_password: str
    database_host: str
    database_port: str
    environment: str
    url_domain: str
    secret_key: str
    hash_algorithm: str
    access_token_expire_minutes: int
    gemini_api_key: str
    gemini_model: str

    @property
    def url_db(self) -> str:
        return f"mysql+asyncmy://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"

    @property
    def url_db_sync(self) -> str:
        return f"mysql+pymysql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"

    class Config:
        extra = "allow"
        env_file = f"{ROOT_PATH}/.env"

env_vars = Settings()


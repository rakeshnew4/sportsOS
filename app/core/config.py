from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_backend: Literal["local_json", "firestore"] = "local_json"
    local_data_path: str = "./local_data/store.json"

    google_application_credentials: str = "./firebase_serviceaccount.json"
    firestore_project_id: str | None = None
    firestore_emulator_host: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()

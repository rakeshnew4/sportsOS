from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_backend: Literal["local_json", "firestore", "postgresql"] = "postgresql"
    database_url: str = "postgresql://sportsdb:sportsdb_pass@localhost:5432/sportsdb"

    # Legacy JSON / Firestore fields kept for backwards-compat (ignored when
    # data_backend == "postgresql").
    local_data_path: str = "./local_data/store.json"
    google_application_credentials: str = "./firebase_serviceaccount.json"
    firestore_project_id: str | None = None
    firestore_emulator_host: str | None = None

    cors_allow_origins: str = "http://localhost:3000"

    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

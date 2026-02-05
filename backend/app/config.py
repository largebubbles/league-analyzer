from pathlib import Path

from pydantic_settings import BaseSettings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    riot_api_key: str
    riot_platform: str = "na1"
    riot_region: str = "americas"
    cache_ttl_seconds: int = 300  # 5 min for summoner data
    match_cache_ttl_seconds: int = 86400  # 24h (match data is immutable)
    rate_limit_per_second: int = 20
    rate_limit_per_2min: int = 100
    sqlite_db_path: str = "cache.db"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = {"env_file": str(_PROJECT_ROOT / ".env")}


settings = Settings()

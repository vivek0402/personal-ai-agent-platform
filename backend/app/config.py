from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = ""
    supabase_url: str = ""
    supabase_key: str = ""          # service-role key (server-side only)
    supabase_anon_key: str = ""
    allowed_origins: str = "http://localhost:3000"
    frontend_url: str = ""      # set to Vercel production URL in Render env vars
    environment: str = "development"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        origins = [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url.rstrip("/"))
        return origins


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

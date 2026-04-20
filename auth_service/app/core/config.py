from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "auth-service"
    env: str = "local"

    jwt_secret: str = "change_me_super_secret"
    jwt_alg: str = "HS256"
    access_token_expire_minutes: int = 60

    sqlite_path: str = "./auth.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def database_url(self) -> str:
        if self.sqlite_path.startswith("sqlite"):
            return self.sqlite_path
        return f"sqlite+aiosqlite:///{self.sqlite_path}"


settings = Settings()
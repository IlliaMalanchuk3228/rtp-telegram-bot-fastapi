from pydantic import BaseSettings


class Settings(BaseSettings):
    TELEGRAM_TOKEN: str
    WEBHOOK_URL: str

    # DigitalOcean Spaces (S3) details:
    SPACES_KEY: str
    SPACES_SECRET: str
    SPACES_REGION: str
    SPACES_NAME: str

    class Config:
        env_file = ".env"

    @property
    def cdn_base(self) -> str:
        # dynamically derive the CDN hostname
        return f"https://{self.SPACES_NAME}.{self.SPACES_REGION}.cdn.digitaloceanspaces.com"


settings = Settings()

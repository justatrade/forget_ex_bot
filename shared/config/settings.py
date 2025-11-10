from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class TelegramSettings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_id: int = Field(..., alias="ADMIN_ID")

    # class Config:
    #     env_prefix = ""


class ChannelSettings(BaseSettings):
    channel_id_prod: int = Field(..., alias="CHANNEL_ID_PROD")
    channel_id_test: int = Field(..., alias="CHANNEL_ID_TEST")

    # class Config:
    #     env_prefix = ""

    def get_channel_id(self, debug: bool) -> int:
        return self.channel_id_test if debug else self.channel_id_prod


class DatabaseSettings(BaseSettings):
    db_host: str = Field("127.0.0.1", alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")
    postgres_db: str = Field(..., alias="POSTGRES_DB")
    postgres_user: str = Field(..., alias="POSTGRES_USER")
    postgres_password: str = Field(..., alias="POSTGRES_PASSWORD")

    # class Config:
    #     env_prefix = ""

    @property
    def url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.db_host}:"
            f"{self.db_port}/{self.postgres_db}"
        )


class ProdamusSettings(BaseSettings):
    api_key: str
    secret: str
    endpoint: str

    class Config:
        env_prefix = ""


class PriceSettings(BaseSettings):
    basic: int
    premium: int

    class Config:
        env_prefix = ""


class PromoSettings(BaseSettings):
    code_main: str
    discount_percent: int

    class Config:
        env_prefix = ""


class AppSettings(BaseSettings):
    debug: bool = False
    webhook_url: str
    success_url: str
    log_level: str = "INFO"

    class Config:
        env_prefix = ""


class Settings:
    telegram: TelegramSettings = TelegramSettings()
    channel: ChannelSettings = ChannelSettings()
    database: DatabaseSettings = DatabaseSettings()
    prodamus: ProdamusSettings = ProdamusSettings()
    price: PriceSettings = PriceSettings()
    promo: PromoSettings = PromoSettings()
    app: AppSettings = AppSettings()


settings = Settings()
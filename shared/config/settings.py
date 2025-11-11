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


class RedisSettings(BaseSettings):
    host: str = Field("redis", alias="REDIS_HOST")
    port: int = Field(6379, alias="REDIS_PORT")
    db: int = Field(0, alias="REDIS_DB")

    # class Config:
    #     env_prefix = ""


class ProdamusSettings(BaseSettings):
    api_key: str = Field(..., alias="PRODAMUS_API_KEY")
    secret: str = Field(..., alias="PRODAMUS_SECRET")
    endpoint: str = Field(..., alias="PRODAMUS_ENDPOINT")

    # class Config:
    #     env_prefix = ""


class PriceSettings(BaseSettings):
    basic: int = Field(..., alias="PRICE_BASIC")
    premium: int = Field(..., alias="PRICE_PREMIUM")

    # class Config:
    #     env_prefix = ""


class PromoSettings(BaseSettings):
    code_main: str = Field(..., alias="PROMO_CODE_MAIN")
    discount_percent: int = Field(..., alias="PROMO_DISCOUNT_PERCENT")

    # class Config:
    #     env_prefix = ""


class AppSettings(BaseSettings):
    debug: bool = Field(False, alias="DEBUG")
    webhook_url: str = Field(..., alias="WEBHOOK_URL")
    success_url: str = Field(..., alias="SUCCESS_URL")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    # class Config:
    #     env_prefix = ""


class Settings:
    telegram: TelegramSettings = TelegramSettings()
    channel: ChannelSettings = ChannelSettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    prodamus: ProdamusSettings = ProdamusSettings()
    price: PriceSettings = PriceSettings()
    promo: PromoSettings = PromoSettings()
    app: AppSettings = AppSettings()


settings = Settings()
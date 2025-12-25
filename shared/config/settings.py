from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


load_dotenv()


class TelegramSettings(BaseSettings):
    bot_token: str = Field(..., alias="BOT_TOKEN")
    admin_id: int|str|list[int] = Field(..., alias="ADMIN_ID")
    mara_channel: str = Field(..., alias="MARA_CHANNEL_ID")
    dasha_channel: str = Field(..., alias="DASHA_CHANNEL_ID")
    sell_mode: str = Field(..., alias="BOT_SELL_MODE")

    @field_validator("admin_id", mode="before")
    @classmethod
    def convert_to_list(cls, value):
        if isinstance(value, str):
            return [int(v) for v in value.split(",")]
        return [value]


class ChannelSettings(BaseSettings):
    channel_id_prod: int = Field(..., alias="CHANNEL_ID_PROD")
    channel_id_test: int = Field(..., alias="CHANNEL_ID_TEST")

    def get_channel_id(self, debug: bool) -> int:
        return self.channel_id_test if debug else self.channel_id_prod


class DatabaseSettings(BaseSettings):
    db_host: str = Field("127.0.0.1", alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")
    postgres_db: str = Field(..., alias="POSTGRES_DB")
    postgres_user: str = Field(..., alias="POSTGRES_USER")
    postgres_password: str = Field(..., alias="POSTGRES_PASSWORD")

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
    password: str = Field(..., alias="REDIS_PASSWORD")
    db: int = Field(0, alias="REDIS_DB")
    stream_name: str = Field("payments_stream", alias="REDIS_STREAM_NAME")
    group_name: str = Field("bot_group", alias="REDIS_GROUP_NAME")
    consumer_name: str = Field("bot_consumer", alias="REDIS_CONSUMER_NAME")
    block_ms: int = Field(5000, alias="REDIS_BLOCK_MS")
    read_count: int = Field(10, alias="REDIS_READ_COUNT")
    claim_min_idle: int = Field(60000, alias="REDIS_CLAIM_MIN_IDLE")
    claim_batch: int = Field(10, alias="REDIS_CLAIM_BATCH")
    max_retries: int = Field(5, alias="REDIS_MAX_RETRIES")
    retry_backoff_base_sec: int = Field(2, alias="REDIS_RETRY_BACKOFF_BASE_SEC")
    dlq_stream: str = Field("payments_stream_dlq", alias="REDIS_DLQ_STREAM")
    idempotency_ttl_days: int = Field(7, alias="REDIS_IDEMPOTENCY_TTL_DAYS")


class ProdamusSettings(BaseSettings):
    demo_secret: str = Field(..., alias="PRODAMUS_DEMO_SECRET")
    secret: str = Field(..., alias="PRODAMUS_SECRET")
    endpoint: str = Field(..., alias="PRODAMUS_ENDPOINT")
    var_prefix: str = Field(..., alias="PRODAMUS_VAR_PREFIX")

    def get_secret(self, debug: bool) -> str:
        return self.demo_secret if debug else self.secret


class PriceSettings(BaseSettings):
    basic: int = Field(..., alias="PRICE_BASIC")
    premium: int = Field(..., alias="PRICE_PREMIUM")


class AppSettings(BaseSettings):
    secret_hash: str = Field(..., alias="SECRET_HASH")
    debug: bool = Field(False, alias="DEBUG")
    webhook_url: str = Field(..., alias="WEBHOOK_URL")
    success_url: str = Field(..., alias="SUCCESS_URL")
    log_level: str = Field("INFO", alias="LOG_LEVEL")


class SpecialSettings(BaseSettings):
    common_price: int = Field(..., alias="SPECIAL_COMMON_PRICE")
    twelve_price: int = Field(..., alias="SPECIAL_TWELVE_PRICE")
    all_price: int = Field(..., alias="SPECIAL_ALL_PRICE")
    description_feb: str = Field(..., alias="SPECIAL_DESCRIPTION_FEB")
    description_ny: str = Field(..., alias="SPECIAL_DESCRIPTION_NY")
    description_12: str = Field(..., alias="SPECIAL_DESCRIPTION_12")
    description_all: str = Field(..., alias="SPECIAL_DESCRIPTION_ALL")
    channel_feb: str = Field(..., alias="SPECIAL_CHANNEL_FEB")
    channel_ny: str = Field(..., alias="SPECIAL_CHANNEL_NY")
    channel_12: str = Field(..., alias="SPECIAL_CHANNEL_12")


class RobokassaSettings(BaseSettings):
    payment_url: str = Field(..., alias="ROBOKASSA_PAYMENT_URL")
    merchant_login: str = Field(..., alias="ROBOKASSA_MERCHANT_LOGIN")
    prod_password_1: str = Field(..., alias="ROBOKASSA_PASSWORD_1")
    prod_password_2: str = Field(..., alias="ROBOKASSA_PASSWORD_2")
    test_password_1: str = Field(..., alias="ROBOKASSA_TEST_PASSWORD_1")
    test_password_2: str = Field(..., alias="ROBOKASSA_TEST_PASSWORD_2")
    receipt: bool = Field(False, alias="ROBOKASSA_CREATE_RECEIPT")
    is_test: int = Field(..., alias="ROBOKASSA_IS_TEST")

    @property
    def password_1(self) -> str:
        return self.test_password_1 if self.is_test else self.prod_password_1

    @property
    def password_2(self) -> str:
        return self.test_password_2 if self.is_test else self.prod_password_2


class Settings:
    telegram: TelegramSettings = TelegramSettings()
    channel: ChannelSettings = ChannelSettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    prodamus: ProdamusSettings = ProdamusSettings()
    price: PriceSettings = PriceSettings()
    app: AppSettings = AppSettings()
    special: SpecialSettings = SpecialSettings()
    rk: RobokassaSettings = RobokassaSettings()

settings = Settings()

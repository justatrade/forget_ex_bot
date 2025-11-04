from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
    AsyncEngine,
    AsyncSession,
)

from shared.config.settings import settings
from shared.config.logger import setup_logger


logger = setup_logger(__name__)


class DatabaseConnection:
    _engine: AsyncEngine = None
    _session_factory: async_sessionmaker = None

    @classmethod
    def get_engine(cls) -> AsyncEngine:
        if cls._engine is None:
            cls._engine = create_async_engine(
                settings.database.url,
                echo=settings.app.debug,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20
            )
            logger.info("Database engine created")
        return cls._engine

    @classmethod
    def get_session_factory(cls) -> async_sessionmaker:
        if cls._session_factory is None:
            cls._session_factory = async_sessionmaker(
                bind=cls.get_engine(),
                class_=AsyncSession,
                expire_on_commit=False
            )
            logger.info("Session factory created")
        return cls._session_factory

    @classmethod
    async def create_tables(cls):
        from shared.database.models import BaseModel

        engine = cls.get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(BaseModel.metadata.create_all)
        logger.info("Database tables created")

    @classmethod
    async def close(cls):
        if cls._engine:
            await cls._engine.dispose()
            logger.info("Database connection closed")

    @classmethod
    @asynccontextmanager
    async def get_session(cls) -> AsyncSession:
        session_factory = cls.get_session_factory()
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

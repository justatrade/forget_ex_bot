from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.config import setup_logger
from shared.database.connection import DatabaseConnection


logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("API starting...")
    await DatabaseConnection.create_tables()
    logger.info("API started successfully")
    yield
    logger.info("API shutting down...")
    await DatabaseConnection.close()
    logger.info("API stopped")

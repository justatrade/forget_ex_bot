import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from shared.config.settings import settings


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.app.log_level))

    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    file_handler = TimedRotatingFileHandler(
        filename="logs/bot.log",
        when='midnight',
        interval=1,
        backupCount=0,
        encoding="utf-8"
    )
    file_handler.suffix = "%Y-%m-%d"

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if settings.app.debug:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
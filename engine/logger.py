import logging
import os
from logging.handlers import TimedRotatingFileHandler

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

_setup_done = False


def _reset_setup() -> None:
    global _setup_done
    _setup_done = False
    logger = logging.getLogger("autokeymouse")
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)


def setup_logging(level: int = logging.INFO) -> None:
    global _setup_done
    if _setup_done:
        return
    _setup_done = True

    os.makedirs(LOGS_DIR, exist_ok=True)

    logger = logging.getLogger("autokeymouse")
    logger.setLevel(level)

    log_file = os.path.join(LOGS_DIR, "autokeymouse.log")
    handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    handler.suffix = "%Y-%m-%d"
    handler.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"autokeymouse.{name}")
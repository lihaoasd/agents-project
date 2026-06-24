"""后端日志配置。

只记录业务相关日志，第三方库（watchfiles / uvicorn / httpx 等）的日志默认不输出。
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
LOG_DIR = BACKEND_DIR / "logs"
LOG_FILE = LOG_DIR / "app.log"

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def setup_logging(level: str = "INFO") -> None:
    """配置控制台和文件双输出日志。

    只记录业务相关日志，第三方库日志默认不输出。
    """

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    if getattr(root_logger, "_cultural_travel_logging_configured", False):
        return

    # 根日志器只记录 WARN 及以上，屏蔽第三方库的 INFO/DEBUG 日志
    root_logger.setLevel(getattr(logging, level.upper(), logging.WARN))
    root_logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger._cultural_travel_logging_configured = True  # type: ignore[attr-defined]

    # 屏蔽第三方库的 INFO 及以下日志
    for noisy_logger in ("watchfiles", "httpx", "uvicorn", "uvicorn.access", "httpx._client", "openai._base_client", "openai"):
        logging.getLogger(noisy_logger).setLevel(logging.WARN)


def get_logger(name: str) -> logging.Logger:
    """获取项目日志器。

    业务日志器显式设为 DEBUG，确保在根日志器为 WARN 的情况下仍能输出。
    """

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    return logger
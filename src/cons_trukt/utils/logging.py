"""Logging helpers with Loguru when available and stdlib fallback otherwise."""

from __future__ import annotations

import logging
import sys
from typing import Any


class _StdLoggerAdapter:
    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)

    def info(self, message: str, **context: Any) -> None:
        self._log(logging.INFO, message, context)

    def debug(self, message: str, **context: Any) -> None:
        self._log(logging.DEBUG, message, context)

    def warning(self, message: str, **context: Any) -> None:
        self._log(logging.WARNING, message, context)

    def error(self, message: str, **context: Any) -> None:
        self._log(logging.ERROR, message, context)

    def _log(self, level: int, message: str, context: dict[str, Any]) -> None:
        if context:
            suffix = " ".join(f"{key}={value!r}" for key, value in sorted(context.items()))
            self._logger.log(level, "%s %s", message, suffix)
        else:
            self._logger.log(level, "%s", message)


def configure_logging(level: str = "INFO", structured: bool = True) -> None:
    """Configure process logging without making Loguru a module-load dependency."""
    try:
        from loguru import logger
    except ImportError:
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        return

    logger.remove()
    if structured:
        logger.add(
            sink=lambda message: sys.stdout.write(str(message)),
            level=level.upper(),
            serialize=True,
        )
    else:
        logger.add(lambda message: sys.stdout.write(str(message)), level=level.upper())


def get_logger(name: str) -> Any:
    try:
        from loguru import logger
    except ImportError:
        return _StdLoggerAdapter(name)
    return logger.bind(component=name)

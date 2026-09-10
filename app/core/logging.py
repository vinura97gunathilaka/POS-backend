"""
app.core.logging
----------------
Structured logging configuration for Smart POS backend.

Usage:
    from app.core.logging import get_logger

    logger = get_logger(__name__)
    logger.info("Sale created", sale_id=42, branch_id=1)
"""

import logging
import sys
from typing import Optional


# --------------------------------------------------------------------------- #
#  Log level helper                                                            #
# --------------------------------------------------------------------------- #
def _resolve_level(level: str) -> int:
    return getattr(logging, level.upper(), logging.INFO)


# --------------------------------------------------------------------------- #
#  Formatter — human-readable for dev, JSON-friendly for production           #
# --------------------------------------------------------------------------- #
_DEV_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d — %(message)s"
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _build_formatter() -> logging.Formatter:
    return logging.Formatter(fmt=_DEV_FORMAT, datefmt=_DATE_FORMAT)


# --------------------------------------------------------------------------- #
#  Root logger bootstrap (called once on app startup)                         #
# --------------------------------------------------------------------------- #
_bootstrapped = False


def configure_logging(level: str = "INFO") -> None:
    """
    Call once during application startup (e.g., in main.py lifespan event).
    Configures the root logger with a stderr StreamHandler.
    """
    global _bootstrapped
    if _bootstrapped:
        return

    root = logging.getLogger()
    root.setLevel(_resolve_level(level))

    # Remove any default handlers added by uvicorn / FastAPI
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_build_formatter())
    root.addHandler(handler)

    # Silence noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _bootstrapped = True


# --------------------------------------------------------------------------- #
#  Public helper                                                               #
# --------------------------------------------------------------------------- #
def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a named logger.  Always call configure_logging() first.

    Example:
        logger = get_logger(__name__)
        logger.info("Processing sale", extra={"sale_id": 99})
    """
    return logging.getLogger(name or "smartpos")

"""Logging utilities for Gift Voucher Categorizer."""

import sys

from loguru import logger

from src.config import LOG_LEVEL


def setup_logging() -> None:
    """Configure loguru logger for console output."""
    # Remove default handler
    logger.remove()

    # Add console handler with custom format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<level>{message}</level>"
    )
    logger.add(
        sys.stderr,
        format=log_format,
        level=LOG_LEVEL,
        colorize=True,
    )

    logger.info("Logging initialized (console output)")

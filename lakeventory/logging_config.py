"""Logging configuration helpers for inventory CLI."""

import logging


LEVEL_MAP = {
    "error": logging.ERROR,
    "info": logging.INFO,
    "verbose": logging.INFO,
    "debug": logging.DEBUG,
}


def configure_logging(level_name: str = "info") -> int:
    """Configure root logging level from text level.

    Supported values: error, info, verbose, debug
    """
    normalized = (level_name or "info").strip().lower()
    level = LEVEL_MAP.get(normalized, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    return level

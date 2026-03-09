"""Utility functions for safe API calls and iteration."""

import logging
import os
import time
from typing import List

try:
    from tqdm.auto import tqdm
except Exception:
    tqdm = None


logger = logging.getLogger(__name__)


def _progress_enabled() -> bool:
    """Return True when progress bars should be shown."""
    return os.getenv("INVENTORY_PROGRESS", "1") not in {"0", "false", "False", "no", "NO"}


def safe_iter(label: str, iterator, warnings: List[str], batch_size: int, sleep_ms: int):
    """
    Safely iterate over an API result, catching exceptions during iteration.
    
    Args:
        label: Label for logging
        iterator: Iterator to consume
        warnings: List to append warnings to
        batch_size: Number of items per batch before sleeping
        sleep_ms: Sleep time in milliseconds between batches
        
    Yields:
        Items from the iterator
    """
    try:
        count = 0
        iterable = iterator
        if tqdm is not None:
            logger.debug("Progress enabled for %s", label)
            iterable = tqdm(
                iterator,
                desc=label,
                unit="item",
                leave=False,
                disable=not _progress_enabled(),
            )

        for item in iterable:
            count += 1
            yield item
            if batch_size > 0 and count % batch_size == 0 and sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)
    except Exception as exc:
        logger.error("%s failed: %s", label, exc)
        warnings.append(f"{label} failed: {exc}")


def safe_list_call(label: str, api_call, warnings: List[str]):
    """
    Safely call an API that returns an iterator/list.
    
    If the API call fails (e.g., API not enabled), log warning and return empty list.
    
    Args:
        label: Label for logging
        api_call: Callable that returns an iterator
        warnings: List to append warnings to
        
    Returns:
        Iterator from api_call or empty list on error
    """
    try:
        return api_call()
    except Exception as exc:
        logger.debug("%s not available: %s", label, exc)
        warnings.append(f"{label} not available: {exc}")
        return []

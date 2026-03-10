"""Utility functions for safe API calls and iteration."""

import logging
import time
from typing import List

try:
    from tqdm.auto import tqdm
except Exception:
    tqdm = None


logger = logging.getLogger(__name__)
_PROGRESS_ENABLED = True


def set_progress_enabled(enabled: bool) -> None:
    """Set progress-bar enablement globally for this process."""
    global _PROGRESS_ENABLED
    _PROGRESS_ENABLED = bool(enabled)


def _is_expected_skip(exc: Exception) -> bool:
    """Return True for known non-actionable limitations that should be skipped."""
    message = str(exc).lower()
    known_patterns = [
        "no metastore assigned",
        "ds_no_metastore_assigned",
        "not an account admin",
        "has no attribute 'list'",
    ]
    return any(pattern in message for pattern in known_patterns)


def _progress_enabled() -> bool:
    """Return True when progress bars should be shown."""
    return _PROGRESS_ENABLED


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
        if _is_expected_skip(exc):
            logger.info("%s skipped: %s", label, exc)
            return
        logger.error("%s failed: %s", label, exc)
        warnings.append(f"{label} failed: {exc}")


def _safe_list_call(label: str, api_call, warnings: List[str]):
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
        if _is_expected_skip(exc):
            logger.info("%s skipped: %s", label, exc)
            return []
        logger.debug("%s not available: %s", label, exc)
        warnings.append(f"{label} not available: {exc}")
        return []

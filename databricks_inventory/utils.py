"""Utility functions for safe API calls and iteration."""

import time
from typing import List


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
        for item in iterator:
            count += 1
            yield item
            if batch_size > 0 and count % batch_size == 0 and sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)
    except Exception as exc:
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
        warnings.append(f"{label} not available: {exc}")
        return []

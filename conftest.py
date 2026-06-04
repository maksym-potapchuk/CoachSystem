"""Project-wide pytest fixtures."""
import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """Reset the cache around every test.

    DRF stores throttle counters in Django's cache (LocMemCache in dev/tests),
    which persists for the whole process. Without this, request counts bleed
    across tests and an unrelated test can spuriously hit a 429. Clearing the
    cache per test keeps each one isolated.
    """
    cache.clear()
    yield
    cache.clear()

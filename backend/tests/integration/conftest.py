"""Live tests: call a running WriteWise backend, which calls the real OpenAI API.

They cost API credits, so they are skipped unless explicitly enabled:

    WRITEWISE_LIVE_TESTS=1 REACT_APP_BACKEND_URL=http://127.0.0.1:8001 pytest backend/tests/integration
"""
import os

import pytest

LIVE_ENABLED = os.environ.get("WRITEWISE_LIVE_TESTS") == "1"
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def pytest_collection_modifyitems(config, items):
    if LIVE_ENABLED and BASE_URL:
        return
    reason = "live OpenAI tests: set WRITEWISE_LIVE_TESTS=1 and REACT_APP_BACKEND_URL to run"
    for item in items:
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.skip(reason=reason))

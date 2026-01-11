"""
Pytest configuration and fixtures.
"""

import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def redis_url() -> str:
    """Redis URL for testing (using DB 1 to avoid conflicts)."""
    return "redis://localhost:6379/1"


@pytest.fixture
def test_user_id() -> str:
    """Test user ID."""
    return "test_user_123"


@pytest.fixture
def test_session_id() -> str:
    """Test session ID."""
    return "test_session_456"


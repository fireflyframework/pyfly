"""Shared test fixtures for PyFly."""

import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"

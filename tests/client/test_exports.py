"""Tests for client module public exports."""
from __future__ import annotations


class TestClientExports:
    def test_can_import_declarative(self) -> None:
        from pyfly.client import http_client, get, post, put, delete, patch

        assert http_client is not None

    def test_can_import_post_processor(self) -> None:
        from pyfly.client import HttpClientBeanPostProcessor

        assert HttpClientBeanPostProcessor is not None

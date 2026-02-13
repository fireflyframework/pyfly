"""Tests for package scanning and auto-discovery."""

from pyfly.container import Container
from pyfly.container.scanner import scan_package


class TestPackageScanner:
    def test_scan_finds_injectable_classes(self):
        container = Container()
        # Scan the test_decorators module which has @injectable classes
        found = scan_package("tests.container.test_decorators", container)
        assert found >= 3  # SimpleService, TransientService, SingletonService

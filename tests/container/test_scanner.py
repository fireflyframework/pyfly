"""Tests for package scanning and auto-discovery."""

from pyfly.container import Container, service
from pyfly.container.scanner import scan_package
from pyfly.container.stereotypes import component, repository


@service
class ScannableServiceA:
    pass


@service
class ScannableServiceB:
    pass


@component
class ScannableComponent:
    pass


@repository
class ScannableRepository:
    pass


class TestPackageScanner:
    def test_scan_finds_stereotype_decorated_classes(self):
        container = Container()
        # Scan this module which has stereotype-decorated classes
        found = scan_package("tests.container.test_scanner", container)
        assert found >= 4  # ScannableServiceA, ScannableServiceB, ScannableComponent, ScannableRepository

"""Tests for AspectRegistry and AdviceBinding."""

from __future__ import annotations

from pyfly.aop.decorators import after_returning, around, aspect, before
from pyfly.aop.registry import AspectRegistry
from pyfly.container.ordering import order


# ---- Fixture aspects --------------------------------------------------------


@aspect
class LoggingAspect:
    @before("service.*.*")
    def log_before(self, jp):
        pass

    @after_returning("service.*.*")
    def log_after(self, jp):
        pass


@order(10)
@aspect
class SecurityAspect:
    @around("service.*.create")
    def check_auth(self, jp):
        pass


@order(-5)
@aspect
class EarlyAspect:
    @before("service.*.*")
    def run_early(self, jp):
        pass


# ---- Tests ------------------------------------------------------------------


class TestAspectRegistry:
    """AspectRegistry registration, ordering, and matching."""

    def test_register_single_aspect_binding_count(self) -> None:
        registry = AspectRegistry()
        registry.register(LoggingAspect())
        assert len(registry.get_all_bindings()) == 2

    def test_bindings_have_correct_types_and_pointcuts(self) -> None:
        registry = AspectRegistry()
        registry.register(LoggingAspect())
        bindings = registry.get_all_bindings()

        types = {b.advice_type for b in bindings}
        assert types == {"before", "after_returning"}

        pointcuts = {b.pointcut for b in bindings}
        assert pointcuts == {"service.*.*"}

    def test_multiple_aspects_ordered_by_order(self) -> None:
        registry = AspectRegistry()
        registry.register(LoggingAspect())  # order 0
        registry.register(SecurityAspect())  # order 10
        registry.register(EarlyAspect())  # order -5

        bindings = registry.get_all_bindings()
        orders = [b.aspect_order for b in bindings]
        assert orders == sorted(orders)
        # EarlyAspect (-5) comes first, then LoggingAspect (0), then SecurityAspect (10)
        assert bindings[0].aspect_order == -5
        assert bindings[-1].aspect_order == 10

    def test_get_matching_returns_matching_bindings(self) -> None:
        registry = AspectRegistry()
        registry.register(LoggingAspect())
        registry.register(SecurityAspect())

        matches = registry.get_matching("service.OrderService.create")
        assert len(matches) == 3  # log_before + log_after + check_auth

    def test_get_matching_partial(self) -> None:
        registry = AspectRegistry()
        registry.register(LoggingAspect())
        registry.register(SecurityAspect())

        # "delete" does not match SecurityAspect's "service.*.create"
        matches = registry.get_matching("service.OrderService.delete")
        assert len(matches) == 2  # only LoggingAspect's two bindings

    def test_no_match_for_unrelated_qualified_name(self) -> None:
        registry = AspectRegistry()
        registry.register(LoggingAspect())
        registry.register(SecurityAspect())

        matches = registry.get_matching("repo.UserRepo.find_by_id")
        assert len(matches) == 0

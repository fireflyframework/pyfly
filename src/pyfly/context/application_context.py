# Copyright 2026 Firefly Software Solutions Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""ApplicationContext — the central bean registry and lifecycle manager."""

from __future__ import annotations

import contextlib
import inspect
import typing
from typing import Any, TypeVar

from pyfly.container.container import Container
from pyfly.container.exceptions import BeanCreationException
from pyfly.container.ordering import get_order
from pyfly.container.types import Scope
from pyfly.context.condition_evaluator import ConditionEvaluator
from pyfly.context.environment import Environment
from pyfly.context.events import (
    ApplicationEventBus,
    ApplicationReadyEvent,
    ContextClosedEvent,
    ContextRefreshedEvent,
)
from pyfly.context.post_processor import BeanPostProcessor
from pyfly.core.config import Config

T = TypeVar("T")


class ApplicationContext:
    """Central bean registry, lifecycle manager, and event publisher.

    This is the PyFly equivalent of Spring's ApplicationContext. It wraps
    the DI Container and adds:
    - Named bean access
    - @Bean factory method resolution from @configuration classes
    - @post_construct / @pre_destroy lifecycle
    - BeanPostProcessor hooks
    - Application event publishing
    - Profile-aware Environment
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._container = Container()
        self._environment = Environment(config)
        self._event_bus = ApplicationEventBus()
        self._post_processors: list[BeanPostProcessor] = []
        self._started = False
        self._infrastructure_adapters: list[Any] = []

        # Register config as a singleton bean
        self._container.register(Config, scope=Scope.SINGLETON)
        self._container._registrations[Config].instance = config

    # ------------------------------------------------------------------
    # Bean registration
    # ------------------------------------------------------------------

    def register_bean(self, cls: type, **kwargs: Any) -> None:
        """Register a bean class with the context."""
        name = kwargs.get("name", "") or getattr(cls, "__pyfly_bean_name__", "")
        scope = kwargs.get("scope") or getattr(cls, "__pyfly_scope__", Scope.SINGLETON)
        self._container.register(cls, scope=scope, name=name)

    def register_post_processor(self, processor: BeanPostProcessor) -> None:
        """Register a BeanPostProcessor."""
        self._post_processors.append(processor)

    # ------------------------------------------------------------------
    # Bean access
    # ------------------------------------------------------------------

    def get_bean(self, bean_type: type[T]) -> T:
        """Resolve a bean by type."""
        return self._container.resolve(bean_type)

    def get_bean_by_name(self, name: str) -> Any:
        """Resolve a bean by its registered name."""
        return self._container.resolve_by_name(name)

    def get_beans_of_type(self, bean_type: type[T]) -> list[T]:
        """Resolve all beans of the given type, sorted by @order."""
        results = self._container.resolve_all(bean_type)
        return sorted(results, key=lambda b: get_order(type(b)))

    def contains_bean(self, name: str) -> bool:
        """Check if a named bean exists."""
        return self._container.contains(name)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def container(self) -> Container:
        """Escape hatch: direct access to the underlying Container."""
        return self._container

    @property
    def config(self) -> Config:
        """Application configuration."""
        return self._config

    @property
    def environment(self) -> Environment:
        """Application environment with profile support."""
        return self._environment

    @property
    def event_bus(self) -> ApplicationEventBus:
        """Application event bus."""
        return self._event_bus

    @property
    def bean_count(self) -> int:
        """Number of beans eagerly initialized during start()."""
        return sum(
            1 for reg in self._container._registrations.values() if reg.instance is not None
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the context: resolve @configuration beans, call lifecycle hooks, publish events."""
        try:
            await self._do_start()
        except BeanCreationException:
            raise  # Already a clear error, propagate as-is
        except Exception as exc:
            raise BeanCreationException(
                subsystem="startup",
                provider="unknown",
                reason=str(exc),
            ) from exc

    async def _do_start(self) -> None:
        """Internal startup logic."""
        # 1. Filter beans by active profiles
        self._filter_by_profile()

        # 1b. Evaluate @conditional_on_* decorators (pass 1: property/class)
        self._evaluate_conditions()

        # 2. Process user @configuration classes and their @bean methods
        self._process_configurations(auto=False)

        # 2b. Process @auto_configuration classes (after user configs, so
        #     @conditional_on_missing_bean can see user-provided beans)
        self._evaluate_bean_conditions()
        self._process_configurations(auto=True)

        # 2c. Run imperative auto-configuration (detect providers, wire adapter beans)
        from pyfly.config.auto import AutoConfigurationEngine

        engine = AutoConfigurationEngine()
        engine.configure(self._config, self._container)

        # 2d. Start infrastructure adapters (fail-fast: validates connectivity)
        self._infrastructure_adapters = engine.adapters
        for adapter in self._infrastructure_adapters:
            if hasattr(adapter, 'start'):
                try:
                    await adapter.start()
                except Exception as exc:
                    adapter_name = type(adapter).__name__
                    subsystem = self._infer_subsystem(adapter_name)
                    provider = engine.results.get(subsystem, "unknown")
                    raise BeanCreationException(
                        subsystem=subsystem,
                        provider=provider,
                        reason=str(exc),
                    ) from exc

        # 3. Eagerly resolve all singletons (sorted by @order)
        sorted_entries = sorted(
            self._container._registrations.items(),
            key=lambda item: get_order(item[0]),
        )
        for cls, reg in sorted_entries:
            if reg.scope == Scope.SINGLETON and reg.instance is None:
                with contextlib.suppress(KeyError):
                    self._container.resolve(cls)

        # 4. Run post-processors and lifecycle hooks
        sorted_pps = sorted(self._post_processors, key=lambda pp: get_order(type(pp)))
        for reg in self._container._registrations.values():
            if reg.instance is not None:
                bean_name = reg.name or reg.impl_type.__name__

                # BeanPostProcessor.before_init
                for pp in sorted_pps:
                    reg.instance = pp.before_init(reg.instance, bean_name)

                # @post_construct
                await self._call_post_construct(reg.instance)

                # BeanPostProcessor.after_init
                for pp in sorted_pps:
                    reg.instance = pp.after_init(reg.instance, bean_name)

        # 5. Publish lifecycle events
        await self._event_bus.publish(ContextRefreshedEvent())
        await self._event_bus.publish(ApplicationReadyEvent())
        self._started = True

    async def stop(self) -> None:
        """Stop the context: call @pre_destroy, publish ContextClosedEvent."""
        # Stop infrastructure adapters (reverse order)
        for adapter in reversed(self._infrastructure_adapters):
            if hasattr(adapter, 'stop'):
                try:
                    await adapter.stop()
                except Exception:
                    pass  # Best-effort cleanup

        # Call @pre_destroy on all resolved beans (reverse order)
        for reg in reversed(list(self._container._registrations.values())):
            if reg.instance is not None:
                await self._call_pre_destroy(reg.instance)

        await self._event_bus.publish(ContextClosedEvent())
        self._started = False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_subsystem(adapter_name: str) -> str:
        """Infer subsystem from adapter class name."""
        name_lower = adapter_name.lower()
        if "kafka" in name_lower:
            return "messaging"
        if "rabbit" in name_lower:
            return "messaging"
        if "redis" in name_lower:
            return "cache"
        if "httpx" in name_lower or "httpclient" in name_lower:
            return "client"
        if "executor" in name_lower or "threadpool" in name_lower:
            return "scheduling"
        if "eventbus" in name_lower or "eventpublisher" in name_lower:
            return "eda"
        if "memory" in name_lower:
            if "cache" in name_lower:
                return "cache"
            if "broker" in name_lower or "message" in name_lower:
                return "messaging"
            if "event" in name_lower:
                return "eda"
        return "infrastructure"

    def _filter_by_profile(self) -> None:
        """Remove beans whose profile expression does not match active profiles."""
        to_remove: list[type] = []
        for cls in list(self._container._registrations):
            profile_expr = getattr(cls, "__pyfly_profile__", "")
            if profile_expr and not self._environment.accepts_profiles(profile_expr):
                to_remove.append(cls)

        for cls in to_remove:
            self._remove_registration(cls)

    def _evaluate_conditions(self) -> None:
        """Pass 1: remove beans that fail non-bean-dependent conditions (on_property, on_class)."""
        evaluator = ConditionEvaluator(self._config, self._container)
        to_remove: list[type] = []
        for cls in list(self._container._registrations):
            if not evaluator.should_include(cls, bean_pass=False):
                to_remove.append(cls)
        for cls in to_remove:
            self._remove_registration(cls)

    def _evaluate_bean_conditions(self) -> None:
        """Pass 2: remove beans that fail bean-dependent conditions (on_bean, on_missing_bean)."""
        evaluator = ConditionEvaluator(self._config, self._container)
        to_remove: list[type] = []
        for cls in list(self._container._registrations):
            if not evaluator.should_include(cls, bean_pass=True):
                to_remove.append(cls)
        for cls in to_remove:
            self._remove_registration(cls)

    def _remove_registration(self, cls: type) -> None:
        """Remove a bean registration and its named entry."""
        reg = self._container._registrations.pop(cls)
        if reg.name and reg.name in self._container._named:
            del self._container._named[reg.name]

    def _process_configurations(self, *, auto: bool = False) -> None:
        """Find @configuration beans, call their @bean methods, register results.

        Args:
            auto: When False, process only user @configuration classes.
                  When True, process only @auto_configuration classes.
        """
        for cls, _reg in list(self._container._registrations.items()):
            if getattr(cls, "__pyfly_stereotype__", "") != "configuration":
                continue
            is_auto = getattr(cls, "__pyfly_auto_configuration__", False)
            if is_auto != auto:
                continue

            # Resolve the configuration class itself
            config_instance = self._container.resolve(cls)

            # Find @bean methods
            for attr_name in dir(config_instance):
                method = getattr(config_instance, attr_name, None)
                if method is None or not getattr(method, "__pyfly_bean__", False):
                    continue

                # Get return type from method hints
                hints = typing.get_type_hints(method)
                return_type = hints.get("return")
                if return_type is None:
                    continue

                # Call the factory method (inject params from container)
                result = self._call_bean_method(config_instance, method)
                bean_name = getattr(method, "__pyfly_bean_name__", "") or attr_name
                bean_scope = getattr(method, "__pyfly_bean_scope__", Scope.SINGLETON)

                # Register the produced bean
                self._container.register(return_type, scope=bean_scope, name=bean_name)
                if bean_scope == Scope.SINGLETON:
                    self._container._registrations[return_type].instance = result

    def _call_bean_method(self, config_instance: Any, method: Any) -> Any:
        """Call a @bean method, injecting its parameters from the container."""
        hints = typing.get_type_hints(method)
        hints.pop("return", None)

        kwargs: dict[str, Any] = {}
        for param_name, param_type in hints.items():
            kwargs[param_name] = self._container.resolve(param_type)

        return method(**kwargs)

    async def _call_post_construct(self, instance: Any) -> None:
        """Call all @post_construct methods on an instance."""
        for attr_name in dir(instance):
            method = getattr(instance, attr_name, None)
            if method is not None and getattr(method, "__pyfly_post_construct__", False):
                result = method()
                if inspect.isawaitable(result):
                    await result

    async def _call_pre_destroy(self, instance: Any) -> None:
        """Call all @pre_destroy methods on an instance."""
        for attr_name in dir(instance):
            method = getattr(instance, attr_name, None)
            if method is not None and getattr(method, "__pyfly_pre_destroy__", False):
                result = method()
                if inspect.isawaitable(result):
                    await result

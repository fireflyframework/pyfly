"""Tests for ApplicationContext — the central bean registry."""

import pytest

from pyfly.container.bean import bean
from pyfly.container.stereotypes import configuration, repository, service
from pyfly.context.application_context import ApplicationContext
from pyfly.context.events import ApplicationReadyEvent, ContextRefreshedEvent
from pyfly.context.lifecycle import post_construct, pre_destroy
from pyfly.core.config import Config

# --- Test beans ---

@service
class GreetingService:
    def greet(self) -> str:
        return "Hello"


@repository
class UserRepository:
    def find(self, user_id: str) -> dict:
        return {"id": user_id}


@service
class UserService:
    def __init__(self, repo: UserRepository):
        self.repo = repo

    def get_user(self, user_id: str) -> dict:
        return self.repo.find(user_id)


@configuration
class AppConfig:
    @bean
    def greeting_message(self) -> str:
        return "Welcome!"


# --- Tests ---

class TestApplicationContextBasics:
    @pytest.mark.asyncio
    async def test_register_and_resolve(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(GreetingService)
        await ctx.start()
        svc = ctx.get_bean(GreetingService)
        assert svc.greet() == "Hello"

    @pytest.mark.asyncio
    async def test_dependency_injection(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(UserRepository)
        ctx.register_bean(UserService)
        await ctx.start()
        svc = ctx.get_bean(UserService)
        assert svc.get_user("u-1")["id"] == "u-1"

    @pytest.mark.asyncio
    async def test_get_bean_by_name(self):
        ctx = ApplicationContext(Config({}))

        @service(name="myService")
        class NamedService:
            pass

        ctx.register_bean(NamedService)
        await ctx.start()
        result = ctx.get_bean_by_name("myService")
        assert isinstance(result, NamedService)

    @pytest.mark.asyncio
    async def test_contains_bean(self):
        ctx = ApplicationContext(Config({}))

        @service(name="exists")
        class ExistingService:
            pass

        ctx.register_bean(ExistingService)
        await ctx.start()
        assert ctx.contains_bean("exists") is True
        assert ctx.contains_bean("missing") is False


class TestBeanFactoryMethods:
    @pytest.mark.asyncio
    async def test_configuration_bean_method(self):
        ctx = ApplicationContext(Config({}))
        ctx.register_bean(AppConfig)
        await ctx.start()
        msg = ctx.get_bean(str)
        assert msg == "Welcome!"


class TestLifecycleAnnotations:
    @pytest.mark.asyncio
    async def test_post_construct_called(self):
        log: list[str] = []

        @service
        class InitService:
            @post_construct
            async def setup(self):
                log.append("initialized")

        ctx = ApplicationContext(Config({}))
        ctx.register_bean(InitService)
        await ctx.start()
        assert "initialized" in log

    @pytest.mark.asyncio
    async def test_pre_destroy_called(self):
        log: list[str] = []

        @service
        class CleanupService:
            @pre_destroy
            async def teardown(self):
                log.append("destroyed")

        ctx = ApplicationContext(Config({}))
        ctx.register_bean(CleanupService)
        await ctx.start()
        await ctx.stop()
        assert "destroyed" in log


class TestApplicationEvents:
    @pytest.mark.asyncio
    async def test_context_refreshed_published(self):
        events: list = []

        ctx = ApplicationContext(Config({}))

        async def on_refreshed(event):
            events.append(event)

        ctx.event_bus.subscribe(ContextRefreshedEvent, on_refreshed)
        await ctx.start()
        assert any(isinstance(e, ContextRefreshedEvent) for e in events)

    @pytest.mark.asyncio
    async def test_application_ready_published(self):
        events: list = []

        ctx = ApplicationContext(Config({}))

        async def on_ready(event):
            events.append(event)

        ctx.event_bus.subscribe(ApplicationReadyEvent, on_ready)
        await ctx.start()
        assert any(isinstance(e, ApplicationReadyEvent) for e in events)


class TestEnvironmentAccess:
    @pytest.mark.asyncio
    async def test_environment_available(self):
        ctx = ApplicationContext(Config({"app": {"name": "test"}}))
        await ctx.start()
        assert ctx.environment.get_property("app.name") == "test"

    @pytest.mark.asyncio
    async def test_config_available(self):
        config = Config({"key": "value"})
        ctx = ApplicationContext(config)
        await ctx.start()
        assert ctx.config.get("key") == "value"

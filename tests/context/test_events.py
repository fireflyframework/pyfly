"""Tests for application events and @event_listener."""

import pytest

from pyfly.context.events import (
    ApplicationEvent,
    ApplicationEventBus,
    ApplicationReadyEvent,
    ContextClosedEvent,
    ContextRefreshedEvent,
    app_event_listener,
)


class TestApplicationEvents:
    def test_context_refreshed_event(self):
        event = ContextRefreshedEvent()
        assert isinstance(event, ApplicationEvent)

    def test_application_ready_event(self):
        event = ApplicationReadyEvent()
        assert isinstance(event, ApplicationEvent)

    def test_context_closed_event(self):
        event = ContextClosedEvent()
        assert isinstance(event, ApplicationEvent)

    def test_custom_event(self):
        class UserCreatedEvent(ApplicationEvent):
            def __init__(self, user_id: str):
                self.user_id = user_id

        event = UserCreatedEvent(user_id="u-1")
        assert event.user_id == "u-1"
        assert isinstance(event, ApplicationEvent)


class TestAppEventListener:
    def test_marks_method(self):
        class MyService:
            @app_event_listener
            async def on_ready(self, event: ApplicationReadyEvent) -> None:
                pass

        assert getattr(MyService.on_ready, "__pyfly_app_event_listener__") is True

    def test_preserves_method(self):
        class MyService:
            @app_event_listener
            async def on_ready(self, event: ApplicationReadyEvent) -> None:
                self.ready = True

        svc = MyService()
        assert callable(svc.on_ready)


class TestApplicationEventBus:
    @pytest.mark.asyncio
    async def test_publish_calls_listeners(self):
        bus = ApplicationEventBus()
        received: list[ApplicationEvent] = []

        async def listener(event: ApplicationReadyEvent) -> None:
            received.append(event)

        bus.subscribe(ApplicationReadyEvent, listener)
        await bus.publish(ApplicationReadyEvent())
        assert len(received) == 1
        assert isinstance(received[0], ApplicationReadyEvent)

    @pytest.mark.asyncio
    async def test_publish_only_matching_type(self):
        bus = ApplicationEventBus()
        received: list[ApplicationEvent] = []

        async def listener(event: ApplicationReadyEvent) -> None:
            received.append(event)

        bus.subscribe(ApplicationReadyEvent, listener)
        await bus.publish(ContextClosedEvent())
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_multiple_listeners(self):
        bus = ApplicationEventBus()
        log: list[str] = []

        async def listener1(event: ApplicationReadyEvent) -> None:
            log.append("first")

        async def listener2(event: ApplicationReadyEvent) -> None:
            log.append("second")

        bus.subscribe(ApplicationReadyEvent, listener1)
        bus.subscribe(ApplicationReadyEvent, listener2)
        await bus.publish(ApplicationReadyEvent())
        assert log == ["first", "second"]

    @pytest.mark.asyncio
    async def test_subclass_event_received_by_parent_listener(self):
        bus = ApplicationEventBus()
        received: list[ApplicationEvent] = []

        async def listener(event: ApplicationEvent) -> None:
            received.append(event)

        bus.subscribe(ApplicationEvent, listener)
        await bus.publish(ApplicationReadyEvent())
        assert len(received) == 1

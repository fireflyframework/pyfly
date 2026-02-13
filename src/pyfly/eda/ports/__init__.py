"""EDA ports — abstract interfaces for event-driven architecture."""

from pyfly.eda.ports.outbound import EventConsumer, EventPublisher

__all__ = ["EventConsumer", "EventPublisher"]

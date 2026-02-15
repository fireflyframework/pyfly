# PyFly Adapters

Adapters are the concrete implementations that fulfill PyFly's port contracts.
Each adapter doc covers setup, configuration, and adapter-specific features.

For the full port APIs and usage patterns, see the linked module guides.

---

## Data Adapters

| Adapter | Module | Backend | Guide |
|---------|--------|---------|-------|
| [SQLAlchemy](sqlalchemy.md) | Data Relational | PostgreSQL, MySQL, SQLite | [Module Guide](../modules/data-relational.md) |
| [MongoDB](mongodb.md) | Data Document | MongoDB (Beanie ODM) | [Module Guide](../modules/data-document.md) |

## Web Adapter

| Adapter | Module | Backend | Guide |
|---------|--------|---------|-------|
| [Starlette](starlette.md) | Web | Starlette / Uvicorn | [Module Guide](../modules/web.md) |

## Messaging Adapters

| Adapter | Module | Backend | Guide |
|---------|--------|---------|-------|
| [Kafka](kafka.md) | Messaging | Apache Kafka (aiokafka) | [Module Guide](../modules/messaging.md) |
| [RabbitMQ](rabbitmq.md) | Messaging | RabbitMQ (aio-pika) | [Module Guide](../modules/messaging.md) |

## Cache Adapter

| Adapter | Module | Backend | Guide |
|---------|--------|---------|-------|
| [Redis](redis.md) | Caching | Redis (async) | [Module Guide](../modules/caching.md) |

## HTTP Client Adapter

| Adapter | Module | Backend | Guide |
|---------|--------|---------|-------|
| [HTTPX](httpx.md) | Client | HTTPX | [Module Guide](../modules/client.md) |

---

<p align="center">
  <a href="../README.md">Back to Documentation Home</a> · <a href="../modules/README.md">Module Guides</a>
</p>

# RabbitMQ Adapter

> **Module:** Messaging — [Module Guide](../modules/messaging.md)
> **Package:** `pyfly.messaging.adapters.rabbitmq`
> **Backend:** aio-pika 9.0+

## Quick Start

### Installation

```bash
pip install pyfly[rabbitmq]

# Or install both Kafka and RabbitMQ
pip install pyfly[eda]
```

### Minimal Configuration

```yaml
# pyfly.yaml
pyfly:
  messaging:
    provider: "rabbitmq"
    rabbitmq:
      url: "amqp://guest:guest@localhost/"
```

### Minimal Example

```python
from pyfly.messaging import message_listener

@message_listener(topic="orders", group_id="order-service")
async def handle_order(self, event: dict) -> None:
    print(f"Received order: {event}")
```

---

## Configuration Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `pyfly.messaging.provider` | `str` | `"auto"` | Adapter selection (`auto`, `kafka`, `rabbitmq`) |
| `pyfly.messaging.rabbitmq.url` | `str` | `"amqp://guest:guest@localhost/"` | RabbitMQ connection URL (AMQP) |

When `provider` is `"auto"`, PyFly selects the adapter based on which library is installed. If `aio-pika` is found, the RabbitMQ adapter is used.

---

## Adapter-Specific Features

### RabbitMQAdapter

Implements `MessageBrokerPort` using `aio_pika.connect_robust()`.

- **Exchange:** Uses a single direct exchange (default name: `"pyfly"`) with topics as routing keys
- **Queues:** Declares durable queues per consumer group
- **Publishing:** Serializes messages to JSON and publishes with optional headers
- **Subscribing:** Creates async consumers with acknowledgment support

### Consumer Groups

Consumer groups are mapped to RabbitMQ queues. Multiple instances with the same `group_id` share the queue for competing-consumer load balancing.

### Lifecycle

- `start()` — Establishes a robust connection, declares exchange and queues, starts consumers
- `stop()` — Closes the connection gracefully

---

## Testing

When no broker library is installed, PyFly auto-configures `InMemoryMessageBroker` — no RabbitMQ needed for unit tests.

```yaml
# pyfly-test.yaml
pyfly:
  messaging:
    provider: "memory"
```

---

## See Also

- [Messaging Module Guide](../modules/messaging.md) — Full API reference: publishing, consuming, message listeners
- [Kafka Adapter](kafka.md) — Alternative messaging backend
- [Adapter Catalog](README.md)

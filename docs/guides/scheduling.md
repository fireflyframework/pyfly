# Scheduling Guide

Schedule periodic tasks, cron jobs, and asynchronous method execution with the
PyFly scheduling module.

---

## Table of Contents

1. [Introduction](#introduction)
2. [The @scheduled Decorator](#the-scheduled-decorator)
   - [fixed_rate](#fixed_rate)
   - [fixed_delay](#fixed_delay)
   - [cron](#cron)
   - [initial_delay](#initial_delay)
3. [CronExpression](#cronexpression)
   - [5-Field Format](#5-field-format)
   - [next_fire_time()](#next_fire_time)
   - [previous_fire_time()](#previous_fire_time)
   - [next_n_fire_times()](#next_n_fire_times)
   - [seconds_until_next()](#seconds_until_next)
   - [Cron Examples](#cron-examples)
4. [TaskScheduler](#taskscheduler)
   - [Creating a TaskScheduler](#creating-a-taskscheduler)
   - [Discovering Scheduled Methods](#discovering-scheduled-methods)
   - [Starting and Stopping](#starting-and-stopping)
   - [How Loops Work Internally](#how-loops-work-internally)
5. [TaskExecutorPort](#taskexecutorport)
6. [AsyncIOTaskExecutor](#asynciotaskexecutor)
7. [ThreadPoolTaskExecutor](#threadpooltaskexecutor)
8. [The @async_method Decorator](#the-async_method-decorator)
9. [Configuration](#configuration)
10. [Complete Example](#complete-example)

---

## Introduction

Most non-trivial applications need to run work on a schedule: syncing data from
an upstream API every five minutes, purging stale records at midnight, or
publishing health-check heartbeats every ten seconds. The PyFly scheduling
module gives you a declarative, decorator-driven way to define these tasks
without manually managing threads, event loops, or timer wheels.

The module is built around a hexagonal architecture:

- **Decorators** (`@scheduled`, `@async_method`) mark methods for scheduling.
- **CronExpression** provides next-fire-time calculations via standard 5-field
  cron syntax.
- **TaskScheduler** is the engine that discovers decorated methods, creates
  execution loops, and manages their lifecycle.
- **TaskExecutorPort** is the outbound port abstraction, allowing you to swap
  execution strategies.
- **AsyncIOTaskExecutor** and **ThreadPoolTaskExecutor** are the built-in
  adapters.

All public types are available from a single import:

```python
from pyfly.scheduling import (
    scheduled,
    async_method,
    CronExpression,
    TaskScheduler,
    TaskExecutorPort,
    AsyncIOTaskExecutor,
    ThreadPoolTaskExecutor,
)
```

---

## The @scheduled Decorator

`@scheduled` marks a bean method for periodic execution. It is a keyword-only
decorator that accepts exactly one trigger parameter: `fixed_rate`,
`fixed_delay`, or `cron`. Providing zero or more than one trigger raises a
`ValueError` at decoration time.

```python
from pyfly.scheduling import scheduled
```

### fixed_rate

Runs the method at a fixed interval, measured from the **start** of each
invocation. If the method takes longer than the interval, the next run begins
immediately after the current one finishes, but there is no overlap -- the
scheduler awaits the executor's `submit()` then sleeps for the remaining
interval.

The parameter accepts a `datetime.timedelta`:

```python
from datetime import timedelta

class MetricsCollector:
    @scheduled(fixed_rate=timedelta(seconds=30))
    async def collect(self):
        """Collect system metrics every 30 seconds."""
        await self.scrape_metrics()
```

### fixed_delay

Runs the method repeatedly with a fixed delay **between the end of one
execution and the start of the next**. This guarantees a minimum gap between
runs, regardless of how long each execution takes.

```python
class DataSyncer:
    @scheduled(fixed_delay=timedelta(minutes=5))
    async def sync(self):
        """Sync data, then wait 5 minutes before the next sync."""
        await self.pull_upstream_changes()
```

The key difference from `fixed_rate`: with `fixed_delay`, the scheduler waits
for the task to complete (`await task`), then sleeps for the full delay before
running again. With `fixed_rate`, the scheduler fires-and-forgets the task,
sleeps for the interval, then fires again.

### cron

Runs the method according to a standard 5-field cron expression. The scheduler
calculates `seconds_until_next()` via `CronExpression`, sleeps that long, then
executes the method.

```python
class ReportGenerator:
    @scheduled(cron="0 2 * * 1")  # Every Monday at 02:00
    async def generate_weekly_report(self):
        await self.build_and_email_report()
```

### initial_delay

An optional `timedelta` that delays the very first execution. Applies to both
`fixed_rate` and `fixed_delay` triggers. Ignored for `cron` triggers (the first
execution always waits for the next matching cron time).

```python
class CacheWarmer:
    @scheduled(fixed_rate=timedelta(minutes=10), initial_delay=timedelta(seconds=30))
    async def warm_cache(self):
        """Wait 30 seconds after startup, then warm cache every 10 minutes."""
        await self.preload_hot_keys()
```

### Decorator Metadata

Under the hood, `@scheduled` attaches metadata attributes to the decorated
function:

| Attribute | Value |
|---|---|
| `__pyfly_scheduled__` | `True` |
| `__pyfly_scheduled_cron__` | The cron expression string, or `None` |
| `__pyfly_scheduled_fixed_rate__` | The `timedelta`, or `None` |
| `__pyfly_scheduled_fixed_delay__` | The `timedelta`, or `None` |
| `__pyfly_scheduled_initial_delay__` | The `timedelta`, or `None` |

The `TaskScheduler` reads these attributes during its discovery phase.

---

## CronExpression

`CronExpression` is an immutable dataclass that wraps a cron expression string
and provides fire-time calculation methods. It delegates parsing and iteration
to the [croniter](https://github.com/kiorky/croniter) library.

```python
from pyfly.scheduling import CronExpression
```

### 5-Field Format

PyFly uses the standard 5-field cron format:

```
 +------------- minute       (0-59)
 |  +---------- hour         (0-23)
 |  |  +------- day of month (1-31)
 |  |  |  +---- month        (1-12)
 |  |  |  |  +- day of week  (0-6, 0 = Sunday)
 |  |  |  |  |
 *  *  *  *  *
```

Special characters: `*` (any), `,` (list), `-` (range), `/` (step).

Invalid expressions raise `ValueError` during construction:

```python
CronExpression("invalid")  # ValueError: Invalid cron expression: invalid
```

### next_fire_time()

Returns the next `datetime` after a given reference point (default: `now()`):

```python
from datetime import datetime
from pyfly.scheduling import CronExpression

cron = CronExpression("0 9 * * *")  # Daily at 09:00
next_run = cron.next_fire_time()
print(next_run)  # e.g., 2026-02-15 09:00:00

# With an explicit reference time
ref = datetime(2026, 3, 1, 8, 0)
next_run = cron.next_fire_time(after=ref)
print(next_run)  # 2026-03-01 09:00:00
```

### previous_fire_time()

Returns the most recent fire time before a given reference point:

```python
cron = CronExpression("0 */6 * * *")  # Every 6 hours
prev = cron.previous_fire_time()
```

### next_n_fire_times()

Returns a list of the next N fire times:

```python
cron = CronExpression("30 8 * * 1-5")  # Weekdays at 08:30
upcoming = cron.next_n_fire_times(5)
for t in upcoming:
    print(t)
```

### seconds_until_next()

Returns the number of seconds (as `float`) until the next fire time. This is
the method the `TaskScheduler` uses to determine how long to sleep in a cron
loop:

```python
cron = CronExpression("0 0 * * *")  # Midnight
delay = cron.seconds_until_next()
print(f"Next midnight in {delay:.0f} seconds")
```

### Cron Examples

| Expression | Description |
|---|---|
| `* * * * *` | Every minute |
| `0 * * * *` | Every hour, on the hour |
| `0 0 * * *` | Every day at midnight |
| `0 9 * * 1-5` | Weekdays at 09:00 |
| `30 2 1 * *` | 1st of each month at 02:30 |
| `*/15 * * * *` | Every 15 minutes |
| `0 0 * * 0` | Every Sunday at midnight |
| `0 8,12,18 * * *` | Daily at 08:00, 12:00, and 18:00 |

---

## TaskScheduler

`TaskScheduler` is the engine that ties everything together. It scans beans for
`@scheduled` methods, creates async loops for each, and manages start/stop
lifecycle.

```python
from pyfly.scheduling import TaskScheduler
```

### Creating a TaskScheduler

The constructor takes an optional `TaskExecutorPort`. If none is provided, it
defaults to `AsyncIOTaskExecutor`:

```python
# Default: uses AsyncIOTaskExecutor
scheduler = TaskScheduler()

# Custom: use ThreadPoolTaskExecutor for CPU-bound tasks
from pyfly.scheduling import ThreadPoolTaskExecutor
scheduler = TaskScheduler(executor=ThreadPoolTaskExecutor(max_workers=8))
```

### Discovering Scheduled Methods

Call `discover()` with a list of bean instances. It scans every public attribute
(names not starting with `_`) and records those marked with
`__pyfly_scheduled__ = True`. Returns the number of scheduled methods found:

```python
beans = [metrics_collector, data_syncer, report_generator]
count = scheduler.discover(beans)
print(f"Found {count} scheduled methods")
```

### Starting and Stopping

`start()` and `stop()` are async methods. `start()` creates an
`asyncio.Task` for each discovered entry. `stop()` cancels all loop tasks,
gathers them, clears the task list, and stops the executor:

```python
await scheduler.start()
# ... application runs ...
await scheduler.stop()
```

Stops all scheduling loops and the executor. Always waits for pending tasks
to complete (graceful shutdown).

### How Loops Work Internally

Each trigger type has its own loop coroutine inside `TaskScheduler`:

- **Cron loop** (`_run_cron_loop`): Calculates `seconds_until_next()` from a
  `CronExpression`, sleeps that duration, submits the method to the executor,
  then repeats.
- **Fixed-rate loop** (`_run_fixed_rate_loop`): Optionally sleeps for
  `initial_delay`, then enters a loop that submits the method and sleeps for
  the rate interval.
- **Fixed-delay loop** (`_run_fixed_delay_loop`): Optionally sleeps for
  `initial_delay`, then enters a loop that submits the method, **awaits
  the returned task** (waits for completion), sleeps for the delay, then
  repeats.

Both sync and async methods are supported transparently. The static
`_invoke()` helper calls the method and, if the result is awaitable, awaits it.

---

## TaskExecutorPort

`TaskExecutorPort` is a `Protocol` (runtime-checkable) that defines the
contract for task execution:

```python
from pyfly.scheduling import TaskExecutorPort

@runtime_checkable
class TaskExecutorPort(Protocol):
    async def submit(self, coro: Coroutine[Any, Any, T]) -> asyncio.Task[T]: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
```

You can implement this protocol to create custom executors -- for example, one
that publishes tasks to a distributed queue or logs execution metrics.

---

## AsyncIOTaskExecutor

The default executor. Wraps `asyncio.create_task()` and tracks running tasks in
a `set` for clean shutdown:

```python
from pyfly.scheduling import AsyncIOTaskExecutor

executor = AsyncIOTaskExecutor()
task = await executor.submit(some_coroutine())
await executor.stop()  # Wait for all pending tasks
```

- **submit()**: Creates an `asyncio.Task` via `create_task()`, adds it to an
  internal tracking set, and registers a done-callback that removes it.
- **start()**: No-op (ready after construction).
- **stop()**: Waits for all pending tasks to complete, then clears the task set.

This executor is ideal for I/O-bound tasks that use `async`/`await`.

---

## ThreadPoolTaskExecutor

For CPU-bound or blocking work, `ThreadPoolTaskExecutor` wraps a standard
`concurrent.futures.ThreadPoolExecutor`:

```python
from pyfly.scheduling import ThreadPoolTaskExecutor

executor = ThreadPoolTaskExecutor(max_workers=4)
```

It exposes two submission methods:

- **submit(coro)**: Works identically to `AsyncIOTaskExecutor.submit()` --
  creates an `asyncio.Task` for async coroutines.
- **submit_sync(func, *args)**: Runs a synchronous function in the thread pool
  via `loop.run_in_executor()`, wraps the result with `asyncio.ensure_future()`.

```python
# Async coroutine
task = await executor.submit(async_work())

# Sync function in thread pool
task = executor.submit_sync(cpu_heavy_function, arg1, arg2)
```

**Constructor:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `max_workers` | `int` | `4` | Number of threads in the pool |

**API:**

- **start()**: No-op (ready after construction).
- **stop()**: Waits for all pending tasks, clears task set, shuts down the thread pool.

---

## The @async_method Decorator

`@async_method` marks a method to execute asynchronously via a
`TaskExecutorPort`. The caller returns immediately -- the actual execution is
offloaded to the executor:

```python
from pyfly.scheduling import async_method

class NotificationService:
    @async_method
    async def send_email(self, to: str, subject: str, body: str):
        """This runs asynchronously -- caller does not wait."""
        await self.email_client.send(to, subject, body)
```

Under the hood, `@async_method` sets `__pyfly_async__ = True` on the function.
The framework picks this up and routes the call through the configured
`TaskExecutorPort`.

---

## Configuration

Scheduling behavior can be configured in `pyfly.yaml`:

```yaml
pyfly:
  scheduling:
    enabled: true
    thread-pool:
      max-workers: 4
```

| Key | Description | Default |
|---|---|---|
| `pyfly.scheduling.enabled` | Enable or disable the scheduling subsystem | `true` |
| `pyfly.scheduling.thread-pool.max-workers` | Max threads for `ThreadPoolTaskExecutor` | `4` |

When `enabled` is `false`, the `TaskScheduler` will not start any loops and
`@scheduled` methods will be ignored.

**Requires:** `pip install pyfly[scheduling]` (installs `croniter` for cron
expression parsing)

---

## Complete Example

Below is a full example that demonstrates all three trigger types working
together in a single application: a periodic data sync (fixed delay), a
cron-based nightly cleanup, and a fixed-rate health heartbeat.

```python
from datetime import timedelta

from pyfly.container import service
from pyfly.context import post_construct, pre_destroy
from pyfly.scheduling import (
    AsyncIOTaskExecutor,
    CronExpression,
    TaskScheduler,
    scheduled,
)


@service
class DataSyncService:
    """Pulls data from an upstream API with a guaranteed gap between runs."""

    @scheduled(fixed_delay=timedelta(minutes=5))
    async def sync_upstream(self):
        print("Starting data sync...")
        # Simulate work
        import asyncio
        await asyncio.sleep(2)
        print("Data sync complete.")


@service
class CleanupService:
    """Purges stale records every night at 02:00."""

    @scheduled(cron="0 2 * * *")
    async def purge_stale_records(self):
        print("Running nightly cleanup...")
        # Delete records older than 90 days
        await self.repository.delete_older_than(days=90)
        print("Cleanup done.")


@service
class HealthMonitor:
    """Publishes a heartbeat every 10 seconds, starting after a 5-second delay."""

    @scheduled(fixed_rate=timedelta(seconds=10), initial_delay=timedelta(seconds=5))
    async def heartbeat(self):
        print("Heartbeat: OK")


@service
class SchedulerManager:
    """Manages the lifecycle of the TaskScheduler."""

    def __init__(
        self,
        sync_service: DataSyncService,
        cleanup_service: CleanupService,
        health_monitor: HealthMonitor,
    ):
        self._scheduler = TaskScheduler()  # Uses AsyncIOTaskExecutor by default
        self._beans = [sync_service, cleanup_service, health_monitor]

    @post_construct
    async def start(self):
        count = self._scheduler.discover(self._beans)
        print(f"Discovered {count} scheduled tasks")
        await self._scheduler.start()

    @pre_destroy
    async def stop(self):
        await self._scheduler.stop()
        print("Scheduler stopped.")
```

### Using CronExpression Standalone

You can also use `CronExpression` independently for any cron-related
calculation:

```python
from datetime import datetime
from pyfly.scheduling import CronExpression

# When is the next weekday at 09:00?
cron = CronExpression("0 9 * * 1-5")
print(f"Next working-day start: {cron.next_fire_time()}")
print(f"Seconds to wait: {cron.seconds_until_next():.0f}")

# Show the next 5 fire times
for t in cron.next_n_fire_times(5):
    print(f"  {t}")

# What was the last fire time?
print(f"Previous fire: {cron.previous_fire_time()}")
```

### Custom Executor

Implementing a custom executor is straightforward -- just satisfy the
`TaskExecutorPort` protocol:

```python
import asyncio
import logging
from typing import Any, Coroutine, TypeVar

from pyfly.scheduling import TaskExecutorPort

T = TypeVar("T")
logger = logging.getLogger(__name__)


class LoggingTaskExecutor:
    """Custom executor that logs every task submission."""

    def __init__(self):
        self._tasks: set[asyncio.Task[Any]] = set()

    async def submit(self, coro: Coroutine[Any, Any, T]) -> asyncio.Task[T]:
        logger.info("Submitting task: %s", coro.__qualname__)
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def start(self) -> None:
        pass  # Ready after construction

    async def stop(self) -> None:
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()


# Use it with the scheduler
scheduler = TaskScheduler(executor=LoggingTaskExecutor())
```

This architecture makes it easy to plug in metrics collection, distributed
execution, or any other cross-cutting concern without modifying your scheduled
tasks.

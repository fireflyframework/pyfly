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
"""PyFly Scheduling — periodic task execution with cron, fixed-rate, and fixed-delay modes.

Framework-agnostic types (ports, decorators, cron) are exported directly.
Default adapter (AsyncIO) exports are re-exported for convenience.
"""

# Framework-agnostic exports
from pyfly.scheduling.cron import CronExpression
from pyfly.scheduling.decorators import async_method, scheduled
from pyfly.scheduling.ports.outbound import TaskExecutorPort
from pyfly.scheduling.task_scheduler import TaskScheduler

# Default adapter re-exports
from pyfly.scheduling.adapters.asyncio_executor import AsyncIOTaskExecutor
from pyfly.scheduling.adapters.thread_executor import ThreadPoolTaskExecutor

__all__ = [
    # Framework-agnostic
    "CronExpression",
    "TaskExecutorPort",
    "TaskScheduler",
    "async_method",
    "scheduled",
    # Adapters
    "AsyncIOTaskExecutor",
    "ThreadPoolTaskExecutor",
]

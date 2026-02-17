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
"""Transactional engine auto-configuration — wires all transactional beans into the DI container.

Creates beans for:

* Configuration properties (saga, TCC, backpressure)
* Default persistence and observability adapters
* Saga engine components (resolver, invoker, compensator, orchestrator, engine, registry)
* TCC engine components (resolver, invoker, orchestrator, engine, registry)
* Recovery service
"""

from __future__ import annotations

import logging

from pyfly.container.bean import bean
from pyfly.context.conditions import auto_configuration, conditional_on_property
from pyfly.transactional.saga.config.properties import (
    BackpressureProperties,
    SagaEngineProperties,
)
from pyfly.transactional.saga.engine.argument_resolver import ArgumentResolver
from pyfly.transactional.saga.engine.compensator import SagaCompensator
from pyfly.transactional.saga.engine.execution_orchestrator import (
    SagaExecutionOrchestrator,
)
from pyfly.transactional.saga.engine.saga_engine import SagaEngine
from pyfly.transactional.saga.engine.step_invoker import StepInvoker
from pyfly.transactional.saga.persistence.recovery import SagaRecoveryService
from pyfly.transactional.saga.registry.saga_registry import SagaRegistry
from pyfly.transactional.shared.observability.events import LoggerEventsAdapter
from pyfly.transactional.shared.persistence.memory import InMemoryPersistenceAdapter
from pyfly.transactional.tcc.config.properties import TccEngineProperties
from pyfly.transactional.tcc.engine.argument_resolver import TccArgumentResolver
from pyfly.transactional.tcc.engine.execution_orchestrator import (
    TccExecutionOrchestrator,
)
from pyfly.transactional.tcc.engine.participant_invoker import TccParticipantInvoker
from pyfly.transactional.tcc.engine.tcc_engine import TccEngine
from pyfly.transactional.tcc.registry.tcc_registry import TccRegistry

_logger = logging.getLogger(__name__)


@auto_configuration
@conditional_on_property("pyfly.transactional.enabled", having_value="true")
class TransactionalEngineAutoConfiguration:
    """Auto-configures the transactional engine subsystem.

    Creates the following beans:

    * :class:`SagaEngineProperties`
    * :class:`TccEngineProperties`
    * :class:`BackpressureProperties`
    * :class:`InMemoryPersistenceAdapter` — default persistence (when no external store is configured)
    * :class:`LoggerEventsAdapter` — default events adapter
    * :class:`ArgumentResolver` — saga argument resolver
    * :class:`StepInvoker` — saga step invoker
    * :class:`SagaCompensator` — saga compensator
    * :class:`SagaExecutionOrchestrator` — saga execution orchestrator
    * :class:`SagaEngine` — main saga engine
    * :class:`SagaRegistry` — saga registry
    * :class:`TccRegistry` — TCC registry
    * :class:`TccEngine` — TCC engine (with its own invoker and orchestrator)
    * :class:`SagaRecoveryService` — recovery service
    """

    # -- Configuration properties -------------------------------------------

    @bean
    def saga_engine_properties(self) -> SagaEngineProperties:
        return SagaEngineProperties()

    @bean
    def tcc_engine_properties(self) -> TccEngineProperties:
        return TccEngineProperties()

    @bean
    def backpressure_properties(self) -> BackpressureProperties:
        return BackpressureProperties()

    # -- Default infrastructure adapters ------------------------------------

    @bean
    def in_memory_persistence_adapter(self) -> InMemoryPersistenceAdapter:
        return InMemoryPersistenceAdapter()

    @bean
    def logger_events_adapter(self) -> LoggerEventsAdapter:
        return LoggerEventsAdapter()

    # -- Saga engine components ---------------------------------------------

    @bean
    def saga_argument_resolver(self) -> ArgumentResolver:
        return ArgumentResolver()

    @bean
    def saga_step_invoker(
        self,
        argument_resolver: ArgumentResolver,
    ) -> StepInvoker:
        return StepInvoker(argument_resolver=argument_resolver)

    @bean
    def saga_compensator(
        self,
        step_invoker: StepInvoker,
        events_adapter: LoggerEventsAdapter,
    ) -> SagaCompensator:
        return SagaCompensator(
            step_invoker=step_invoker,
            events_port=events_adapter,
        )

    @bean
    def saga_execution_orchestrator(
        self,
        step_invoker: StepInvoker,
        events_adapter: LoggerEventsAdapter,
    ) -> SagaExecutionOrchestrator:
        return SagaExecutionOrchestrator(
            step_invoker=step_invoker,
            events_port=events_adapter,
        )

    @bean
    def saga_registry(self) -> SagaRegistry:
        return SagaRegistry()

    @bean
    def saga_engine(
        self,
        registry: SagaRegistry,
        step_invoker: StepInvoker,
        execution_orchestrator: SagaExecutionOrchestrator,
        compensator: SagaCompensator,
        persistence_adapter: InMemoryPersistenceAdapter,
        events_adapter: LoggerEventsAdapter,
    ) -> SagaEngine:
        return SagaEngine(
            registry=registry,
            step_invoker=step_invoker,
            execution_orchestrator=execution_orchestrator,
            compensator=compensator,
            persistence_port=persistence_adapter,
            events_port=events_adapter,
        )

    # -- TCC engine components ----------------------------------------------

    @bean
    def tcc_registry(self) -> TccRegistry:
        return TccRegistry()

    @bean
    def tcc_engine(
        self,
        tcc_registry: TccRegistry,
        persistence_adapter: InMemoryPersistenceAdapter,
        events_adapter: LoggerEventsAdapter,
    ) -> TccEngine:
        tcc_argument_resolver = TccArgumentResolver()
        tcc_invoker = TccParticipantInvoker(argument_resolver=tcc_argument_resolver)
        tcc_orchestrator = TccExecutionOrchestrator(participant_invoker=tcc_invoker)

        return TccEngine(
            registry=tcc_registry,
            participant_invoker=tcc_invoker,
            orchestrator=tcc_orchestrator,
            persistence_port=persistence_adapter,
            events_port=events_adapter,
        )

    # -- Recovery service ---------------------------------------------------

    @bean
    def saga_recovery_service(
        self,
        persistence_adapter: InMemoryPersistenceAdapter,
        saga_engine: SagaEngine,
        events_adapter: LoggerEventsAdapter,
    ) -> SagaRecoveryService:
        return SagaRecoveryService(
            persistence_port=persistence_adapter,
            saga_engine=saga_engine,
            events_port=events_adapter,
        )

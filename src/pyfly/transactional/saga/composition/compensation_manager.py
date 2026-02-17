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
"""Manages cross-saga compensation within a composition."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyfly.transactional.saga.composition.composition import SagaComposition
    from pyfly.transactional.saga.composition.composition_context import (
        CompositionContext,
    )

logger = logging.getLogger(__name__)


class CompensationManager:
    """Compensates successfully completed sagas after a composition failure.

    Compensation is executed in reverse completion order so that the most
    recently completed saga is compensated first.  This is a placeholder
    implementation that records compensation intent in the composition
    context; a full implementation would delegate back to the saga engine
    to re-execute each saga's built-in compensation.
    """

    async def compensate_completed(
        self,
        completed_sagas: list[str],
        composition: SagaComposition,
        ctx: CompositionContext,
        saga_engine: Any,
    ) -> None:
        """Compensate completed sagas in reverse order.

        Parameters
        ----------
        completed_sagas:
            Names of sagas that completed successfully and need to be
            compensated.
        composition:
            The composition definition (for policy look-up).
        ctx:
            The mutable composition context where compensation status is
            recorded.
        saga_engine:
            The saga engine (or mock) used to trigger compensation.  The
            current placeholder only records the intent.
        """
        if not completed_sagas:
            return

        # Reverse order: last completed should be compensated first.
        for saga_name in reversed(completed_sagas):
            logger.info(
                "Compensating saga '%s' in composition '%s' (correlation_id=%s)",
                saga_name,
                composition.name,
                ctx.correlation_id,
            )
            ctx.compensated_sagas.append(saga_name)

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
"""Tests for TCC annotations — @tcc, @tcc_participant, @try_method, @confirm_method, @cancel_method."""

from __future__ import annotations

import dataclasses

import pytest

from pyfly.transactional.tcc.annotations import (
    FromTry,
    cancel_method,
    confirm_method,
    tcc,
    tcc_participant,
    try_method,
)


# ---------------------------------------------------------------------------
# @tcc
# ---------------------------------------------------------------------------


class TestTccDecorator:
    def test_sets_pyfly_tcc_metadata(self) -> None:
        @tcc(name="order-payment")
        class OrderPaymentTcc:
            pass

        assert hasattr(OrderPaymentTcc, "__pyfly_tcc__")
        assert OrderPaymentTcc.__pyfly_tcc__["name"] == "order-payment"

    def test_stores_all_custom_fields(self) -> None:
        @tcc(
            name="order-payment",
            timeout_ms=30000,
            retry_enabled=True,
            max_retries=3,
            backoff_ms=1000,
        )
        class FullTcc:
            pass

        meta = FullTcc.__pyfly_tcc__
        assert meta["name"] == "order-payment"
        assert meta["timeout_ms"] == 30000
        assert meta["retry_enabled"] is True
        assert meta["max_retries"] == 3
        assert meta["backoff_ms"] == 1000

    def test_defaults_timeout_ms_to_zero(self) -> None:
        @tcc(name="default-tcc")
        class DefaultTcc:
            pass

        assert DefaultTcc.__pyfly_tcc__["timeout_ms"] == 0

    def test_defaults_retry_enabled_to_false(self) -> None:
        @tcc(name="default-tcc")
        class DefaultTcc:
            pass

        assert DefaultTcc.__pyfly_tcc__["retry_enabled"] is False

    def test_defaults_max_retries_to_zero(self) -> None:
        @tcc(name="default-tcc")
        class DefaultTcc:
            pass

        assert DefaultTcc.__pyfly_tcc__["max_retries"] == 0

    def test_defaults_backoff_ms_to_zero(self) -> None:
        @tcc(name="default-tcc")
        class DefaultTcc:
            pass

        assert DefaultTcc.__pyfly_tcc__["backoff_ms"] == 0

    def test_returns_same_class(self) -> None:
        class OriginalTcc:
            pass

        decorated = tcc(name="test")(OriginalTcc)
        assert decorated is OriginalTcc

    def test_metadata_dict_has_expected_keys(self) -> None:
        @tcc(name="my-tcc")
        class MyTcc:
            pass

        assert set(MyTcc.__pyfly_tcc__.keys()) == {
            "name",
            "timeout_ms",
            "retry_enabled",
            "max_retries",
            "backoff_ms",
        }


# ---------------------------------------------------------------------------
# @tcc_participant
# ---------------------------------------------------------------------------


class TestTccParticipantDecorator:
    def test_sets_pyfly_tcc_participant_metadata(self) -> None:
        @tcc_participant(id="payment-service")
        class PaymentParticipant:
            pass

        assert hasattr(PaymentParticipant, "__pyfly_tcc_participant__")
        assert PaymentParticipant.__pyfly_tcc_participant__["id"] == "payment-service"

    def test_stores_all_custom_fields(self) -> None:
        @tcc_participant(id="payment-service", order=1, timeout_ms=5000, optional=True)
        class FullParticipant:
            pass

        meta = FullParticipant.__pyfly_tcc_participant__
        assert meta["id"] == "payment-service"
        assert meta["order"] == 1
        assert meta["timeout_ms"] == 5000
        assert meta["optional"] is True

    def test_defaults_order_to_zero(self) -> None:
        @tcc_participant(id="svc")
        class DefaultParticipant:
            pass

        assert DefaultParticipant.__pyfly_tcc_participant__["order"] == 0

    def test_defaults_timeout_ms_to_zero(self) -> None:
        @tcc_participant(id="svc")
        class DefaultParticipant:
            pass

        assert DefaultParticipant.__pyfly_tcc_participant__["timeout_ms"] == 0

    def test_defaults_optional_to_false(self) -> None:
        @tcc_participant(id="svc")
        class DefaultParticipant:
            pass

        assert DefaultParticipant.__pyfly_tcc_participant__["optional"] is False

    def test_returns_same_class(self) -> None:
        class OriginalParticipant:
            pass

        decorated = tcc_participant(id="svc")(OriginalParticipant)
        assert decorated is OriginalParticipant

    def test_metadata_dict_has_expected_keys(self) -> None:
        @tcc_participant(id="svc")
        class Participant:
            pass

        assert set(Participant.__pyfly_tcc_participant__.keys()) == {
            "id",
            "order",
            "timeout_ms",
            "optional",
        }


# ---------------------------------------------------------------------------
# @try_method
# ---------------------------------------------------------------------------


class TestTryMethodDecorator:
    def test_sets_pyfly_try_method_metadata(self) -> None:
        @try_method()
        async def try_reserve(self, request, ctx) -> str:
            return "reserved"

        assert hasattr(try_reserve, "__pyfly_try_method__")

    def test_stores_all_custom_fields(self) -> None:
        @try_method(timeout_ms=5000, retry=2, backoff_ms=100)
        async def try_reserve(self, request, ctx) -> str:
            return "reserved"

        meta = try_reserve.__pyfly_try_method__
        assert meta["timeout_ms"] == 5000
        assert meta["retry"] == 2
        assert meta["backoff_ms"] == 100

    def test_defaults_timeout_ms_to_zero(self) -> None:
        @try_method()
        async def try_default(self) -> None:
            pass

        assert try_default.__pyfly_try_method__["timeout_ms"] == 0

    def test_defaults_retry_to_zero(self) -> None:
        @try_method()
        async def try_default(self) -> None:
            pass

        assert try_default.__pyfly_try_method__["retry"] == 0

    def test_defaults_backoff_ms_to_zero(self) -> None:
        @try_method()
        async def try_default(self) -> None:
            pass

        assert try_default.__pyfly_try_method__["backoff_ms"] == 0

    def test_preserves_function_name(self) -> None:
        @try_method()
        async def try_reserve() -> str:
            return "reserved"

        assert try_reserve.__name__ == "try_reserve"

    def test_preserves_function_docstring(self) -> None:
        @try_method()
        async def try_reserve() -> str:
            """Reserve resources."""
            return "reserved"

        assert try_reserve.__doc__ == "Reserve resources."

    def test_preserves_async_function_behavior(self) -> None:
        import asyncio

        @try_method(timeout_ms=1000)
        async def try_add(a: int, b: int) -> int:
            return a + b

        result = asyncio.get_event_loop().run_until_complete(try_add(2, 3))
        assert result == 5

    def test_preserves_sync_function_behavior(self) -> None:
        @try_method()
        def try_multiply(a: int, b: int) -> int:
            return a * b

        assert try_multiply(4, 5) == 20

    def test_metadata_dict_has_expected_keys(self) -> None:
        @try_method()
        async def try_fn() -> None:
            pass

        assert set(try_fn.__pyfly_try_method__.keys()) == {
            "timeout_ms",
            "retry",
            "backoff_ms",
        }


# ---------------------------------------------------------------------------
# @confirm_method
# ---------------------------------------------------------------------------


class TestConfirmMethodDecorator:
    def test_sets_pyfly_confirm_method_metadata(self) -> None:
        @confirm_method()
        async def confirm(self, reservation_id, ctx) -> None:
            pass

        assert hasattr(confirm, "__pyfly_confirm_method__")

    def test_stores_all_custom_fields(self) -> None:
        @confirm_method(timeout_ms=10000, retry=3, backoff_ms=200)
        async def confirm(self, reservation_id, ctx) -> None:
            pass

        meta = confirm.__pyfly_confirm_method__
        assert meta["timeout_ms"] == 10000
        assert meta["retry"] == 3
        assert meta["backoff_ms"] == 200

    def test_defaults_timeout_ms_to_zero(self) -> None:
        @confirm_method()
        async def confirm_default(self) -> None:
            pass

        assert confirm_default.__pyfly_confirm_method__["timeout_ms"] == 0

    def test_defaults_retry_to_zero(self) -> None:
        @confirm_method()
        async def confirm_default(self) -> None:
            pass

        assert confirm_default.__pyfly_confirm_method__["retry"] == 0

    def test_defaults_backoff_ms_to_zero(self) -> None:
        @confirm_method()
        async def confirm_default(self) -> None:
            pass

        assert confirm_default.__pyfly_confirm_method__["backoff_ms"] == 0

    def test_preserves_function_name(self) -> None:
        @confirm_method()
        async def confirm_payment() -> None:
            pass

        assert confirm_payment.__name__ == "confirm_payment"

    def test_preserves_function_docstring(self) -> None:
        @confirm_method()
        async def confirm_payment() -> None:
            """Confirm the payment."""
            pass

        assert confirm_payment.__doc__ == "Confirm the payment."

    def test_preserves_async_function_behavior(self) -> None:
        import asyncio

        @confirm_method(timeout_ms=5000)
        async def confirm_add(a: int, b: int) -> int:
            return a + b

        result = asyncio.get_event_loop().run_until_complete(confirm_add(10, 20))
        assert result == 30

    def test_preserves_sync_function_behavior(self) -> None:
        @confirm_method()
        def confirm_multiply(a: int, b: int) -> int:
            return a * b

        assert confirm_multiply(6, 7) == 42

    def test_metadata_dict_has_expected_keys(self) -> None:
        @confirm_method()
        async def confirm_fn() -> None:
            pass

        assert set(confirm_fn.__pyfly_confirm_method__.keys()) == {
            "timeout_ms",
            "retry",
            "backoff_ms",
        }


# ---------------------------------------------------------------------------
# @cancel_method
# ---------------------------------------------------------------------------


class TestCancelMethodDecorator:
    def test_sets_pyfly_cancel_method_metadata(self) -> None:
        @cancel_method()
        async def cancel(self, reservation_id) -> None:
            pass

        assert hasattr(cancel, "__pyfly_cancel_method__")

    def test_stores_all_custom_fields(self) -> None:
        @cancel_method(timeout_ms=5000, retry=1, backoff_ms=50)
        async def cancel(self, reservation_id) -> None:
            pass

        meta = cancel.__pyfly_cancel_method__
        assert meta["timeout_ms"] == 5000
        assert meta["retry"] == 1
        assert meta["backoff_ms"] == 50

    def test_defaults_timeout_ms_to_zero(self) -> None:
        @cancel_method()
        async def cancel_default(self) -> None:
            pass

        assert cancel_default.__pyfly_cancel_method__["timeout_ms"] == 0

    def test_defaults_retry_to_zero(self) -> None:
        @cancel_method()
        async def cancel_default(self) -> None:
            pass

        assert cancel_default.__pyfly_cancel_method__["retry"] == 0

    def test_defaults_backoff_ms_to_zero(self) -> None:
        @cancel_method()
        async def cancel_default(self) -> None:
            pass

        assert cancel_default.__pyfly_cancel_method__["backoff_ms"] == 0

    def test_preserves_function_name(self) -> None:
        @cancel_method()
        async def cancel_payment() -> None:
            pass

        assert cancel_payment.__name__ == "cancel_payment"

    def test_preserves_function_docstring(self) -> None:
        @cancel_method()
        async def cancel_payment() -> None:
            """Cancel the payment."""
            pass

        assert cancel_payment.__doc__ == "Cancel the payment."

    def test_preserves_async_function_behavior(self) -> None:
        import asyncio

        @cancel_method(timeout_ms=3000)
        async def cancel_sub(a: int, b: int) -> int:
            return a - b

        result = asyncio.get_event_loop().run_until_complete(cancel_sub(10, 3))
        assert result == 7

    def test_preserves_sync_function_behavior(self) -> None:
        @cancel_method()
        def cancel_divide(a: int, b: int) -> float:
            return a / b

        assert cancel_divide(10, 2) == 5.0

    def test_metadata_dict_has_expected_keys(self) -> None:
        @cancel_method()
        async def cancel_fn() -> None:
            pass

        assert set(cancel_fn.__pyfly_cancel_method__.keys()) == {
            "timeout_ms",
            "retry",
            "backoff_ms",
        }


# ---------------------------------------------------------------------------
# FromTry marker
# ---------------------------------------------------------------------------


class TestFromTryMarker:
    def test_exists(self) -> None:
        assert FromTry is not None

    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(FromTry)

    def test_is_frozen(self) -> None:
        marker = FromTry()
        with pytest.raises((AttributeError, TypeError)):
            marker.x = "y"  # type: ignore[attr-defined]

    def test_has_no_fields(self) -> None:
        fields = dataclasses.fields(FromTry)
        assert len(fields) == 0

    def test_instantiation(self) -> None:
        marker = FromTry()
        assert isinstance(marker, FromTry)


# ---------------------------------------------------------------------------
# Integration: full decorated TCC
# ---------------------------------------------------------------------------


class TestFullDecoratedTcc:
    """Verify the complete example from the task description works correctly."""

    def test_full_tcc_structure(self) -> None:
        @tcc(
            name="order-payment",
            timeout_ms=30000,
            retry_enabled=True,
            max_retries=3,
            backoff_ms=1000,
        )
        class OrderPaymentTcc:
            @tcc_participant(
                id="payment-service", order=1, timeout_ms=-1, optional=False
            )
            class PaymentParticipant:
                @try_method(timeout_ms=5000, retry=2, backoff_ms=100)
                async def try_reserve(self, request, ctx) -> str:
                    return "reserved"

                @confirm_method(timeout_ms=10000, retry=3)
                async def confirm(self, reservation_id, ctx) -> None:
                    pass

                @cancel_method(timeout_ms=5000, retry=1)
                async def cancel(self, reservation_id) -> None:
                    pass

        # TCC-level metadata
        assert OrderPaymentTcc.__pyfly_tcc__["name"] == "order-payment"
        assert OrderPaymentTcc.__pyfly_tcc__["timeout_ms"] == 30000
        assert OrderPaymentTcc.__pyfly_tcc__["retry_enabled"] is True
        assert OrderPaymentTcc.__pyfly_tcc__["max_retries"] == 3
        assert OrderPaymentTcc.__pyfly_tcc__["backoff_ms"] == 1000

        # Participant-level metadata
        participant = OrderPaymentTcc.PaymentParticipant
        assert participant.__pyfly_tcc_participant__["id"] == "payment-service"
        assert participant.__pyfly_tcc_participant__["order"] == 1
        assert participant.__pyfly_tcc_participant__["timeout_ms"] == -1
        assert participant.__pyfly_tcc_participant__["optional"] is False

        # Method-level metadata
        inst = participant()
        assert inst.try_reserve.__func__.__pyfly_try_method__["timeout_ms"] == 5000
        assert inst.try_reserve.__func__.__pyfly_try_method__["retry"] == 2
        assert inst.try_reserve.__func__.__pyfly_try_method__["backoff_ms"] == 100

        assert inst.confirm.__func__.__pyfly_confirm_method__["timeout_ms"] == 10000
        assert inst.confirm.__func__.__pyfly_confirm_method__["retry"] == 3
        assert inst.confirm.__func__.__pyfly_confirm_method__["backoff_ms"] == 0

        assert inst.cancel.__func__.__pyfly_cancel_method__["timeout_ms"] == 5000
        assert inst.cancel.__func__.__pyfly_cancel_method__["retry"] == 1
        assert inst.cancel.__func__.__pyfly_cancel_method__["backoff_ms"] == 0

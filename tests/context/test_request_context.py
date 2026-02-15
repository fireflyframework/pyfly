"""Tests for RequestContext — request-scoped context backed by contextvars."""

import asyncio
import uuid

import pytest

from pyfly.context.request_context import RequestContext


class TestRequestContext:
    """Unit tests for RequestContext lifecycle and isolation."""

    def test_current_returns_none_outside_request(self):
        assert RequestContext.current() is None

    def test_init_and_current(self):
        ctx = RequestContext.init()
        assert ctx is not None
        assert RequestContext.current() is ctx
        assert isinstance(ctx.request_id, str)
        assert len(ctx.request_id) > 0
        RequestContext.clear()

    def test_clear_resets_to_none(self):
        RequestContext.init()
        RequestContext.clear()
        assert RequestContext.current() is None

    def test_custom_request_id(self):
        rid = str(uuid.uuid4())
        ctx = RequestContext.init(request_id=rid)
        assert ctx.request_id == rid
        RequestContext.clear()

    def test_attributes_get_set(self):
        ctx = RequestContext.init()
        ctx.set("tenant_id", "acme")
        assert ctx.get("tenant_id") == "acme"
        assert ctx.get("missing") is None
        assert ctx.get("missing", "default") == "default"
        RequestContext.clear()

    def test_security_context_default_none(self):
        ctx = RequestContext.init()
        assert ctx.security_context is None
        RequestContext.clear()

    def test_security_context_set(self):
        from pyfly.security.context import SecurityContext

        ctx = RequestContext.init()
        sc = SecurityContext(user_id="user1", roles=["ADMIN"])
        ctx.security_context = sc
        assert ctx.security_context.user_id == "user1"
        RequestContext.clear()

    @pytest.mark.asyncio
    async def test_isolation_between_tasks(self):
        """Each asyncio task gets its own context (contextvars copy-on-create)."""
        results = {}

        async def worker(name: str):
            ctx = RequestContext.init()
            ctx.set("worker", name)
            await asyncio.sleep(0.01)
            results[name] = RequestContext.current().get("worker")
            RequestContext.clear()

        await asyncio.gather(worker("a"), worker("b"))
        assert results["a"] == "a"
        assert results["b"] == "b"

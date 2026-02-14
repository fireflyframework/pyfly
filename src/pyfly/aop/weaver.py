"""AOP weaver — wraps bean methods with matching advice chains."""

from __future__ import annotations

import functools
import inspect
from typing import Any

from pyfly.aop.registry import AspectRegistry
from pyfly.aop.types import JoinPoint


def weave_bean(bean: Any, qualified_prefix: str, registry: AspectRegistry) -> None:
    """Weave advice into public methods of *bean*.

    For each public method (name not starting with ``_``), build a qualified
    name ``f"{qualified_prefix}.{method_name}"`` and ask the *registry* for
    matching bindings.  If any bindings match, replace the method on the
    instance with a wrapper that executes the advice chain.

    Async methods support all advice types including ``@around``.
    Sync methods support ``@before``, ``@after_returning``, ``@after_throwing``,
    and ``@after`` (no ``@around``).
    """
    for attr_name in dir(bean):
        if attr_name.startswith("_"):
            continue

        attr = getattr(bean, attr_name, None)
        if attr is None or not callable(attr):
            continue

        qualified_name = f"{qualified_prefix}.{attr_name}"
        bindings = registry.get_matching(qualified_name)
        if not bindings:
            continue

        # Group bindings by advice type
        before_bindings = [b for b in bindings if b.advice_type == "before"]
        after_returning_bindings = [b for b in bindings if b.advice_type == "after_returning"]
        after_throwing_bindings = [b for b in bindings if b.advice_type == "after_throwing"]
        after_bindings = [b for b in bindings if b.advice_type == "after"]
        around_bindings = [b for b in bindings if b.advice_type == "around"]

        original = attr

        if inspect.iscoroutinefunction(original):
            wrapper = _build_async_wrapper(
                bean,
                attr_name,
                original,
                before_bindings,
                after_returning_bindings,
                after_throwing_bindings,
                after_bindings,
                around_bindings,
            )
        else:
            wrapper = _build_sync_wrapper(
                bean,
                attr_name,
                original,
                before_bindings,
                after_returning_bindings,
                after_throwing_bindings,
                after_bindings,
            )

        # Replace the method on the instance
        setattr(bean, attr_name, wrapper)


def _build_async_wrapper(
    bean: Any,
    method_name: str,
    original: Any,
    before_bindings: list,
    after_returning_bindings: list,
    after_throwing_bindings: list,
    after_bindings: list,
    around_bindings: list,
) -> Any:
    """Build an async wrapper that applies the advice chain."""

    @functools.wraps(original)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        jp = JoinPoint(
            target=bean,
            method_name=method_name,
            args=args,
            kwargs=kwargs,
        )

        # 1. Run @before advice (sync)
        for binding in before_bindings:
            binding.handler(jp)

        try:
            # 2. Execute the method (with or without @around)
            if around_bindings:
                # Set proceed to call the original async method
                async def _proceed(*a: Any, **kw: Any) -> Any:
                    call_args = a if a else jp.args
                    call_kwargs = kw if kw else jp.kwargs
                    return await original(*call_args, **call_kwargs)

                jp.proceed = _proceed
                # Call the first around handler (it may be async)
                result = around_bindings[0].handler(jp)
                if inspect.isawaitable(result):
                    result = await result
            else:
                result = await original(*args, **kwargs)

            # 3. On success: set return_value, run @after_returning
            jp.return_value = result
            for binding in after_returning_bindings:
                binding.handler(jp)

            return result

        except Exception as exc:
            # 4. On exception: set exception, run @after_throwing, re-raise
            jp.exception = exc
            for binding in after_throwing_bindings:
                binding.handler(jp)
            raise

        finally:
            # 5. Run @after (always)
            for binding in after_bindings:
                binding.handler(jp)

    return wrapper


def _build_sync_wrapper(
    bean: Any,
    method_name: str,
    original: Any,
    before_bindings: list,
    after_returning_bindings: list,
    after_throwing_bindings: list,
    after_bindings: list,
) -> Any:
    """Build a sync wrapper that applies the advice chain (no @around support)."""

    @functools.wraps(original)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        jp = JoinPoint(
            target=bean,
            method_name=method_name,
            args=args,
            kwargs=kwargs,
        )

        # 1. Run @before advice (sync)
        for binding in before_bindings:
            binding.handler(jp)

        try:
            # 2. Execute the original method
            result = original(*args, **kwargs)

            # 3. On success: set return_value, run @after_returning
            jp.return_value = result
            for binding in after_returning_bindings:
                binding.handler(jp)

            return result

        except Exception as exc:
            # 4. On exception: set exception, run @after_throwing, re-raise
            jp.exception = exc
            for binding in after_throwing_bindings:
                binding.handler(jp)
            raise

        finally:
            # 5. Run @after (always)
            for binding in after_bindings:
                binding.handler(jp)

    return wrapper

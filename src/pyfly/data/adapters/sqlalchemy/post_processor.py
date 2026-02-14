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
"""BeanPostProcessor that wires query methods onto Repository beans."""

from __future__ import annotations

from typing import Any

from pyfly.data.adapters.sqlalchemy.repository import Repository
from pyfly.data.query import QueryExecutor
from pyfly.data.query_parser import QueryMethodCompiler, QueryMethodParser

# Prefixes that indicate a derived query method.
_DERIVED_PREFIXES = ("find_by_", "count_by_", "exists_by_", "delete_by_")


class RepositoryBeanPostProcessor:
    """Replaces stub methods on :class:`Repository` subclasses with real query implementations.

    For each method decorated with ``@query``, compiles the annotated SQL/JPQL
    into an executable async callable.  For each derived query stub (methods
    starting with ``find_by_``, ``count_by_``, ``exists_by_``, or
    ``delete_by_``), parses the method name and compiles a corresponding
    SQLAlchemy query.
    """

    def __init__(self) -> None:
        self._query_executor = QueryExecutor()
        self._query_parser = QueryMethodParser()
        self._query_compiler = QueryMethodCompiler()

    def before_init(self, bean: Any, bean_name: str) -> Any:
        return bean

    def after_init(self, bean: Any, bean_name: str) -> Any:
        if not isinstance(bean, Repository):
            return bean

        entity = bean._model
        cls = type(bean)

        # Collect names defined on the base Repository class so we never
        # replace them.
        base_names = set(dir(Repository))

        for attr_name in list(vars(cls)):
            if attr_name.startswith("_"):
                continue

            attr = getattr(cls, attr_name, None)
            if attr is None or not callable(attr):
                continue

            # --- @query-decorated methods ---
            if hasattr(attr, "__pyfly_query__"):
                compiled_fn = self._query_executor.compile_query_method(attr, entity)
                wrapper = self._wrap_query_method(compiled_fn)
                setattr(bean, attr_name, wrapper.__get__(bean, cls))
                continue

            # --- Derived query methods ---
            if attr_name in base_names:
                continue

            if any(attr_name.startswith(prefix) for prefix in _DERIVED_PREFIXES):
                if self._is_stub(attr):
                    parsed = self._query_parser.parse(attr_name)
                    compiled_fn = self._query_compiler.compile(parsed, entity)
                    wrapper = self._wrap_derived_method(compiled_fn)
                    setattr(bean, attr_name, wrapper.__get__(bean, cls))

        return bean

    # ------------------------------------------------------------------
    # Wrapper factories
    # ------------------------------------------------------------------

    @staticmethod
    def _wrap_query_method(compiled_fn: Any) -> Any:
        """Wrap a ``@query``-compiled function to inject ``bean._session``."""

        async def wrapper(self_arg: Any, **kwargs: Any) -> Any:
            return await compiled_fn(self_arg._session, **kwargs)

        return wrapper

    @staticmethod
    def _wrap_derived_method(compiled_fn: Any) -> Any:
        """Wrap a derived-query-compiled function to inject ``bean._session``."""

        async def wrapper(self_arg: Any, *args: Any) -> Any:
            return await compiled_fn(self_arg._session, *args)

        return wrapper

    # ------------------------------------------------------------------
    # Stub detection
    # ------------------------------------------------------------------

    @staticmethod
    def _is_stub(method: Any) -> bool:
        """Return ``True`` if *method* appears to be a stub (body is ``...`` or ``pass``).

        A method is considered a stub when its code object contains no
        meaningful constants beyond ``None`` (which is the implicit return
        for ``pass`` bodies and ``...`` / ``Ellipsis`` stubs).
        """
        func = method
        # Unwrap staticmethod / classmethod / descriptors
        if isinstance(func, (staticmethod, classmethod)):
            func = func.__func__
        if hasattr(func, "__wrapped__"):
            func = func.__wrapped__

        code = getattr(func, "__code__", None)
        if code is None:
            return False

        # A stub function compiled from ``...`` or ``pass`` has
        # co_consts == (None,) — the implicit ``return None``.
        # Some versions of Python also include Ellipsis for ``...``.
        consts = set(code.co_consts)
        consts.discard(None)
        consts.discard(Ellipsis)

        # If nothing meaningful remains in the constants and there is
        # very little bytecode, treat as a stub.
        return len(consts) == 0 and code.co_code is not None

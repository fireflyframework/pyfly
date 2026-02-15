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
"""BeanPostProcessor that wires query methods onto MongoRepository beans."""

from __future__ import annotations

from typing import Any

from pyfly.data.document.mongodb.query_compiler import MongoQueryMethodCompiler
from pyfly.data.document.mongodb.repository import MongoRepository
from pyfly.data.query_parser import QueryMethodParser

# Prefixes that indicate a derived query method.
_DERIVED_PREFIXES = ("find_by_", "count_by_", "exists_by_", "delete_by_")


class MongoRepositoryBeanPostProcessor:
    """Replaces stub methods on :class:`MongoRepository` subclasses with real query implementations.

    For each derived query stub (methods starting with ``find_by_``,
    ``count_by_``, ``exists_by_``, or ``delete_by_``), parses the method
    name and compiles a corresponding MongoDB query.

    Mirrors :class:`~pyfly.data.relational.sqlalchemy.post_processor.RepositoryBeanPostProcessor`
    but targets MongoDB via Beanie ODM.
    """

    def __init__(self) -> None:
        self._query_parser = QueryMethodParser()
        self._query_compiler = MongoQueryMethodCompiler()

    def before_init(self, bean: Any, bean_name: str) -> Any:
        return bean

    def after_init(self, bean: Any, bean_name: str) -> Any:
        if not isinstance(bean, MongoRepository):
            return bean

        cls = type(bean)

        # Collect names defined on the base MongoRepository class so we never
        # replace them.
        base_names = set(dir(MongoRepository))

        for attr_name in list(vars(cls)):
            if attr_name.startswith("_"):
                continue

            attr = getattr(cls, attr_name, None)
            if attr is None or not callable(attr):
                continue

            # --- Derived query methods ---
            if attr_name in base_names:
                continue

            if any(attr_name.startswith(prefix) for prefix in _DERIVED_PREFIXES) and self._is_stub(attr):
                    parsed = self._query_parser.parse(attr_name)
                    compiled_fn = self._query_compiler.compile(parsed, bean._model)
                    wrapper = self._wrap_derived_method(compiled_fn)
                    setattr(bean, attr_name, wrapper.__get__(bean, cls))

        return bean

    # ------------------------------------------------------------------
    # Wrapper factories
    # ------------------------------------------------------------------

    @staticmethod
    def _wrap_derived_method(compiled_fn: Any) -> Any:
        """Wrap a derived-query-compiled function to inject ``bean._model``."""

        async def wrapper(self_arg: Any, *args: Any) -> Any:
            return await compiled_fn(self_arg._model, *args)

        return wrapper

    # ------------------------------------------------------------------
    # Stub detection
    # ------------------------------------------------------------------

    @staticmethod
    def _is_stub(method: Any) -> bool:
        """Return ``True`` if *method* appears to be a stub (body is ``...`` or ``pass``)."""
        func = method
        if isinstance(func, (staticmethod, classmethod)):
            func = func.__func__
        if hasattr(func, "__wrapped__"):
            func = func.__wrapped__

        code = getattr(func, "__code__", None)
        if code is None:
            return False

        consts = set(code.co_consts)
        consts.discard(None)
        consts.discard(Ellipsis)

        return len(consts) == 0 and code.co_code is not None

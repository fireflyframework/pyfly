"""BeanPostProcessor — hooks into bean creation lifecycle."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BeanPostProcessor(Protocol):
    """Hook into bean initialization.

    Implementations are called for every bean created by the ApplicationContext:
    - ``before_init``: called before @post_construct
    - ``after_init``: called after @post_construct
    """

    def before_init(self, bean: Any, bean_name: str) -> Any:
        """Called before @post_construct. May return a replacement bean."""
        ...

    def after_init(self, bean: Any, bean_name: str) -> Any:
        """Called after @post_construct. May return a replacement bean."""
        ...

"""Aspect-Oriented Programming support for PyFly."""

from pyfly.aop.decorators import after, after_returning, after_throwing, around, aspect, before
from pyfly.aop.pointcut import matches_pointcut
from pyfly.aop.post_processor import AspectBeanPostProcessor
from pyfly.aop.registry import AdviceBinding, AspectRegistry
from pyfly.aop.types import JoinPoint
from pyfly.aop.weaver import weave_bean

__all__ = [
    "AdviceBinding",
    "AspectBeanPostProcessor",
    "AspectRegistry",
    "JoinPoint",
    "after",
    "after_returning",
    "after_throwing",
    "around",
    "aspect",
    "before",
    "matches_pointcut",
    "weave_bean",
]

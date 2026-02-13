"""Tests for conditional bean decorators."""

from pyfly.context.conditions import (
    conditional_on_class,
    conditional_on_missing_bean,
    conditional_on_property,
)


class TestConditionalOnProperty:
    def test_marks_class(self):
        @conditional_on_property("cache.enabled", having_value="true")
        class MyBean:
            pass

        cond = MyBean.__pyfly_conditions__
        assert len(cond) == 1
        assert cond[0]["type"] == "on_property"
        assert cond[0]["key"] == "cache.enabled"
        assert cond[0]["having_value"] == "true"

    def test_stacks_with_other_conditions(self):
        @conditional_on_property("a", having_value="1")
        @conditional_on_property("b", having_value="2")
        class MyBean:
            pass

        cond = MyBean.__pyfly_conditions__
        assert len(cond) == 2


class TestConditionalOnClass:
    def test_marks_class(self):
        @conditional_on_class("json")
        class MyBean:
            pass

        cond = MyBean.__pyfly_conditions__
        assert len(cond) == 1
        assert cond[0]["type"] == "on_class"
        assert cond[0]["module_name"] == "json"

    def test_evaluates_available(self):
        @conditional_on_class("json")
        class MyBean:
            pass

        cond = MyBean.__pyfly_conditions__[0]
        assert cond["check"]() is True

    def test_evaluates_unavailable(self):
        @conditional_on_class("nonexistent_xyz_module_12345")
        class MyBean:
            pass

        cond = MyBean.__pyfly_conditions__[0]
        assert cond["check"]() is False


class TestConditionalOnMissingBean:
    def test_marks_class(self):
        class SomeInterface:
            pass

        @conditional_on_missing_bean(SomeInterface)
        class FallbackImpl:
            pass

        cond = FallbackImpl.__pyfly_conditions__
        assert len(cond) == 1
        assert cond[0]["type"] == "on_missing_bean"
        assert cond[0]["bean_type"] is SomeInterface

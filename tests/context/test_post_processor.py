"""Tests for BeanPostProcessor protocol."""

from pyfly.context.post_processor import BeanPostProcessor


class TestBeanPostProcessor:
    def test_protocol_is_structural(self):
        class MyProcessor:
            def before_init(self, bean, bean_name):
                return bean

            def after_init(self, bean, bean_name):
                return bean

        assert isinstance(MyProcessor(), BeanPostProcessor)

    def test_non_conforming_rejected(self):
        class NotAProcessor:
            pass

        assert not isinstance(NotAProcessor(), BeanPostProcessor)

    def test_processor_can_modify_bean(self):
        class WrapperProcessor:
            def before_init(self, bean, bean_name):
                return bean

            def after_init(self, bean, bean_name):
                bean._wrapped = True
                return bean

        class MyService:
            pass

        processor = WrapperProcessor()
        svc = MyService()
        result = processor.after_init(svc, "myService")
        assert result._wrapped is True

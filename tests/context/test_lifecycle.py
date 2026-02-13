"""Tests for @post_construct and @pre_destroy lifecycle annotations."""


from pyfly.context.lifecycle import post_construct, pre_destroy


class TestPostConstruct:
    def test_marks_method(self):
        class MyService:
            @post_construct
            async def init(self):
                pass

        assert MyService.init.__pyfly_post_construct__ is True

    def test_preserves_method(self):
        class MyService:
            @post_construct
            async def init(self):
                self.ready = True

        svc = MyService()
        assert callable(svc.init)


class TestPreDestroy:
    def test_marks_method(self):
        class MyService:
            @pre_destroy
            async def cleanup(self):
                pass

        assert MyService.cleanup.__pyfly_pre_destroy__ is True

    def test_preserves_method(self):
        class MyService:
            @pre_destroy
            async def cleanup(self):
                self.closed = True

        svc = MyService()
        assert callable(svc.cleanup)


class TestMultipleAnnotations:
    def test_class_can_have_both(self):
        class MyService:
            @post_construct
            async def start(self):
                pass

            @pre_destroy
            async def stop(self):
                pass

        assert MyService.start.__pyfly_post_construct__ is True
        assert MyService.stop.__pyfly_pre_destroy__ is True

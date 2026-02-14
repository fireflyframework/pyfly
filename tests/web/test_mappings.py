"""Tests for HTTP method mapping decorators."""

from pyfly.web.mappings import (
    delete_mapping,
    get_mapping,
    patch_mapping,
    post_mapping,
    put_mapping,
    request_mapping,
)


class TestRequestMapping:
    def test_class_level_path(self):
        @request_mapping("/api/orders")
        class MyController:
            pass

        assert getattr(MyController, "__pyfly_request_mapping__") == "/api/orders"

    def test_preserves_class(self):
        @request_mapping("/api")
        class MyController:
            """My docstring."""

        assert MyController.__name__ == "MyController"
        assert MyController.__doc__ == "My docstring."


class TestGetMapping:
    def test_marks_method(self):
        class Ctrl:
            @get_mapping("/{item_id}")
            async def get_item(self):
                pass

        meta = getattr(Ctrl.get_item, "__pyfly_mapping__")
        assert meta["method"] == "GET"
        assert meta["path"] == "/{item_id}"
        assert meta["status_code"] == 200

    def test_preserves_method(self):
        class Ctrl:
            @get_mapping("/")
            async def list_items(self):
                return []

        assert callable(Ctrl.list_items)


class TestPostMapping:
    def test_marks_method(self):
        class Ctrl:
            @post_mapping("/", status_code=201)
            async def create(self):
                pass

        meta = getattr(Ctrl.create, "__pyfly_mapping__")
        assert meta["method"] == "POST"
        assert meta["status_code"] == 201


class TestPutMapping:
    def test_marks_method(self):
        class Ctrl:
            @put_mapping("/{id}")
            async def update(self):
                pass

        meta = getattr(Ctrl.update, "__pyfly_mapping__")
        assert meta["method"] == "PUT"
        assert meta["path"] == "/{id}"


class TestPatchMapping:
    def test_marks_method(self):
        class Ctrl:
            @patch_mapping("/{id}")
            async def partial_update(self):
                pass

        meta = getattr(Ctrl.partial_update, "__pyfly_mapping__")
        assert meta["method"] == "PATCH"


class TestDeleteMapping:
    def test_marks_method(self):
        class Ctrl:
            @delete_mapping("/{id}", status_code=204)
            async def remove(self):
                pass

        meta = getattr(Ctrl.remove, "__pyfly_mapping__")
        assert meta["method"] == "DELETE"
        assert meta["status_code"] == 204


class TestDefaultStatusCodes:
    def test_get_default_200(self):
        class Ctrl:
            @get_mapping("/")
            async def get(self):
                pass

        assert getattr(Ctrl.get, "__pyfly_mapping__")["status_code"] == 200

    def test_post_default_200(self):
        class Ctrl:
            @post_mapping("/")
            async def create(self):
                pass

        assert getattr(Ctrl.create, "__pyfly_mapping__")["status_code"] == 200

    def test_delete_default_200(self):
        class Ctrl:
            @delete_mapping("/")
            async def remove(self):
                pass

        assert getattr(Ctrl.remove, "__pyfly_mapping__")["status_code"] == 200

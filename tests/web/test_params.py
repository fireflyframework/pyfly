"""Tests for request binding types."""

from typing import get_args, get_origin

from pyfly.web.params import Body, Cookie, Header, PathVar, QueryParam


class TestPathVar:
    def test_generic_type(self):
        hint = PathVar[str]
        assert get_origin(hint) is PathVar
        assert get_args(hint) == (str,)

    def test_int_type(self):
        hint = PathVar[int]
        assert get_origin(hint) is PathVar
        assert get_args(hint) == (int,)


class TestQueryParam:
    def test_generic_type(self):
        hint = QueryParam[int]
        assert get_origin(hint) is QueryParam
        assert get_args(hint) == (int,)

    def test_optional_type(self):
        hint = QueryParam[str | None]
        assert get_origin(hint) is QueryParam
        args = get_args(hint)
        assert len(args) == 1


class TestBody:
    def test_generic_type(self):
        from pydantic import BaseModel

        class MyModel(BaseModel):
            name: str

        hint = Body[MyModel]
        assert get_origin(hint) is Body
        assert get_args(hint) == (MyModel,)


class TestHeader:
    def test_generic_type(self):
        hint = Header[str]
        assert get_origin(hint) is Header
        assert get_args(hint) == (str,)


class TestCookie:
    def test_generic_type(self):
        hint = Cookie[str]
        assert get_origin(hint) is Cookie
        assert get_args(hint) == (str,)

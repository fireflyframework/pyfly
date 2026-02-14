"""Tests for return value handler."""

import pytest
from pydantic import BaseModel
from starlette.responses import HTMLResponse, JSONResponse, Response

from pyfly.web.response import handle_return_value


class ItemResponse(BaseModel):
    id: str
    name: str


class TestHandleReturnValue:
    def test_pydantic_model(self):
        item = ItemResponse(id="1", name="Widget")
        response = handle_return_value(item)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200

    def test_pydantic_model_custom_status(self):
        item = ItemResponse(id="1", name="Widget")
        response = handle_return_value(item, status_code=201)
        assert response.status_code == 201

    def test_dict(self):
        response = handle_return_value({"key": "value"})
        assert isinstance(response, JSONResponse)
        assert response.status_code == 200

    def test_none_returns_no_content(self):
        response = handle_return_value(None)
        assert response.status_code == 204

    def test_none_with_explicit_status(self):
        response = handle_return_value(None, status_code=202)
        assert response.status_code == 202

    def test_starlette_response_passthrough(self):
        html = HTMLResponse("<h1>Hello</h1>")
        response = handle_return_value(html)
        assert response is html

    def test_list(self):
        response = handle_return_value([1, 2, 3])
        assert isinstance(response, JSONResponse)

    def test_string(self):
        response = handle_return_value("hello")
        assert isinstance(response, JSONResponse)

"""Tests for OpenAPI 3.1 schema generator."""

from pyfly.web.openapi import OpenAPIGenerator


class TestOpenAPIGenerator:
    def test_basic_spec(self):
        gen = OpenAPIGenerator(title="Test API", version="1.0.0")
        spec = gen.generate()
        assert spec["openapi"] == "3.1.0"
        assert spec["info"]["title"] == "Test API"
        assert spec["info"]["version"] == "1.0.0"

    def test_description(self):
        gen = OpenAPIGenerator(title="Test", version="1.0", description="My API")
        spec = gen.generate()
        assert spec["info"]["description"] == "My API"

    def test_empty_paths(self):
        gen = OpenAPIGenerator(title="Test", version="1.0")
        spec = gen.generate()
        assert spec["paths"] == {}

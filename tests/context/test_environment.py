"""Tests for Environment with profile support."""

import os

import pytest

from pyfly.context.environment import Environment
from pyfly.core.config import Config


class TestEnvironment:
    def test_default_no_profiles(self):
        env = Environment(Config({}))
        assert env.active_profiles == []

    def test_profiles_from_config(self):
        env = Environment(Config({"pyfly": {"profiles": {"active": "production,staging"}}}))
        assert env.active_profiles == ["production", "staging"]

    def test_profiles_from_env_var(self, monkeypatch):
        monkeypatch.setenv("PYFLY_PROFILES_ACTIVE", "test,ci")
        env = Environment(Config({}))
        assert env.active_profiles == ["test", "ci"]

    def test_env_var_overrides_config(self, monkeypatch):
        monkeypatch.setenv("PYFLY_PROFILES_ACTIVE", "override")
        env = Environment(Config({"pyfly": {"profiles": {"active": "original"}}}))
        assert env.active_profiles == ["override"]

    def test_accepts_profiles_match(self):
        env = Environment(Config({"pyfly": {"profiles": {"active": "production"}}}))
        assert env.accepts_profiles("production") is True
        assert env.accepts_profiles("staging") is False
        assert env.accepts_profiles("production", "staging") is True

    def test_get_property_from_config(self):
        env = Environment(Config({"app": {"name": "MyApp"}}))
        assert env.get_property("app.name") == "MyApp"

    def test_get_property_default(self):
        env = Environment(Config({}))
        assert env.get_property("missing.key", "default") == "default"

    def test_get_property_none_when_missing(self):
        env = Environment(Config({}))
        assert env.get_property("missing.key") is None

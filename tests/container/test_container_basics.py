# Copyright 2026 Firefly Software Solutions Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for DI container basic registration and resolution."""

import pytest

from pyfly.container import Container, Scope


class Greeter:
    def greet(self) -> str:
        return "hello"


class UserService:
    def __init__(self, greeter: Greeter) -> None:
        self.greeter = greeter


class TestContainerBasics:
    def test_register_and_resolve(self):
        container = Container()
        container.register(Greeter)
        instance = container.resolve(Greeter)
        assert isinstance(instance, Greeter)
        assert instance.greet() == "hello"

    def test_resolve_with_dependency(self):
        container = Container()
        container.register(Greeter)
        container.register(UserService)
        service = container.resolve(UserService)
        assert isinstance(service, UserService)
        assert isinstance(service.greeter, Greeter)

    def test_singleton_scope_returns_same_instance(self):
        container = Container()
        container.register(Greeter, scope=Scope.SINGLETON)
        a = container.resolve(Greeter)
        b = container.resolve(Greeter)
        assert a is b

    def test_transient_scope_returns_new_instance(self):
        container = Container()
        container.register(Greeter, scope=Scope.TRANSIENT)
        a = container.resolve(Greeter)
        b = container.resolve(Greeter)
        assert a is not b

    def test_resolve_unregistered_raises(self):
        container = Container()
        with pytest.raises(KeyError):
            container.resolve(Greeter)

    def test_bind_interface_to_implementation(self):
        class Cache:
            pass

        class RedisCache(Cache):
            pass

        container = Container()
        container.register(RedisCache)
        container.bind(Cache, RedisCache)
        instance = container.resolve(Cache)
        assert isinstance(instance, RedisCache)

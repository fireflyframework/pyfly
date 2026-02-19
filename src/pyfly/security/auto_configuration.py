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
"""Security auto-configuration — JWT and password encoding beans."""

# NOTE: No `from __future__ import annotations` — typing.get_type_hints()
# must resolve return types at runtime for @bean method registration.

try:
    from pyfly.security.jwt import JWTService
except ImportError:
    JWTService = object  # type: ignore[misc,assignment]

try:
    from pyfly.security.password import BcryptPasswordEncoder
except ImportError:
    BcryptPasswordEncoder = object  # type: ignore[misc,assignment]

from pyfly.container.bean import bean
from pyfly.context.conditions import (
    auto_configuration,
    conditional_on_class,
    conditional_on_property,
)
from pyfly.core.config import Config


@auto_configuration
@conditional_on_property("pyfly.security.enabled", having_value="true")
@conditional_on_class("jwt")
class JwtAutoConfiguration:
    """Auto-configures a JWTService bean when pyjwt is installed."""

    @bean
    def jwt_service(self, config: Config) -> JWTService:
        secret = str(config.get("pyfly.security.jwt.secret", "change-me-in-production"))
        algorithm = str(config.get("pyfly.security.jwt.algorithm", "HS256"))
        return JWTService(secret=secret, algorithm=algorithm)


@auto_configuration
@conditional_on_property("pyfly.security.enabled", having_value="true")
@conditional_on_class("bcrypt")
class PasswordEncoderAutoConfiguration:
    """Auto-configures a BcryptPasswordEncoder bean when bcrypt is installed."""

    @bean
    def password_encoder(self, config: Config) -> BcryptPasswordEncoder:
        rounds = int(config.get("pyfly.security.password.bcrypt-rounds", 12))
        return BcryptPasswordEncoder(rounds=rounds)

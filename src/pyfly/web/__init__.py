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
"""PyFly Web — Enterprise web layer with pluggable adapters.

Framework-agnostic types (mappings, params, etc.) are exported directly.
Default adapter (Starlette) exports are re-exported for convenience.
"""

# Framework-agnostic exports
# Default adapter (Starlette) re-exports
from pyfly.web.adapters.starlette import (
    ControllerRegistrar,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    create_app,
    handle_return_value,
)
from pyfly.web.cors import CORSConfig
from pyfly.web.exception_handler import exception_handler
from pyfly.web.filters import OncePerRequestFilter
from pyfly.web.mappings import (
    delete_mapping,
    get_mapping,
    patch_mapping,
    post_mapping,
    put_mapping,
    request_mapping,
)
from pyfly.web.params import Body, Cookie, Header, PathVar, QueryParam, Valid
from pyfly.web.ports.filter import WebFilter
from pyfly.web.security_headers import SecurityHeadersConfig

__all__ = [
    # Framework-agnostic
    "Body",
    "CORSConfig",
    "Cookie",
    "Header",
    "OncePerRequestFilter",
    "PathVar",
    "QueryParam",
    "SecurityHeadersConfig",
    "Valid",
    "WebFilter",
    "delete_mapping",
    "exception_handler",
    "get_mapping",
    "patch_mapping",
    "post_mapping",
    "put_mapping",
    "request_mapping",
    # Default adapter (Starlette)
    "ControllerRegistrar",
    "RequestLoggingMiddleware",
    "SecurityHeadersMiddleware",
    "create_app",
    "handle_return_value",
]

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
"""PyFly Web — Enterprise web layer on Starlette."""

from pyfly.web.app import create_app
from pyfly.web.controller import ControllerRegistrar
from pyfly.web.exception_handler import exception_handler
from pyfly.web.mappings import (
    delete_mapping,
    get_mapping,
    patch_mapping,
    post_mapping,
    put_mapping,
    request_mapping,
)
from pyfly.web.params import Body, Cookie, Header, PathVar, QueryParam
from pyfly.web.request_logger import RequestLoggingMiddleware
from pyfly.web.response import handle_return_value

__all__ = [
    "Body",
    "ControllerRegistrar",
    "Cookie",
    "Header",
    "PathVar",
    "QueryParam",
    "RequestLoggingMiddleware",
    "create_app",
    "delete_mapping",
    "exception_handler",
    "get_mapping",
    "handle_return_value",
    "patch_mapping",
    "post_mapping",
    "put_mapping",
    "request_mapping",
]

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
"""Container exceptions — fatal errors during bean creation and startup."""

from __future__ import annotations


class BeanCreationException(Exception):
    """Fatal error during bean creation -- application cannot start.

    Raised when explicitly-configured infrastructure is unavailable
    or misconfigured.  Analogous to Spring Boot's BeanCreationException.
    """

    def __init__(self, subsystem: str, provider: str, reason: str) -> None:
        self.subsystem = subsystem
        self.provider = provider
        self.reason = reason
        super().__init__(
            f"Failed to configure {subsystem} with provider '{provider}': {reason}"
        )

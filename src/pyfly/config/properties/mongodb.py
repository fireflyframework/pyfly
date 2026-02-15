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
"""MongoDB subsystem configuration properties."""

from __future__ import annotations

from dataclasses import dataclass

from pyfly.core.config import config_properties


@config_properties(prefix="pyfly.mongodb")
@dataclass
class MongoDBProperties:
    """Configuration for the MongoDB subsystem (pyfly.mongodb.*)."""

    enabled: bool = False
    uri: str = "mongodb://localhost:27017"
    database: str = "pyfly"
    min_pool_size: int = 0
    max_pool_size: int = 100

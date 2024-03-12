# Copyright 2020 Google LLC
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

import asyncio
from typing import Set

from google.cloud.pubsublite.internal.wire.assigner import Assigner
from google.cloud.pubsublite.types.partition import Partition


class FixedSetAssigner(Assigner):
    _partitions: Set[Partition]
    _returned_set: bool

    def __init__(self, partitions: Set[Partition]):
        self._partitions = partitions
        self._returned_set = False

    async def get_assignment(self) -> Set[Partition]:
        """Only returns an assignment the first iteration."""
        if self._returned_set:
            await asyncio.sleep(float("inf"))
            raise RuntimeError("Should never happen.")
        self._returned_set = True
        return self._partitions

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

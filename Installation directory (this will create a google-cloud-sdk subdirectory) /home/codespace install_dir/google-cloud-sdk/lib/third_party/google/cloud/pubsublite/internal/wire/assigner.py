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

from abc import abstractmethod, ABCMeta
from typing import AsyncContextManager, Set

from google.cloud.pubsublite.types.partition import Partition


class Assigner(AsyncContextManager, metaclass=ABCMeta):
    """
    An assigner will deliver a continuous stream of assignments when called into. Perform all necessary work with the
    assignment before attempting to get the next one.
    """

    @abstractmethod
    async def get_assignment(self) -> Set[Partition]:
        raise NotImplementedError()

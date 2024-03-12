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

from abc import ABC, abstractmethod

from google.cloud.pubsublite.types.partition import Partition
from google.cloud.pubsublite_v1.types.common import PubSubMessage


class RoutingPolicy(ABC):
    """A policy for how to route messages."""

    @abstractmethod
    def route(self, message: PubSubMessage) -> Partition:
        """
        Route a message to a given partition.
        Args:
          message: The message to route

        Returns: The partition to route to

        """
        raise NotImplementedError()

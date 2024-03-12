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
from typing import AsyncContextManager
from google.cloud.pubsublite_v1.types import PubSubMessage
from google.cloud.pubsublite.types import MessageMetadata


class Publisher(AsyncContextManager, metaclass=ABCMeta):
    """
    A Pub/Sub Lite asynchronous wire protocol publisher.
    """

    @abstractmethod
    async def publish(self, message: PubSubMessage) -> MessageMetadata:
        """
        Publish the provided message.

        Args:
          message: The message to be published.

        Returns:
          Metadata about the published message.

        Raises:
          GoogleAPICallError: On a permanent error.
        """
        raise NotImplementedError()

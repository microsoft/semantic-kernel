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
from typing import AsyncContextManager, List
from google.cloud.pubsublite_v1.types import SequencedMessage, FlowControlRequest


class Subscriber(AsyncContextManager, metaclass=ABCMeta):
    """
    A Pub/Sub Lite asynchronous wire protocol subscriber.
    """

    @abstractmethod
    async def read(self) -> List[SequencedMessage.meta.pb]:
        """
        Read a batch of messages off of the stream.

        Returns:
          The next batch of messages.

        Raises:
          GoogleAPICallError: On a permanent error.
        """
        raise NotImplementedError()

    @abstractmethod
    def allow_flow(self, request: FlowControlRequest):
        """
        Allow an additional amount of messages and bytes to be sent to this client.
        """
        raise NotImplementedError()

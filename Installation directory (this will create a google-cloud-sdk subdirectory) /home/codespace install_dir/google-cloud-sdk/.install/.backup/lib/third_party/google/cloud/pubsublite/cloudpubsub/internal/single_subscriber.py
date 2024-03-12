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
from typing import AsyncContextManager, Callable, List, Set, Optional

from google.cloud.pubsub_v1.subscriber.message import Message

from google.cloud.pubsublite.types import (
    SubscriptionPath,
    FlowControlSettings,
    Partition,
)


class AsyncSingleSubscriber(AsyncContextManager, metaclass=ABCMeta):
    """
    A Cloud Pub/Sub asynchronous subscriber.

    Must be used in an `async with` block or have __aenter__() awaited before use.
    """

    @abstractmethod
    async def read(self) -> List[Message]:
        """
        Read the next batch off of the stream.

        Returns:
          The next batch of messages. ack() or nack() must eventually be called
          exactly once on each message.

          Pub/Sub Lite does not support nack() by default- if you do call nack(), it will immediately fail the client
          unless you have a NackHandler installed.

        Raises:
          GoogleAPICallError: On a permanent error.
        """
        raise NotImplementedError()


AsyncSubscriberFactory = Callable[
    [SubscriptionPath, Optional[Set[Partition]], FlowControlSettings],
    AsyncSingleSubscriber,
]

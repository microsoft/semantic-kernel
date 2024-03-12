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
from typing import Callable

from google.api_core.exceptions import FailedPrecondition
from google.pubsub_v1 import PubsubMessage


class NackHandler(ABC):
    """
    A NackHandler handles calls to the nack() method which is not expressible in Pub/Sub Lite.
    """

    @abstractmethod
    def on_nack(self, message: PubsubMessage, ack: Callable[[], None]):
        """Handle a negative acknowledgement. ack must eventually be called.

        This method will be called on an event loop and should not block.

        Args:
          message: The nacked message.
          ack: A callable to acknowledge the underlying message. This must eventually be called.

        Raises:
          GoogleAPICallError: To fail the client if raised inline.
        """
        pass


class DefaultNackHandler(NackHandler):
    def on_nack(self, message: PubsubMessage, ack: Callable[[], None]):
        raise FailedPrecondition(
            "You may not nack messages by default when using a PubSub Lite client. See NackHandler for how to customize"
            " this."
        )

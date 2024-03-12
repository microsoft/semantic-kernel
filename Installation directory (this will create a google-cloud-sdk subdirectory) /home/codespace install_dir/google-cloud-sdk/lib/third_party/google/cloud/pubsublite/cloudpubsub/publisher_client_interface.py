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
from concurrent.futures import Future
from typing import ContextManager, Mapping, Union, AsyncContextManager

from google.cloud.pubsublite.types import TopicPath


class AsyncPublisherClientInterface(AsyncContextManager, metaclass=ABCMeta):
    """
    An AsyncPublisherClientInterface publishes messages similar to Google Pub/Sub, but must be used in an
    async context. Any publish failures are unlikely to succeed if retried.

    Must be used in an `async with` block or have __aenter__() awaited before use.
    """

    @abstractmethod
    async def publish(
        self,
        topic: Union[TopicPath, str],
        data: bytes,
        ordering_key: str = "",
        **attrs: Mapping[str, str],
    ) -> str:
        """
        Publish a message.

        Args:
          topic: The topic to publish to. Publishes to new topics may have nontrivial startup latency.
          data: The bytestring payload of the message
          ordering_key: The key to enforce ordering on, or "" for no ordering.
          **attrs: Additional attributes to send.

        Returns:
          An ack id, which can be decoded using MessageMetadata.decode.

        Raises:
          GoogleApiCallError: On a permanent failure.
        """
        raise NotImplementedError()


class PublisherClientInterface(ContextManager, metaclass=ABCMeta):
    """
    A PublisherClientInterface publishes messages similar to Google Pub/Sub.
    Any publish failures are unlikely to succeed if retried.

    Must be used in a `with` block or have __enter__() called before use.
    """

    @abstractmethod
    def publish(
        self,
        topic: Union[TopicPath, str],
        data: bytes,
        ordering_key: str = "",
        **attrs: Mapping[str, str],
    ) -> "Future[str]":
        """
        Publish a message.

        Args:
          topic: The topic to publish to. Publishes to new topics may have nontrivial startup latency.
          data: The bytestring payload of the message
          ordering_key: The key to enforce ordering on, or "" for no ordering.
          **attrs: Additional attributes to send.

        Returns:
          A future completed with an ack id of type str, which can be decoded using
          MessageMetadata.decode.

        Raises:
          GoogleApiCallError: On a permanent failure.
        """
        raise NotImplementedError()

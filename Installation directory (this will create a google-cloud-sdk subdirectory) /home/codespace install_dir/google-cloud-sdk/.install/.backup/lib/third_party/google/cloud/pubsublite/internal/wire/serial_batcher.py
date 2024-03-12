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
from typing import Generic, List, NamedTuple
import asyncio

from google.cloud.pubsublite.internal.wire.connection import Request, Response
from google.cloud.pubsublite.internal.wire.work_item import WorkItem


class BatchSize(NamedTuple):
    element_count: int
    byte_count: int

    def __add__(self, other: "BatchSize") -> "BatchSize":
        return BatchSize(
            self.element_count + other.element_count, self.byte_count + other.byte_count
        )


class RequestSizer(Generic[Request], metaclass=ABCMeta):
    """A RequestSizer determines the size of a request."""

    @abstractmethod
    def get_size(self, request: Request) -> BatchSize:
        """
        Args:
          request: A single request.

        Returns: The BatchSize of this request
        """
        raise NotImplementedError()


class IgnoredRequestSizer(RequestSizer[Request]):
    def get_size(self, request) -> BatchSize:
        return BatchSize(0, 0)


class SerialBatcher(Generic[Request, Response]):
    _sizer: RequestSizer[Request]
    _requests: List[WorkItem[Request, Response]]  # A list of outstanding requests
    _batch_size: BatchSize

    def __init__(self, sizer: RequestSizer[Request] = IgnoredRequestSizer()):
        self._sizer = sizer
        self._requests = []
        self._batch_size = BatchSize(0, 0)

    def add(self, request: Request) -> "asyncio.Future[Response]":
        """Add a new request to this batcher.

        Args:
          request: The request to send.

        Returns:
          A future that will resolve to the response or a GoogleAPICallError.
        """
        item = WorkItem[Request, Response](request)
        self._requests.append(item)
        self._batch_size += self._sizer.get_size(request)
        return item.response_future

    def size(self) -> BatchSize:
        return self._batch_size

    def flush(self) -> List[WorkItem[Request, Response]]:
        requests = self._requests
        self._requests = []
        self._batch_size = BatchSize(0, 0)
        return requests

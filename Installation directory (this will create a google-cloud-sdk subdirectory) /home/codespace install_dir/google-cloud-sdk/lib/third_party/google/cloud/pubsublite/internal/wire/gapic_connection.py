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

from typing import (
    cast,
    AsyncIterator,
    TypeVar,
    Optional,
    Callable,
    AsyncIterable,
    Awaitable,
)
import asyncio

from google.api_core.exceptions import GoogleAPICallError, FailedPrecondition

from google.cloud.pubsublite.internal.wire.connection import (
    Connection,
    Request,
    Response,
    ConnectionFactory,
)
from google.cloud.pubsublite.internal.wire.work_item import WorkItem
from google.cloud.pubsublite.internal.wire.permanent_failable import PermanentFailable

T = TypeVar("T")


class GapicConnection(
    Connection[Request, Response], AsyncIterator[Request], PermanentFailable
):
    """A Connection wrapping a gapic AsyncIterator[Request/Response] pair."""

    _write_queue: "asyncio.Queue[WorkItem[Request, None]]"
    _response_it: Optional[AsyncIterator[Response]]

    def __init__(self):
        super().__init__()
        self._write_queue = asyncio.Queue(maxsize=1)

    def set_response_it(self, response_it: AsyncIterator[Response]):
        self._response_it = response_it

    async def write(self, request: Request) -> None:
        item = WorkItem(request)
        await self.await_unless_failed(self._write_queue.put(item))
        await self.await_unless_failed(item.response_future)

    async def read(self) -> Response:
        if self._response_it is None:
            self.fail(FailedPrecondition("GapicConnection not initialized."))
            raise self.error()
        try:
            response_it = cast(AsyncIterator[Response], self._response_it)
            return await self.await_unless_failed(response_it.__anext__())
        except StopAsyncIteration:
            self.fail(FailedPrecondition("Server sent unprompted half close."))
        except GoogleAPICallError as e:
            self.fail(e)
        raise self.error()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        pass

    async def __anext__(self) -> Request:
        item: WorkItem[Request, None] = await self.await_unless_failed(
            self._write_queue.get()
        )
        item.response_future.set_result(None)
        return item.request

    def __aiter__(self) -> AsyncIterator[Response]:
        return self


class GapicConnectionFactory(ConnectionFactory[Request, Response]):
    """A ConnectionFactory that produces GapicConnections."""

    _producer = Callable[[AsyncIterator[Request]], Awaitable[AsyncIterable[Response]]]

    def __init__(
        self,
        producer: Callable[
            [AsyncIterator[Request]], Awaitable[AsyncIterable[Response]]
        ],
    ):
        self._producer = producer

    async def new(self) -> Connection[Request, Response]:
        conn = GapicConnection[Request, Response]()
        response_fut = self._producer(conn)
        response_iterable = await response_fut
        conn.set_response_it(response_iterable.__aiter__())
        return conn

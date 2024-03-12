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
from typing import Optional, List

import logging

from google.cloud.pubsublite.internal.wait_ignore_cancelled import wait_ignore_errors
from google.cloud.pubsublite.internal.wire.committer import Committer
from google.cloud.pubsublite.internal.wire.retrying_connection import (
    RetryingConnection,
    ConnectionFactory,
)
from google.api_core.exceptions import FailedPrecondition, GoogleAPICallError
from google.cloud.pubsublite.internal.wire.connection_reinitializer import (
    ConnectionReinitializer,
)
from google.cloud.pubsublite.internal.wire.connection import Connection
from google.cloud.pubsublite_v1 import Cursor
from google.cloud.pubsublite_v1.types import (
    StreamingCommitCursorRequest,
    StreamingCommitCursorResponse,
    InitialCommitCursorRequest,
)


_LOGGER = logging.getLogger(__name__)


class CommitterImpl(
    Committer,
    ConnectionReinitializer[
        StreamingCommitCursorRequest, StreamingCommitCursorResponse
    ],
):
    _initial: InitialCommitCursorRequest
    _flush_seconds: float
    _connection: RetryingConnection[
        StreamingCommitCursorRequest, StreamingCommitCursorResponse
    ]

    _next_to_commit: Optional[Cursor]
    _outstanding_commits: List[Cursor]

    _receiver: Optional[asyncio.Future]
    _flusher: Optional[asyncio.Future]
    _empty: asyncio.Event

    def __init__(
        self,
        initial: InitialCommitCursorRequest,
        flush_seconds: float,
        factory: ConnectionFactory[
            StreamingCommitCursorRequest, StreamingCommitCursorResponse
        ],
    ):
        self._initial = initial
        self._flush_seconds = flush_seconds
        self._connection = RetryingConnection(factory, self)
        self._next_to_commit = None
        self._outstanding_commits = []
        self._receiver = None
        self._flusher = None
        self._empty = asyncio.Event()
        self._empty.set()

    async def __aenter__(self):
        await self._connection.__aenter__()
        return self

    def _start_loopers(self):
        assert self._receiver is None
        assert self._flusher is None
        self._receiver = asyncio.ensure_future(self._receive_loop())
        self._flusher = asyncio.ensure_future(self._flush_loop())

    async def _stop_loopers(self):
        if self._receiver:
            self._receiver.cancel()
            await wait_ignore_errors(self._receiver)
            self._receiver = None
        if self._flusher:
            self._flusher.cancel()
            await wait_ignore_errors(self._flusher)
            self._flusher = None

    def _handle_response(self, response: StreamingCommitCursorResponse):
        if "commit" not in response:
            self._connection.fail(
                FailedPrecondition(
                    "Received an invalid subsequent response on the commit stream."
                )
            )
        if response.commit.acknowledged_commits > len(self._outstanding_commits):
            self._connection.fail(
                FailedPrecondition(
                    "Received a commit response on the stream with no outstanding commits."
                )
            )
        for _ in range(response.commit.acknowledged_commits):
            self._outstanding_commits.pop(0)
        if len(self._outstanding_commits) == 0:
            self._empty.set()

    async def _receive_loop(self):
        while True:
            response = await self._connection.read()
            self._handle_response(response)

    async def _flush_loop(self):
        while True:
            await asyncio.sleep(self._flush_seconds)
            await self._flush()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._stop_loopers()
        if not self._connection.error():
            await self._flush()
        await self._connection.__aexit__(exc_type, exc_val, exc_tb)

    async def _flush(self):
        if self._next_to_commit is None:
            return
        req = StreamingCommitCursorRequest()
        req.commit.cursor = self._next_to_commit
        self._outstanding_commits.append(self._next_to_commit)
        self._next_to_commit = None
        self._empty.clear()
        try:
            await self._connection.write(req)
        except GoogleAPICallError as e:
            _LOGGER.debug(f"Failed commit on stream: {e}")

    async def wait_until_empty(self):
        await self._flush()
        await self._connection.await_unless_failed(self._empty.wait())

    def commit(self, cursor: Cursor) -> None:
        if self._connection.error():
            raise self._connection.error()
        self._next_to_commit = cursor

    async def stop_processing(self, error: GoogleAPICallError):
        await self._stop_loopers()

    async def reinitialize(
        self,
        connection: Connection[
            StreamingCommitCursorRequest, StreamingCommitCursorResponse
        ],
    ):
        await connection.write(StreamingCommitCursorRequest(initial=self._initial))
        response = await connection.read()
        if "initial" not in response:
            self._connection.fail(
                FailedPrecondition(
                    "Received an invalid initial response on the publish stream."
                )
            )
        if self._next_to_commit is None:
            if self._outstanding_commits:
                self._next_to_commit = self._outstanding_commits[-1]
        self._outstanding_commits = []
        self._start_loopers()

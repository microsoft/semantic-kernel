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
from typing import Optional, List, NamedTuple

import logging
from google.cloud.pubsub_v1.types import BatchSettings

from google.cloud.pubsublite.internal.publish_sequence_number import (
    PublishSequenceNumber,
)
from google.cloud.pubsublite.internal.wait_ignore_cancelled import wait_ignore_errors
from google.cloud.pubsublite.internal.wire.publisher import Publisher
from google.cloud.pubsublite.internal.wire.retrying_connection import (
    RetryingConnection,
    ConnectionFactory,
)
from google.api_core.exceptions import FailedPrecondition, GoogleAPICallError
from google.cloud.pubsublite.internal.wire.connection_reinitializer import (
    ConnectionReinitializer,
)
from google.cloud.pubsublite.internal.wire.connection import Connection
from google.cloud.pubsublite.internal.wire.serial_batcher import (
    SerialBatcher,
    RequestSizer,
    BatchSize,
)
from google.cloud.pubsublite.types import Partition, MessageMetadata
from google.cloud.pubsublite_v1.types import (
    PubSubMessage,
    Cursor,
    PublishRequest,
    PublishResponse,
    InitialPublishRequest,
)
from google.cloud.pubsublite.internal.wire.work_item import WorkItem

_LOGGER = logging.getLogger(__name__)

# Maximum bytes per batch at 3.5 MiB to avoid GRPC limit of 4 MiB
_MAX_BYTES = int(3.5 * 1024 * 1024)

# Maximum messages per batch at 1000
_MAX_MESSAGES = 1000


class _MessageWithSequence(NamedTuple):
    message: PubSubMessage
    sequence_number: PublishSequenceNumber


class SinglePartitionPublisher(
    Publisher,
    ConnectionReinitializer[PublishRequest, PublishResponse],
    RequestSizer[_MessageWithSequence],
):
    _initial: InitialPublishRequest
    _batching_settings: BatchSettings
    _connection: RetryingConnection[PublishRequest, PublishResponse]

    _next_sequence: PublishSequenceNumber
    _batcher: SerialBatcher[_MessageWithSequence, Cursor]
    _outstanding_writes: List[List[WorkItem[_MessageWithSequence, Cursor]]]

    _receiver: Optional[asyncio.Future]
    _flusher: Optional[asyncio.Future]

    def __init__(
        self,
        initial: InitialPublishRequest,
        batching_settings: BatchSettings,
        factory: ConnectionFactory[PublishRequest, PublishResponse],
        initial_sequence: PublishSequenceNumber,
    ):
        self._initial = initial
        self._batching_settings = batching_settings
        self._connection = RetryingConnection(factory, self)
        self._next_sequence = initial_sequence
        self._batcher = SerialBatcher(self)
        self._outstanding_writes = []
        self._receiver = None
        self._flusher = None

    @property
    def _partition(self) -> Partition:
        return Partition(self._initial.partition)

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

    def _handle_response(self, response: PublishResponse):
        if "message_response" not in response:
            self._connection.fail(
                FailedPrecondition(
                    "Received an invalid subsequent response on the publish stream."
                )
            )
        if not self._outstanding_writes:
            self._connection.fail(
                FailedPrecondition(
                    "Received an publish response on the stream with no outstanding publishes."
                )
            )
        ranges = response.message_response.cursor_ranges
        ranges.sort(key=lambda r: r.start_index)
        batch: List[WorkItem[_MessageWithSequence]] = self._outstanding_writes.pop(0)
        range_idx = 0
        for msg_idx, item in enumerate(batch):
            if range_idx < len(ranges) and ranges[range_idx].end_index <= msg_idx:
                range_idx += 1
            offset = -1
            if (
                range_idx < len(ranges)
                and msg_idx >= ranges[range_idx].start_index
                and msg_idx < ranges[range_idx].end_index
            ):
                offset_in_range = msg_idx - ranges[range_idx].start_index
                offset = ranges[range_idx].start_cursor.offset + offset_in_range
            item.response_future.set_result(Cursor(offset=offset))

    async def _receive_loop(self):
        while True:
            response = await self._connection.read()
            self._handle_response(response)

    async def _flush_loop(self):
        while True:
            await asyncio.sleep(self._batching_settings.max_latency)
            await self._flush()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._connection.error():
            self._fail_if_retrying_failed()
        else:
            await self._flush()
        await self._stop_loopers()
        await self._connection.__aexit__(exc_type, exc_val, exc_tb)

    def _fail_if_retrying_failed(self):
        if self._connection.error():
            for batch in self._outstanding_writes:
                for item in batch:
                    item.response_future.set_exception(self._connection.error())

    async def _flush(self):
        batch = self._batcher.flush()
        if not batch:
            return
        self._outstanding_writes.append(batch)
        aggregate = PublishRequest()
        aggregate.message_publish_request.messages = [
            item.request.message for item in batch
        ]
        if self._initial.client_id:
            aggregate.message_publish_request.first_sequence_number = batch[
                0
            ].request.sequence_number.value
        try:
            await self._connection.write(aggregate)
        except GoogleAPICallError as e:
            _LOGGER.debug(f"Failed publish on stream: {e}")
            self._fail_if_retrying_failed()

    async def publish(self, message: PubSubMessage) -> MessageMetadata:
        future = self._batcher.add(_MessageWithSequence(message, self._next_sequence))
        self._next_sequence = self._next_sequence.next()
        if self._should_flush():
            await self._flush()
        return MessageMetadata(self._partition, await future)

    async def stop_processing(self, error: GoogleAPICallError):
        await self._stop_loopers()

    async def reinitialize(
        self,
        connection: Connection[PublishRequest, PublishResponse],
    ):
        await connection.write(PublishRequest(initial_request=self._initial))
        response = await connection.read()
        if "initial_response" not in response:
            self._connection.fail(
                FailedPrecondition(
                    "Received an invalid initial response on the publish stream."
                )
            )
        for batch in self._outstanding_writes:
            aggregate = PublishRequest()
            aggregate.message_publish_request.messages = [
                item.request.message for item in batch
            ]
            await connection.write(aggregate)
        self._start_loopers()

    def get_size(self, request: _MessageWithSequence) -> BatchSize:
        return BatchSize(
            element_count=1, byte_count=PubSubMessage.pb(request.message).ByteSize()
        )

    def _should_flush(self) -> bool:
        size = self._batcher.size()
        return (size.element_count >= self._batching_settings.max_messages) or (
            size.byte_count >= self._batching_settings.max_bytes
        )

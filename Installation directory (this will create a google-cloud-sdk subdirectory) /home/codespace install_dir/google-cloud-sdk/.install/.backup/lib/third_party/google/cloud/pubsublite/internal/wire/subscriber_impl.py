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
from copy import deepcopy
from typing import Optional, List

from google.api_core.exceptions import GoogleAPICallError, FailedPrecondition

from google.cloud.pubsublite.internal.wait_ignore_cancelled import wait_ignore_errors
from google.cloud.pubsublite.internal.wire.connection import (
    Connection,
    ConnectionFactory,
)
from google.cloud.pubsublite.internal.wire.connection_reinitializer import (
    ConnectionReinitializer,
)
from google.cloud.pubsublite.internal.wire.flow_control_batcher import (
    FlowControlBatcher,
)
from google.cloud.pubsublite.internal.wire.reset_signal import is_reset_signal
from google.cloud.pubsublite.internal.wire.retrying_connection import RetryingConnection
from google.cloud.pubsublite.internal.wire.subscriber import Subscriber
from google.cloud.pubsublite_v1 import (
    SubscribeRequest,
    SubscribeResponse,
    FlowControlRequest,
    SequencedMessage,
    InitialSubscribeRequest,
    SeekRequest,
    Cursor,
)
from google.cloud.pubsublite.internal.wire.subscriber_reset_handler import (
    SubscriberResetHandler,
)


class SubscriberImpl(
    Subscriber, ConnectionReinitializer[SubscribeRequest, SubscribeResponse]
):
    _base_initial: InitialSubscribeRequest
    _token_flush_seconds: float
    _connection: RetryingConnection[SubscribeRequest, SubscribeResponse]
    _reset_handler: SubscriberResetHandler

    _outstanding_flow_control: FlowControlBatcher

    _last_received_offset: Optional[int]

    _message_queue: "asyncio.Queue[List[SequencedMessage.meta.pb]]"

    _receiver: Optional[asyncio.Future]
    _flusher: Optional[asyncio.Future]

    def __init__(
        self,
        base_initial: InitialSubscribeRequest,
        token_flush_seconds: float,
        factory: ConnectionFactory[SubscribeRequest, SubscribeResponse],
        reset_handler: SubscriberResetHandler,
    ):
        self._base_initial = base_initial
        self._token_flush_seconds = token_flush_seconds
        self._connection = RetryingConnection(factory, self)
        self._reset_handler = reset_handler
        self._outstanding_flow_control = FlowControlBatcher()
        self._reinitializing = False
        self._last_received_offset = None
        self._message_queue = asyncio.Queue()
        self._receiver = None
        self._flusher = None

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

    def _handle_response(self, response: SubscribeResponse):
        if "messages" not in response:
            self._connection.fail(
                FailedPrecondition(
                    "Received an invalid subsequent response on the subscribe stream."
                )
            )
            return
        # Workaround for incredibly slow proto-plus-python accesses
        messages = list(
            response.messages.messages._pb  # pytype: disable=attribute-error
        )
        self._outstanding_flow_control.on_messages(messages)
        for message in messages:
            if (
                self._last_received_offset is not None
                and message.cursor.offset <= self._last_received_offset
            ):
                self._connection.fail(
                    FailedPrecondition(
                        "Received an invalid out of order message from the server. Message is {}, previous last received is {}.".format(
                            message.cursor.offset, self._last_received_offset
                        )
                    )
                )
                return
            self._last_received_offset = message.cursor.offset
        # queue is unbounded.
        self._message_queue.put_nowait(messages)

    async def _receive_loop(self):
        while True:
            response = await self._connection.read()
            self._handle_response(response)

    async def _try_send_tokens(self):
        req = self._outstanding_flow_control.release_pending_request()
        if req is None:
            return
        try:
            await self._connection.write(SubscribeRequest(flow_control=req))
        except GoogleAPICallError:
            # May be transient, in which case these tokens will be resent.
            pass

    async def _flush_loop(self):
        while True:
            await asyncio.sleep(self._token_flush_seconds)
            await self._try_send_tokens()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._stop_loopers()
        await self._connection.__aexit__(exc_type, exc_val, exc_tb)

    async def stop_processing(self, error: GoogleAPICallError):
        await self._stop_loopers()
        if is_reset_signal(error):
            # Discard undelivered messages and refill flow control tokens.
            while not self._message_queue.empty():
                batch: List[SequencedMessage.meta.pb] = self._message_queue.get_nowait()
                allowed_bytes = sum(message.size_bytes for message in batch)
                self._outstanding_flow_control.add(
                    FlowControlRequest(
                        allowed_messages=len(batch),
                        allowed_bytes=allowed_bytes,
                    )
                )

            await self._reset_handler.handle_reset()
            self._last_received_offset = None

    async def reinitialize(
        self, connection: Connection[SubscribeRequest, SubscribeResponse]
    ):
        initial = deepcopy(self._base_initial)
        if self._last_received_offset is not None:
            initial.initial_location = SeekRequest(
                cursor=Cursor(offset=self._last_received_offset + 1)
            )
        else:
            initial.initial_location = SeekRequest(
                named_target=SeekRequest.NamedTarget.COMMITTED_CURSOR
            )
        await connection.write(SubscribeRequest(initial=initial))
        response = await connection.read()
        if "initial" not in response:
            self._connection.fail(
                FailedPrecondition(
                    "Received an invalid initial response on the subscribe stream."
                )
            )
            return
        tokens = self._outstanding_flow_control.request_for_restart()
        if tokens is not None:
            await connection.write(SubscribeRequest(flow_control=tokens))
        self._start_loopers()

    async def read(self) -> List[SequencedMessage.meta.pb]:
        return await self._connection.await_unless_failed(self._message_queue.get())

    def allow_flow(self, request: FlowControlRequest):
        self._outstanding_flow_control.add(request)

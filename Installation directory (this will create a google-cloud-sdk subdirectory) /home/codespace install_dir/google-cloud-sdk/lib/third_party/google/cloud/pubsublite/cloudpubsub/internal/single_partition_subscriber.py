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
from typing import Callable, List, Dict, NamedTuple

from google.api_core.exceptions import GoogleAPICallError
from google.cloud.pubsub_v1.subscriber.message import Message
from google.pubsub_v1 import PubsubMessage

from google.cloud.pubsublite.internal.wire.permanent_failable import adapt_error
from google.cloud.pubsublite.types import FlowControlSettings
from google.cloud.pubsublite.cloudpubsub.internal.ack_set_tracker import AckSetTracker
from google.cloud.pubsublite.cloudpubsub.internal.wrapped_message import (
    AckId,
    WrappedMessage,
)
from google.cloud.pubsublite.cloudpubsub.message_transformer import MessageTransformer
from google.cloud.pubsublite.cloudpubsub.nack_handler import NackHandler
from google.cloud.pubsublite.cloudpubsub.internal.single_subscriber import (
    AsyncSingleSubscriber,
)
from google.cloud.pubsublite.internal.wire.permanent_failable import PermanentFailable
from google.cloud.pubsublite.internal.wire.subscriber import Subscriber
from google.cloud.pubsublite.internal.wire.subscriber_reset_handler import (
    SubscriberResetHandler,
)
from google.cloud.pubsublite_v1 import FlowControlRequest, SequencedMessage


class _SizedMessage(NamedTuple):
    message: PubsubMessage
    size_bytes: int


ResettableSubscriberFactory = Callable[[SubscriberResetHandler], Subscriber]


class SinglePartitionSingleSubscriber(
    PermanentFailable, AsyncSingleSubscriber, SubscriberResetHandler
):
    _underlying: Subscriber
    _flow_control_settings: FlowControlSettings
    _ack_set_tracker: AckSetTracker
    _nack_handler: NackHandler
    _transformer: MessageTransformer

    _ack_generation_id: int
    _messages_by_ack_id: Dict[AckId, _SizedMessage]

    _loop: asyncio.AbstractEventLoop

    def __init__(
        self,
        subscriber_factory: ResettableSubscriberFactory,
        flow_control_settings: FlowControlSettings,
        ack_set_tracker: AckSetTracker,
        nack_handler: NackHandler,
        transformer: MessageTransformer,
    ):
        super().__init__()
        self._underlying = subscriber_factory(self)
        self._flow_control_settings = flow_control_settings
        self._ack_set_tracker = ack_set_tracker
        self._nack_handler = nack_handler
        self._transformer = transformer

        self._ack_generation_id = 0
        self._messages_by_ack_id = {}

    async def handle_reset(self):
        # Increment ack generation id to ignore unacked messages.
        self._ack_generation_id += 1
        await self._ack_set_tracker.clear_and_commit()

    def _wrap_message(self, message: SequencedMessage.meta.pb) -> Message:
        # Rewrap in the proto-plus-python wrapper for passing to the transform
        rewrapped = SequencedMessage()
        rewrapped._pb = message
        cps_message = self._transformer.transform(rewrapped)
        offset = message.cursor.offset
        ack_id = AckId(self._ack_generation_id, offset)
        self._ack_set_tracker.track(offset)
        self._messages_by_ack_id[ack_id] = _SizedMessage(
            cps_message, message.size_bytes
        )
        wrapped_message = WrappedMessage(
            pb=cps_message._pb,
            ack_id=ack_id,
            ack_handler=lambda id, ack: self._on_ack_threadsafe(id, ack),
        )
        return wrapped_message

    def _on_ack_threadsafe(self, ack_id: AckId, should_ack: bool) -> None:
        """A function called when a message is acked, may happen from any thread."""
        if should_ack:
            self._loop.call_soon_threadsafe(lambda: self._handle_ack(ack_id))
            return
        try:
            sized_message = self._messages_by_ack_id[ack_id]
            # Call the threadsafe version on ack since the callback may be called from another thread.
            self._nack_handler.on_nack(
                sized_message.message, lambda: self._on_ack_threadsafe(ack_id, True)
            )
        except Exception as e:
            e2 = adapt_error(e)
            self._loop.call_soon_threadsafe(lambda: self.fail(e2))

    async def read(self) -> List[Message]:
        try:
            latest_batch = await self.await_unless_failed(self._underlying.read())
            return [self._wrap_message(message) for message in latest_batch]
        except Exception as e:
            e = adapt_error(e)  # This could be from user code
            self.fail(e)
            raise e

    def _handle_ack(self, ack_id: AckId):
        flow_control = FlowControlRequest()
        flow_control._pb.allowed_messages = 1
        flow_control._pb.allowed_bytes = self._messages_by_ack_id[ack_id].size_bytes
        self._underlying.allow_flow(flow_control)
        del self._messages_by_ack_id[ack_id]
        # Always refill flow control tokens, but do not commit offsets from outdated generations.
        if ack_id.generation == self._ack_generation_id:
            try:
                self._ack_set_tracker.ack(ack_id.offset)
            except GoogleAPICallError as e:
                self.fail(e)

    async def __aenter__(self):
        self._loop = asyncio.get_event_loop()
        await self._ack_set_tracker.__aenter__()
        await self._underlying.__aenter__()
        self._underlying.allow_flow(
            FlowControlRequest(
                allowed_messages=self._flow_control_settings.messages_outstanding,
                allowed_bytes=self._flow_control_settings.bytes_outstanding,
            )
        )
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._underlying.__aexit__(exc_type, exc_value, traceback)
        await self._ack_set_tracker.__aexit__(exc_type, exc_value, traceback)

# Copyright 2017, Google LLC All rights reserved.
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

from __future__ import absolute_import

import datetime as dt
import json
import math
import time
import typing
from typing import Optional, Callable

from google.cloud.pubsub_v1.subscriber._protocol import requests
from google.cloud.pubsub_v1.subscriber import futures
from google.cloud.pubsub_v1.subscriber.exceptions import AcknowledgeStatus


if typing.TYPE_CHECKING:  # pragma: NO COVER
    import datetime
    import queue
    from google.cloud.pubsub_v1 import types
    from cloudsdk.google.protobuf.internal import containers


_MESSAGE_REPR = """\
Message {{
  data: {!r}
  ordering_key: {!r}
  attributes: {}
}}"""

_SUCCESS_FUTURE = futures.Future()
_SUCCESS_FUTURE.set_result(AcknowledgeStatus.SUCCESS)


def _indent(lines: str, prefix: str = "  ") -> str:
    """Indent some text.

    Note that this is present as ``textwrap.indent``, but not in Python 2.

    Args:
        lines:
            The newline delimited string to be indented.
        prefix:
            The prefix to indent each line with. Defaults to two spaces.

    Returns:
        The newly indented content.
    """
    indented = []
    for line in lines.split("\n"):
        indented.append(prefix + line)
    return "\n".join(indented)


class Message(object):
    """A representation of a single Pub/Sub message.

    The common way to interact with
    :class:`~.pubsub_v1.subscriber.message.Message` objects is to receive
    them in callbacks on subscriptions; most users should never have a need
    to instantiate them by hand. (The exception to this is if you are
    implementing a custom subclass to
    :class:`~.pubsub_v1.subscriber._consumer.Consumer`.)

    Attributes:
        message_id (str):
            The message ID. In general, you should not need to use this directly.
        data (bytes):
            The data in the message. Note that this will be a :class:`bytes`,
            not a text string.
        attributes (MutableMapping[str, str]):
            The attributes sent along with the message. See :attr:`attributes` for more
            information on this type.
        publish_time (google.protobuf.timestamp_pb2.Timestamp):
            The time that this message was originally published.
    """

    def __init__(
        self,
        message: "types.PubsubMessage._meta._pb",  # type: ignore
        ack_id: str,
        delivery_attempt: int,
        request_queue: "queue.Queue",
        exactly_once_delivery_enabled_func: Callable[[], bool] = lambda: False,
    ):
        """Construct the Message.

        .. note::

            This class should not be constructed directly; it is the
            responsibility of :class:`BasePolicy` subclasses to do so.

        Args:
            message (types.PubsubMessage._meta._pb):
                The message received from Pub/Sub. For performance reasons it should be
                the raw protobuf message normally wrapped by
                :class:`~pubsub_v1.types.PubsubMessage`. A raw message can be obtained
                from a  :class:`~pubsub_v1.types.PubsubMessage` instance through the
                latter's ``._pb`` attribute.
            ack_id (str):
                The ack_id received from Pub/Sub.
            delivery_attempt (int):
                The delivery attempt counter received from Pub/Sub if a DeadLetterPolicy
                is set on the subscription, and zero otherwise.
            request_queue (queue.Queue):
                A queue provided by the policy that can accept requests; the policy is
                responsible for handling those requests.
            exactly_once_delivery_enabled_func (Callable[[], bool]):
                A Callable that returns whether exactly-once delivery is currently-enabled. Defaults to a lambda that always returns False.
        """
        self._message = message
        self._ack_id = ack_id
        self._delivery_attempt = delivery_attempt if delivery_attempt > 0 else None
        self._request_queue = request_queue
        self._exactly_once_delivery_enabled_func = exactly_once_delivery_enabled_func
        self.message_id = message.message_id

        # The instantiation time is the time that this message
        # was received. Tracking this provides us a way to be smart about
        # the default lease deadline.
        self._received_timestamp = time.time()

        # Store the message attributes directly to speed up attribute access, i.e.
        # to avoid two lookups if self._message.<attribute> pattern was used in
        # properties.
        self._attributes = message.attributes
        self._data = message.data
        self._publish_time = dt.datetime.fromtimestamp(
            message.publish_time.seconds + message.publish_time.nanos / 1e9,
            tz=dt.timezone.utc,
        )
        self._ordering_key = message.ordering_key
        self._size = message.ByteSize()

    def __repr__(self):
        # Get an abbreviated version of the data.
        abbv_data = self._message.data
        if len(abbv_data) > 50:
            abbv_data = abbv_data[:50] + b"..."

        pretty_attrs = json.dumps(
            dict(self.attributes), indent=2, separators=(",", ": "), sort_keys=True
        )
        pretty_attrs = _indent(pretty_attrs)
        # We don't actually want the first line indented.
        pretty_attrs = pretty_attrs.lstrip()
        return _MESSAGE_REPR.format(abbv_data, str(self.ordering_key), pretty_attrs)

    @property
    def attributes(self) -> "containers.ScalarMap":
        """Return the attributes of the underlying Pub/Sub Message.

        .. warning::

            A ``ScalarMap`` behaves slightly differently than a
            ``dict``. For a Pub / Sub message this is a ``string->string`` map.
            When trying to access a value via ``map['key']``, if the key is
            not in the map, then the default value for the string type will
            be returned, which is an empty string. It may be more intuitive
            to just cast the map to a ``dict`` or to one use ``map.get``.

        Returns:
            containers.ScalarMap: The message's attributes. This is a
            ``dict``-like object provided by ``google.protobuf``.
        """
        return self._attributes

    @property
    def data(self) -> bytes:
        """Return the data for the underlying Pub/Sub Message.

        Returns:
            bytes: The message data. This is always a bytestring; if you want
            a text string, call :meth:`bytes.decode`.
        """
        return self._data

    @property
    def publish_time(self) -> "datetime.datetime":
        """Return the time that the message was originally published.

        Returns:
            datetime.datetime: The date and time that the message was
            published.
        """
        return self._publish_time

    @property
    def ordering_key(self) -> str:
        """The ordering key used to publish the message."""
        return self._ordering_key

    @property
    def size(self) -> int:
        """Return the size of the underlying message, in bytes."""
        return self._size

    @property
    def ack_id(self) -> str:
        """the ID used to ack the message."""
        return self._ack_id

    @property
    def delivery_attempt(self) -> Optional[int]:
        """The delivery attempt counter is 1 + (the sum of number of NACKs
        and number of ack_deadline exceeds) for this message. It is set to None
        if a DeadLetterPolicy is not set on the subscription.

        A NACK is any call to ModifyAckDeadline with a 0 deadline. An ack_deadline
        exceeds event is whenever a message is not acknowledged within
        ack_deadline. Note that ack_deadline is initially
        Subscription.ackDeadlineSeconds, but may get extended automatically by
        the client library.

        The first delivery of a given message will have this value as 1. The value
        is calculated at best effort and is approximate.

        Returns:
            Optional[int]: The delivery attempt counter or ``None``.
        """
        return self._delivery_attempt

    def ack(self) -> None:
        """Acknowledge the given message.

        Acknowledging a message in Pub/Sub means that you are done
        with it, and it will not be delivered to this subscription again.
        You should avoid acknowledging messages until you have
        *finished* processing them, so that in the event of a failure,
        you receive the message again.

        .. warning::
            Acks in Pub/Sub are best effort. You should always
            ensure that your processing code is idempotent, as you may
            receive any given message more than once. If you need strong
            guarantees about acks and re-deliveres, enable exactly-once
            delivery on your subscription and use the `ack_with_response`
            method instead. Exactly once delivery is a preview feature.
            For more details, see:
            https://cloud.google.com/pubsub/docs/exactly-once-delivery."

        """
        time_to_ack = math.ceil(time.time() - self._received_timestamp)
        self._request_queue.put(
            requests.AckRequest(
                ack_id=self._ack_id,
                byte_size=self.size,
                time_to_ack=time_to_ack,
                ordering_key=self.ordering_key,
                future=None,
            )
        )

    def ack_with_response(self) -> "futures.Future":
        """Acknowledge the given message.

        Acknowledging a message in Pub/Sub means that you are done
        with it, and it will not be delivered to this subscription again.
        You should avoid acknowledging messages until you have
        *finished* processing them, so that in the event of a failure,
        you receive the message again.

        If exactly-once delivery is NOT enabled on the subscription, the
        future returns immediately with an AcknowledgeStatus.SUCCESS.
        Since acks in Cloud Pub/Sub are best effort when exactly-once
        delivery is disabled, the message may be re-delivered. Because
        re-deliveries are possible, you should ensure that your processing
        code is idempotent, as you may receive any given message more than
        once.

        If exactly-once delivery is enabled on the subscription, the
        future returned by this method tracks the state of acknowledgement
        operation. If the future completes successfully, the message is
        guaranteed NOT to be re-delivered. Otherwise, the future will
        contain an exception with more details about the failure and the
        message may be re-delivered.

        Exactly once delivery is a preview feature. For more details,
        see https://cloud.google.com/pubsub/docs/exactly-once-delivery."

        Returns:
            futures.Future: A
            :class:`~google.cloud.pubsub_v1.subscriber.futures.Future`
            instance that conforms to Python Standard library's
            :class:`~concurrent.futures.Future` interface (but not an
            instance of that class). Call `result()` to get the result
            of the operation; upon success, a
            pubsub_v1.subscriber.exceptions.AcknowledgeStatus.SUCCESS
            will be returned and upon an error, an
            pubsub_v1.subscriber.exceptions.AcknowledgeError exception
            will be thrown.
        """
        req_future: Optional[futures.Future]
        if self._exactly_once_delivery_enabled_func():
            future = futures.Future()
            req_future = future
        else:
            future = _SUCCESS_FUTURE
            req_future = None
        time_to_ack = math.ceil(time.time() - self._received_timestamp)
        self._request_queue.put(
            requests.AckRequest(
                ack_id=self._ack_id,
                byte_size=self.size,
                time_to_ack=time_to_ack,
                ordering_key=self.ordering_key,
                future=req_future,
            )
        )
        return future

    def drop(self) -> None:
        """Release the message from lease management.

        This informs the policy to no longer hold on to the lease for this
        message. Pub/Sub will re-deliver the message if it is not acknowledged
        before the existing lease expires.

        .. warning::
            For most use cases, the only reason to drop a message from
            lease management is on `ack` or `nack`; this library
            automatically drop()s the message on `ack` or `nack`. You probably
            do not want to call this method directly.
        """
        self._request_queue.put(
            requests.DropRequest(
                ack_id=self._ack_id, byte_size=self.size, ordering_key=self.ordering_key
            )
        )

    def modify_ack_deadline(self, seconds: int) -> None:
        """Resets the deadline for acknowledgement.

        New deadline will be the given value of seconds from now.

        The default implementation handles automatically modacking received messages for you;
        you should not need to manually deal with setting ack deadlines. The exception case is
        if you are implementing your own custom subclass of
        :class:`~.pubsub_v1.subcriber._consumer.Consumer`.

        Args:
            seconds (int):
                The number of seconds to set the lease deadline to. This should be
                between 0 and 600. Due to network latency, values below 10 are advised
                against.
        """
        self._request_queue.put(
            requests.ModAckRequest(ack_id=self._ack_id, seconds=seconds, future=None)
        )

    def modify_ack_deadline_with_response(self, seconds: int) -> "futures.Future":
        """Resets the deadline for acknowledgement and returns the response
        status via a future.

        New deadline will be the given value of seconds from now.

        The default implementation handles automatically modacking received messages for you;
        you should not need to manually deal with setting ack deadlines. The exception case is
        if you are implementing your own custom subclass of
        :class:`~.pubsub_v1.subcriber._consumer.Consumer`.

        If exactly-once delivery is NOT enabled on the subscription, the
        future returns immediately with an AcknowledgeStatus.SUCCESS.
        Since modify-ack-deadline operations in Cloud Pub/Sub are best effort
        when exactly-once delivery is disabled, the message may be re-delivered
        within the set deadline.

        If exactly-once delivery is enabled on the subscription, the
        future returned by this method tracks the state of the
        modify-ack-deadline operation. If the future completes successfully,
        the message is guaranteed NOT to be re-delivered within the new deadline.
        Otherwise, the future will contain an exception with more details about
        the failure and the message will be redelivered according to its
        currently-set ack deadline.

        Exactly once delivery is a preview feature. For more details,
        see https://cloud.google.com/pubsub/docs/exactly-once-delivery."

        Args:
            seconds (int):
                The number of seconds to set the lease deadline to. This should be
                between 0 and 600. Due to network latency, values below 10 are advised
                against.
        Returns:
            futures.Future: A
            :class:`~google.cloud.pubsub_v1.subscriber.futures.Future`
            instance that conforms to Python Standard library's
            :class:`~concurrent.futures.Future` interface (but not an
            instance of that class). Call `result()` to get the result
            of the operation; upon success, a
            pubsub_v1.subscriber.exceptions.AcknowledgeStatus.SUCCESS
            will be returned and upon an error, an
            pubsub_v1.subscriber.exceptions.AcknowledgeError exception
            will be thrown.

        """
        req_future: Optional[futures.Future]
        if self._exactly_once_delivery_enabled_func():
            future = futures.Future()
            req_future = future
        else:
            future = _SUCCESS_FUTURE
            req_future = None

        self._request_queue.put(
            requests.ModAckRequest(
                ack_id=self._ack_id, seconds=seconds, future=req_future
            )
        )

        return future

    def nack(self) -> None:
        """Decline to acknowledge the given message.

        This will cause the message to be re-delivered to subscribers. Re-deliveries
        may take place immediately or after a delay, and may arrive at this subscriber
        or another.
        """
        self._request_queue.put(
            requests.NackRequest(
                ack_id=self._ack_id,
                byte_size=self.size,
                ordering_key=self.ordering_key,
                future=None,
            )
        )

    def nack_with_response(self) -> "futures.Future":
        """Decline to acknowledge the given message, returning the response status via
        a future.

        This will cause the message to be re-delivered to subscribers. Re-deliveries
        may take place immediately or after a delay, and may arrive at this subscriber
        or another.

        If exactly-once delivery is NOT enabled on the subscription, the
        future returns immediately with an AcknowledgeStatus.SUCCESS.

        If exactly-once delivery is enabled on the subscription, the
        future returned by this method tracks the state of the
        nack operation. If the future completes successfully,
        the future's result will be an AcknowledgeStatus.SUCCESS.
        Otherwise, the future will contain an exception with more details about
        the failure.

        Exactly once delivery is a preview feature. For more details,
        see https://cloud.google.com/pubsub/docs/exactly-once-delivery."

        Returns:
            futures.Future: A
            :class:`~google.cloud.pubsub_v1.subscriber.futures.Future`
            instance that conforms to Python Standard library's
            :class:`~concurrent.futures.Future` interface (but not an
            instance of that class). Call `result()` to get the result
            of the operation; upon success, a
            pubsub_v1.subscriber.exceptions.AcknowledgeStatus.SUCCESS
            will be returned and upon an error, an
            pubsub_v1.subscriber.exceptions.AcknowledgeError exception
            will be thrown.

        """
        req_future: Optional[futures.Future]
        if self._exactly_once_delivery_enabled_func():
            future = futures.Future()
            req_future = future
        else:
            future = _SUCCESS_FUTURE
            req_future = None

        self._request_queue.put(
            requests.NackRequest(
                ack_id=self._ack_id,
                byte_size=self.size,
                ordering_key=self.ordering_key,
                future=req_future,
            )
        )

        return future

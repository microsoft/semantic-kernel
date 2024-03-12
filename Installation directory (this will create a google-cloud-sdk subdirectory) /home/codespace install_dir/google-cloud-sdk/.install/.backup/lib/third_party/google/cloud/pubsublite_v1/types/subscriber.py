# -*- coding: utf-8 -*-
# Copyright 2022 Google LLC
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
#
from __future__ import annotations

from typing import MutableMapping, MutableSequence

import proto  # type: ignore

from google.cloud.pubsublite_v1.types import common


__protobuf__ = proto.module(
    package="google.cloud.pubsublite.v1",
    manifest={
        "InitialSubscribeRequest",
        "InitialSubscribeResponse",
        "SeekRequest",
        "SeekResponse",
        "FlowControlRequest",
        "SubscribeRequest",
        "MessageResponse",
        "SubscribeResponse",
        "InitialPartitionAssignmentRequest",
        "PartitionAssignment",
        "PartitionAssignmentAck",
        "PartitionAssignmentRequest",
    },
)


class InitialSubscribeRequest(proto.Message):
    r"""The first request that must be sent on a newly-opened stream.
    The client must wait for the response before sending subsequent
    requests on the stream.

    Attributes:
        subscription (str):
            The subscription from which to receive
            messages.
        partition (int):
            The partition from which to receive messages. Partitions are
            zero indexed, so ``partition`` must be in the range [0,
            topic.num_partitions).
        initial_location (google.cloud.pubsublite_v1.types.SeekRequest):
            Optional. Initial target location within the
            message backlog. If not set, messages will be
            delivered from the commit cursor for the given
            subscription and partition.
    """

    subscription: str = proto.Field(
        proto.STRING,
        number=1,
    )
    partition: int = proto.Field(
        proto.INT64,
        number=2,
    )
    initial_location: "SeekRequest" = proto.Field(
        proto.MESSAGE,
        number=4,
        message="SeekRequest",
    )


class InitialSubscribeResponse(proto.Message):
    r"""Response to an InitialSubscribeRequest.

    Attributes:
        cursor (google.cloud.pubsublite_v1.types.Cursor):
            The cursor from which the subscriber will
            start receiving messages once flow control
            tokens become available.
    """

    cursor: common.Cursor = proto.Field(
        proto.MESSAGE,
        number=1,
        message=common.Cursor,
    )


class SeekRequest(proto.Message):
    r"""Request to update the stream's delivery cursor based on the
    given target. Resets the server available tokens to 0.
    SeekRequests past head result in stream breakage.

    SeekRequests may not be sent while another SeekRequest is
    outstanding (i.e., has not received a SeekResponse) on the same
    stream.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        named_target (google.cloud.pubsublite_v1.types.SeekRequest.NamedTarget):
            A named target.

            This field is a member of `oneof`_ ``target``.
        cursor (google.cloud.pubsublite_v1.types.Cursor):
            A target corresponding to the cursor,
            pointing to anywhere in the topic partition.

            This field is a member of `oneof`_ ``target``.
    """

    class NamedTarget(proto.Enum):
        r"""A special target in the partition that takes no other
        parameters.

        Values:
            NAMED_TARGET_UNSPECIFIED (0):
                Default value. This value is unused.
            HEAD (1):
                A target corresponding to the most recently
                published message in the partition.
            COMMITTED_CURSOR (2):
                A target corresponding to the committed
                cursor for the given subscription and topic
                partition.
        """
        NAMED_TARGET_UNSPECIFIED = 0
        HEAD = 1
        COMMITTED_CURSOR = 2

    named_target: NamedTarget = proto.Field(
        proto.ENUM,
        number=1,
        oneof="target",
        enum=NamedTarget,
    )
    cursor: common.Cursor = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof="target",
        message=common.Cursor,
    )


class SeekResponse(proto.Message):
    r"""Response to a SeekRequest.

    Attributes:
        cursor (google.cloud.pubsublite_v1.types.Cursor):
            The new delivery cursor for the current
            stream.
    """

    cursor: common.Cursor = proto.Field(
        proto.MESSAGE,
        number=1,
        message=common.Cursor,
    )


class FlowControlRequest(proto.Message):
    r"""Request to grant tokens to the server, requesting delivery of
    messages when they become available.

    Attributes:
        allowed_messages (int):
            The number of message tokens to grant. Must
            be greater than or equal to 0.
        allowed_bytes (int):
            The number of byte tokens to grant. Must be
            greater than or equal to 0.
    """

    allowed_messages: int = proto.Field(
        proto.INT64,
        number=1,
    )
    allowed_bytes: int = proto.Field(
        proto.INT64,
        number=2,
    )


class SubscribeRequest(proto.Message):
    r"""A request sent from the client to the server on a stream.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        initial (google.cloud.pubsublite_v1.types.InitialSubscribeRequest):
            Initial request on the stream.

            This field is a member of `oneof`_ ``request``.
        seek (google.cloud.pubsublite_v1.types.SeekRequest):
            Request to update the stream's delivery
            cursor.

            This field is a member of `oneof`_ ``request``.
        flow_control (google.cloud.pubsublite_v1.types.FlowControlRequest):
            Request to grant tokens to the server,

            This field is a member of `oneof`_ ``request``.
    """

    initial: "InitialSubscribeRequest" = proto.Field(
        proto.MESSAGE,
        number=1,
        oneof="request",
        message="InitialSubscribeRequest",
    )
    seek: "SeekRequest" = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof="request",
        message="SeekRequest",
    )
    flow_control: "FlowControlRequest" = proto.Field(
        proto.MESSAGE,
        number=3,
        oneof="request",
        message="FlowControlRequest",
    )


class MessageResponse(proto.Message):
    r"""Response containing a list of messages. Upon delivering a
    MessageResponse to the client, the server:

    -  Updates the stream's delivery cursor to one greater than the
       cursor of the last message in the list.
    -  Subtracts the total number of bytes and messages from the tokens
       available to the server.

    Attributes:
        messages (MutableSequence[google.cloud.pubsublite_v1.types.SequencedMessage]):
            Messages from the topic partition.
    """

    messages: MutableSequence[common.SequencedMessage] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message=common.SequencedMessage,
    )


class SubscribeResponse(proto.Message):
    r"""Response to SubscribeRequest.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        initial (google.cloud.pubsublite_v1.types.InitialSubscribeResponse):
            Initial response on the stream.

            This field is a member of `oneof`_ ``response``.
        seek (google.cloud.pubsublite_v1.types.SeekResponse):
            Response to a Seek operation.

            This field is a member of `oneof`_ ``response``.
        messages (google.cloud.pubsublite_v1.types.MessageResponse):
            Response containing messages from the topic
            partition.

            This field is a member of `oneof`_ ``response``.
    """

    initial: "InitialSubscribeResponse" = proto.Field(
        proto.MESSAGE,
        number=1,
        oneof="response",
        message="InitialSubscribeResponse",
    )
    seek: "SeekResponse" = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof="response",
        message="SeekResponse",
    )
    messages: "MessageResponse" = proto.Field(
        proto.MESSAGE,
        number=3,
        oneof="response",
        message="MessageResponse",
    )


class InitialPartitionAssignmentRequest(proto.Message):
    r"""The first request that must be sent on a newly-opened stream.
    The client must wait for the response before sending subsequent
    requests on the stream.

    Attributes:
        subscription (str):
            The subscription name. Structured like:
            projects/<project number>/locations/<zone
            name>/subscriptions/<subscription id>
        client_id (bytes):
            An opaque, unique client identifier. This
            field must be exactly 16 bytes long and is
            interpreted as an unsigned 128 bit integer.
            Other size values will be rejected and the
            stream will be failed with a non-retryable
            error.
            This field is large enough to fit a uuid from
            standard uuid algorithms like uuid1 or uuid4,
            which should be used to generate this number.
            The same identifier should be reused following
            disconnections with retryable stream errors.
    """

    subscription: str = proto.Field(
        proto.STRING,
        number=1,
    )
    client_id: bytes = proto.Field(
        proto.BYTES,
        number=2,
    )


class PartitionAssignment(proto.Message):
    r"""PartitionAssignments should not race with acknowledgements.
    There should be exactly one unacknowledged PartitionAssignment
    at a time. If not, the client must break the stream.

    Attributes:
        partitions (MutableSequence[int]):
            The list of partition numbers this subscriber
            is assigned to.
    """

    partitions: MutableSequence[int] = proto.RepeatedField(
        proto.INT64,
        number=1,
    )


class PartitionAssignmentAck(proto.Message):
    r"""Acknowledge receipt and handling of the previous assignment.
    If not sent within a short period after receiving the
    assignment, partitions may remain unassigned for a period of
    time until the client is known to be inactive, after which time
    the server will break the stream.

    """


class PartitionAssignmentRequest(proto.Message):
    r"""A request on the PartitionAssignment stream.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        initial (google.cloud.pubsublite_v1.types.InitialPartitionAssignmentRequest):
            Initial request on the stream.

            This field is a member of `oneof`_ ``request``.
        ack (google.cloud.pubsublite_v1.types.PartitionAssignmentAck):
            Acknowledgement of a partition assignment.

            This field is a member of `oneof`_ ``request``.
    """

    initial: "InitialPartitionAssignmentRequest" = proto.Field(
        proto.MESSAGE,
        number=1,
        oneof="request",
        message="InitialPartitionAssignmentRequest",
    )
    ack: "PartitionAssignmentAck" = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof="request",
        message="PartitionAssignmentAck",
    )


__all__ = tuple(sorted(__protobuf__.manifest))

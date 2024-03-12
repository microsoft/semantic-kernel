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
        "InitialCommitCursorRequest",
        "InitialCommitCursorResponse",
        "SequencedCommitCursorRequest",
        "SequencedCommitCursorResponse",
        "StreamingCommitCursorRequest",
        "StreamingCommitCursorResponse",
        "CommitCursorRequest",
        "CommitCursorResponse",
        "ListPartitionCursorsRequest",
        "PartitionCursor",
        "ListPartitionCursorsResponse",
    },
)


class InitialCommitCursorRequest(proto.Message):
    r"""The first streaming request that must be sent on a
    newly-opened stream. The client must wait for the response
    before sending subsequent requests on the stream.

    Attributes:
        subscription (str):
            The subscription for which to manage
            committed cursors.
        partition (int):
            The partition for which to manage committed cursors.
            Partitions are zero indexed, so ``partition`` must be in the
            range [0, topic.num_partitions).
    """

    subscription: str = proto.Field(
        proto.STRING,
        number=1,
    )
    partition: int = proto.Field(
        proto.INT64,
        number=2,
    )


class InitialCommitCursorResponse(proto.Message):
    r"""Response to an InitialCommitCursorRequest."""


class SequencedCommitCursorRequest(proto.Message):
    r"""Streaming request to update the committed cursor. Subsequent
    SequencedCommitCursorRequests override outstanding ones.

    Attributes:
        cursor (google.cloud.pubsublite_v1.types.Cursor):
            The new value for the committed cursor.
    """

    cursor: common.Cursor = proto.Field(
        proto.MESSAGE,
        number=1,
        message=common.Cursor,
    )


class SequencedCommitCursorResponse(proto.Message):
    r"""Response to a SequencedCommitCursorRequest.

    Attributes:
        acknowledged_commits (int):
            The number of outstanding
            SequencedCommitCursorRequests acknowledged by
            this response. Note that
            SequencedCommitCursorRequests are acknowledged
            in the order that they are received.
    """

    acknowledged_commits: int = proto.Field(
        proto.INT64,
        number=1,
    )


class StreamingCommitCursorRequest(proto.Message):
    r"""A request sent from the client to the server on a stream.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        initial (google.cloud.pubsublite_v1.types.InitialCommitCursorRequest):
            Initial request on the stream.

            This field is a member of `oneof`_ ``request``.
        commit (google.cloud.pubsublite_v1.types.SequencedCommitCursorRequest):
            Request to commit a new cursor value.

            This field is a member of `oneof`_ ``request``.
    """

    initial: "InitialCommitCursorRequest" = proto.Field(
        proto.MESSAGE,
        number=1,
        oneof="request",
        message="InitialCommitCursorRequest",
    )
    commit: "SequencedCommitCursorRequest" = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof="request",
        message="SequencedCommitCursorRequest",
    )


class StreamingCommitCursorResponse(proto.Message):
    r"""Response to a StreamingCommitCursorRequest.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        initial (google.cloud.pubsublite_v1.types.InitialCommitCursorResponse):
            Initial response on the stream.

            This field is a member of `oneof`_ ``request``.
        commit (google.cloud.pubsublite_v1.types.SequencedCommitCursorResponse):
            Response to committing a new cursor value.

            This field is a member of `oneof`_ ``request``.
    """

    initial: "InitialCommitCursorResponse" = proto.Field(
        proto.MESSAGE,
        number=1,
        oneof="request",
        message="InitialCommitCursorResponse",
    )
    commit: "SequencedCommitCursorResponse" = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof="request",
        message="SequencedCommitCursorResponse",
    )


class CommitCursorRequest(proto.Message):
    r"""Request for CommitCursor.

    Attributes:
        subscription (str):
            The subscription for which to update the
            cursor.
        partition (int):
            The partition for which to update the cursor. Partitions are
            zero indexed, so ``partition`` must be in the range [0,
            topic.num_partitions).
        cursor (google.cloud.pubsublite_v1.types.Cursor):
            The new value for the committed cursor.
    """

    subscription: str = proto.Field(
        proto.STRING,
        number=1,
    )
    partition: int = proto.Field(
        proto.INT64,
        number=2,
    )
    cursor: common.Cursor = proto.Field(
        proto.MESSAGE,
        number=3,
        message=common.Cursor,
    )


class CommitCursorResponse(proto.Message):
    r"""Response for CommitCursor."""


class ListPartitionCursorsRequest(proto.Message):
    r"""Request for ListPartitionCursors.

    Attributes:
        parent (str):
            Required. The subscription for which to retrieve cursors.
            Structured like
            ``projects/{project_number}/locations/{location}/subscriptions/{subscription_id}``.
        page_size (int):
            The maximum number of cursors to return. The
            service may return fewer than this value.
            If unset or zero, all cursors for the parent
            will be returned.
        page_token (str):
            A page token, received from a previous
            ``ListPartitionCursors`` call. Provide this to retrieve the
            subsequent page.

            When paginating, all other parameters provided to
            ``ListPartitionCursors`` must match the call that provided
            the page token.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=2,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=3,
    )


class PartitionCursor(proto.Message):
    r"""A pair of a Cursor and the partition it is for.

    Attributes:
        partition (int):
            The partition this is for.
        cursor (google.cloud.pubsublite_v1.types.Cursor):
            The value of the cursor.
    """

    partition: int = proto.Field(
        proto.INT64,
        number=1,
    )
    cursor: common.Cursor = proto.Field(
        proto.MESSAGE,
        number=2,
        message=common.Cursor,
    )


class ListPartitionCursorsResponse(proto.Message):
    r"""Response for ListPartitionCursors

    Attributes:
        partition_cursors (MutableSequence[google.cloud.pubsublite_v1.types.PartitionCursor]):
            The partition cursors from this request.
        next_page_token (str):
            A token, which can be sent as ``page_token`` to retrieve the
            next page. If this field is omitted, there are no subsequent
            pages.
    """

    @property
    def raw_page(self):
        return self

    partition_cursors: MutableSequence["PartitionCursor"] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message="PartitionCursor",
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


__all__ = tuple(sorted(__protobuf__.manifest))

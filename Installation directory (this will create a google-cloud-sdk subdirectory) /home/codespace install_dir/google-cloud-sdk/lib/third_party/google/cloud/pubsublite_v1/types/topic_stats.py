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
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore


__protobuf__ = proto.module(
    package="google.cloud.pubsublite.v1",
    manifest={
        "ComputeMessageStatsRequest",
        "ComputeMessageStatsResponse",
        "ComputeHeadCursorRequest",
        "ComputeHeadCursorResponse",
        "ComputeTimeCursorRequest",
        "ComputeTimeCursorResponse",
    },
)


class ComputeMessageStatsRequest(proto.Message):
    r"""Compute statistics about a range of messages in a given topic
    and partition.

    Attributes:
        topic (str):
            Required. The topic for which we should
            compute message stats.
        partition (int):
            Required. The partition for which we should
            compute message stats.
        start_cursor (google.cloud.pubsublite_v1.types.Cursor):
            The inclusive start of the range.
        end_cursor (google.cloud.pubsublite_v1.types.Cursor):
            The exclusive end of the range. The range is empty if
            end_cursor <= start_cursor. Specifying a start_cursor before
            the first message and an end_cursor after the last message
            will retrieve all messages.
    """

    topic: str = proto.Field(
        proto.STRING,
        number=1,
    )
    partition: int = proto.Field(
        proto.INT64,
        number=2,
    )
    start_cursor: common.Cursor = proto.Field(
        proto.MESSAGE,
        number=3,
        message=common.Cursor,
    )
    end_cursor: common.Cursor = proto.Field(
        proto.MESSAGE,
        number=4,
        message=common.Cursor,
    )


class ComputeMessageStatsResponse(proto.Message):
    r"""Response containing stats for messages in the requested topic
    and partition.

    Attributes:
        message_count (int):
            The count of messages.
        message_bytes (int):
            The number of quota bytes accounted to these
            messages.
        minimum_publish_time (google.protobuf.timestamp_pb2.Timestamp):
            The minimum publish timestamp across these
            messages. Note that publish timestamps within a
            partition are not guaranteed to be
            non-decreasing. The timestamp will be unset if
            there are no messages.
        minimum_event_time (google.protobuf.timestamp_pb2.Timestamp):
            The minimum event timestamp across these
            messages. For the purposes of this computation,
            if a message does not have an event time, we use
            the publish time. The timestamp will be unset if
            there are no messages.
    """

    message_count: int = proto.Field(
        proto.INT64,
        number=1,
    )
    message_bytes: int = proto.Field(
        proto.INT64,
        number=2,
    )
    minimum_publish_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=3,
        message=timestamp_pb2.Timestamp,
    )
    minimum_event_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=4,
        message=timestamp_pb2.Timestamp,
    )


class ComputeHeadCursorRequest(proto.Message):
    r"""Compute the current head cursor for a partition.

    Attributes:
        topic (str):
            Required. The topic for which we should
            compute the head cursor.
        partition (int):
            Required. The partition for which we should
            compute the head cursor.
    """

    topic: str = proto.Field(
        proto.STRING,
        number=1,
    )
    partition: int = proto.Field(
        proto.INT64,
        number=2,
    )


class ComputeHeadCursorResponse(proto.Message):
    r"""Response containing the head cursor for the requested topic
    and partition.

    Attributes:
        head_cursor (google.cloud.pubsublite_v1.types.Cursor):
            The head cursor.
    """

    head_cursor: common.Cursor = proto.Field(
        proto.MESSAGE,
        number=1,
        message=common.Cursor,
    )


class ComputeTimeCursorRequest(proto.Message):
    r"""Compute the corresponding cursor for a publish or event time
    in a topic partition.

    Attributes:
        topic (str):
            Required. The topic for which we should
            compute the cursor.
        partition (int):
            Required. The partition for which we should
            compute the cursor.
        target (google.cloud.pubsublite_v1.types.TimeTarget):
            Required. The target publish or event time.
            Specifying a future time will return an unset
            cursor.
    """

    topic: str = proto.Field(
        proto.STRING,
        number=1,
    )
    partition: int = proto.Field(
        proto.INT64,
        number=2,
    )
    target: common.TimeTarget = proto.Field(
        proto.MESSAGE,
        number=3,
        message=common.TimeTarget,
    )


class ComputeTimeCursorResponse(proto.Message):
    r"""Response containing the cursor corresponding to a publish or
    event time in a topic partition.

    Attributes:
        cursor (google.cloud.pubsublite_v1.types.Cursor):
            If present, the cursor references the first message with
            time greater than or equal to the specified target time. If
            such a message cannot be found, the cursor will be unset
            (i.e. ``cursor`` is not present).
    """

    cursor: common.Cursor = proto.Field(
        proto.MESSAGE,
        number=1,
        message=common.Cursor,
    )


__all__ = tuple(sorted(__protobuf__.manifest))

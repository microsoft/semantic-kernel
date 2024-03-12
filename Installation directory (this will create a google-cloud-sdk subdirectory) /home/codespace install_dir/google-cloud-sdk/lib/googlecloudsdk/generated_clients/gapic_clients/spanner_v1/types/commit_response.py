# -*- coding: utf-8 -*-
# Copyright 2023 Google LLC
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

from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore


__protobuf__ = proto.module(
    package='google.spanner.v1',
    manifest={
        'CommitResponse',
    },
)


class CommitResponse(proto.Message):
    r"""The response for [Commit][google.spanner.v1.Spanner.Commit].

    Attributes:
        commit_timestamp (google.protobuf.timestamp_pb2.Timestamp):
            The Cloud Spanner timestamp at which the
            transaction committed.
        commit_stats (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.CommitResponse.CommitStats):
            The statistics about this Commit. Not returned by default.
            For more information, see
            [CommitRequest.return_commit_stats][google.spanner.v1.CommitRequest.return_commit_stats].
    """

    class CommitStats(proto.Message):
        r"""Additional statistics about a commit.

        Attributes:
            mutation_count (int):
                The total number of mutations for the transaction. Knowing
                the ``mutation_count`` value can help you maximize the
                number of mutations in a transaction and minimize the number
                of API round trips. You can also monitor this value to
                prevent transactions from exceeding the system
                `limit <https://cloud.google.com/spanner/quotas#limits_for_creating_reading_updating_and_deleting_data>`__.
                If the number of mutations exceeds the limit, the server
                returns
                `INVALID_ARGUMENT <https://cloud.google.com/spanner/docs/reference/rest/v1/Code#ENUM_VALUES.INVALID_ARGUMENT>`__.
        """

        mutation_count: int = proto.Field(
            proto.INT64,
            number=1,
        )

    commit_timestamp: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=1,
        message=timestamp_pb2.Timestamp,
    )
    commit_stats: CommitStats = proto.Field(
        proto.MESSAGE,
        number=2,
        message=CommitStats,
    )


__all__ = tuple(sorted(__protobuf__.manifest))

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

from cloudsdk.google.protobuf import struct_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types import query_plan as gs_query_plan
from googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types import transaction as gs_transaction
from googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types import type as gs_type


__protobuf__ = proto.module(
    package='google.spanner.v1',
    manifest={
        'ResultSet',
        'PartialResultSet',
        'ResultSetMetadata',
        'ResultSetStats',
    },
)


class ResultSet(proto.Message):
    r"""Results from [Read][google.spanner.v1.Spanner.Read] or
    [ExecuteSql][google.spanner.v1.Spanner.ExecuteSql].

    Attributes:
        metadata (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.ResultSetMetadata):
            Metadata about the result set, such as row
            type information.
        rows (MutableSequence[google.protobuf.struct_pb2.ListValue]):
            Each element in ``rows`` is a row whose format is defined by
            [metadata.row_type][google.spanner.v1.ResultSetMetadata.row_type].
            The ith element in each row matches the ith field in
            [metadata.row_type][google.spanner.v1.ResultSetMetadata.row_type].
            Elements are encoded based on type as described
            [here][google.spanner.v1.TypeCode].
        stats (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.ResultSetStats):
            Query plan and execution statistics for the SQL statement
            that produced this result set. These can be requested by
            setting
            [ExecuteSqlRequest.query_mode][google.spanner.v1.ExecuteSqlRequest.query_mode].
            DML statements always produce stats containing the number of
            rows modified, unless executed using the
            [ExecuteSqlRequest.QueryMode.PLAN][google.spanner.v1.ExecuteSqlRequest.QueryMode.PLAN]
            [ExecuteSqlRequest.query_mode][google.spanner.v1.ExecuteSqlRequest.query_mode].
            Other fields may or may not be populated, based on the
            [ExecuteSqlRequest.query_mode][google.spanner.v1.ExecuteSqlRequest.query_mode].
    """

    metadata: 'ResultSetMetadata' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='ResultSetMetadata',
    )
    rows: MutableSequence[struct_pb2.ListValue] = proto.RepeatedField(
        proto.MESSAGE,
        number=2,
        message=struct_pb2.ListValue,
    )
    stats: 'ResultSetStats' = proto.Field(
        proto.MESSAGE,
        number=3,
        message='ResultSetStats',
    )


class PartialResultSet(proto.Message):
    r"""Partial results from a streaming read or SQL query. Streaming
    reads and SQL queries better tolerate large result sets, large
    rows, and large values, but are a little trickier to consume.

    Attributes:
        metadata (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.ResultSetMetadata):
            Metadata about the result set, such as row
            type information. Only present in the first
            response.
        values (MutableSequence[google.protobuf.struct_pb2.Value]):
            A streamed result set consists of a stream of values, which
            might be split into many ``PartialResultSet`` messages to
            accommodate large rows and/or large values. Every N complete
            values defines a row, where N is equal to the number of
            entries in
            [metadata.row_type.fields][google.spanner.v1.StructType.fields].

            Most values are encoded based on type as described
            [here][google.spanner.v1.TypeCode].

            It is possible that the last value in values is "chunked",
            meaning that the rest of the value is sent in subsequent
            ``PartialResultSet``\ (s). This is denoted by the
            [chunked_value][google.spanner.v1.PartialResultSet.chunked_value]
            field. Two or more chunked values can be merged to form a
            complete value as follows:

            -  ``bool/number/null``: cannot be chunked
            -  ``string``: concatenate the strings
            -  ``list``: concatenate the lists. If the last element in a
               list is a ``string``, ``list``, or ``object``, merge it
               with the first element in the next list by applying these
               rules recursively.
            -  ``object``: concatenate the (field name, field value)
               pairs. If a field name is duplicated, then apply these
               rules recursively to merge the field values.

            Some examples of merging:

            ::

                # Strings are concatenated.
                "foo", "bar" => "foobar"

                # Lists of non-strings are concatenated.
                [2, 3], [4] => [2, 3, 4]

                # Lists are concatenated, but the last and first elements are merged
                # because they are strings.
                ["a", "b"], ["c", "d"] => ["a", "bc", "d"]

                # Lists are concatenated, but the last and first elements are merged
                # because they are lists. Recursively, the last and first elements
                # of the inner lists are merged because they are strings.
                ["a", ["b", "c"]], [["d"], "e"] => ["a", ["b", "cd"], "e"]

                # Non-overlapping object fields are combined.
                {"a": "1"}, {"b": "2"} => {"a": "1", "b": 2"}

                # Overlapping object fields are merged.
                {"a": "1"}, {"a": "2"} => {"a": "12"}

                # Examples of merging objects containing lists of strings.
                {"a": ["1"]}, {"a": ["2"]} => {"a": ["12"]}

            For a more complete example, suppose a streaming SQL query
            is yielding a result set whose rows contain a single string
            field. The following ``PartialResultSet``\ s might be
            yielded:

            ::

                {
                  "metadata": { ... }
                  "values": ["Hello", "W"]
                  "chunked_value": true
                  "resume_token": "Af65..."
                }
                {
                  "values": ["orl"]
                  "chunked_value": true
                }
                {
                  "values": ["d"]
                  "resume_token": "Zx1B..."
                }

            This sequence of ``PartialResultSet``\ s encodes two rows,
            one containing the field value ``"Hello"``, and a second
            containing the field value ``"World" = "W" + "orl" + "d"``.

            Not all ``PartialResultSet``\ s contain a ``resume_token``.
            Execution can only be resumed from a previously yielded
            ``resume_token``. For the above sequence of
            ``PartialResultSet``\ s, resuming the query with
            ``"resume_token": "Af65..."`` will yield results from the
            ``PartialResultSet`` with value ``["orl"]``.
        chunked_value (bool):
            If true, then the final value in
            [values][google.spanner.v1.PartialResultSet.values] is
            chunked, and must be combined with more values from
            subsequent ``PartialResultSet``\ s to obtain a complete
            field value.
        resume_token (bytes):
            Streaming calls might be interrupted for a variety of
            reasons, such as TCP connection loss. If this occurs, the
            stream of results can be resumed by re-sending the original
            request and including ``resume_token``. Note that executing
            any other transaction in the same session invalidates the
            token.
        stats (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.ResultSetStats):
            Query plan and execution statistics for the statement that
            produced this streaming result set. These can be requested
            by setting
            [ExecuteSqlRequest.query_mode][google.spanner.v1.ExecuteSqlRequest.query_mode]
            and are sent only once with the last response in the stream.
            This field will also be present in the last response for DML
            statements.
    """

    metadata: 'ResultSetMetadata' = proto.Field(
        proto.MESSAGE,
        number=1,
        message='ResultSetMetadata',
    )
    values: MutableSequence[struct_pb2.Value] = proto.RepeatedField(
        proto.MESSAGE,
        number=2,
        message=struct_pb2.Value,
    )
    chunked_value: bool = proto.Field(
        proto.BOOL,
        number=3,
    )
    resume_token: bytes = proto.Field(
        proto.BYTES,
        number=4,
    )
    stats: 'ResultSetStats' = proto.Field(
        proto.MESSAGE,
        number=5,
        message='ResultSetStats',
    )


class ResultSetMetadata(proto.Message):
    r"""Metadata about a [ResultSet][google.spanner.v1.ResultSet] or
    [PartialResultSet][google.spanner.v1.PartialResultSet].

    Attributes:
        row_type (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.StructType):
            Indicates the field names and types for the rows in the
            result set. For example, a SQL query like
            ``"SELECT UserId, UserName FROM Users"`` could return a
            ``row_type`` value like:

            ::

                "fields": [
                  { "name": "UserId", "type": { "code": "INT64" } },
                  { "name": "UserName", "type": { "code": "STRING" } },
                ]
        transaction (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.Transaction):
            If the read or SQL query began a transaction
            as a side-effect, the information about the new
            transaction is yielded here.
        undeclared_parameters (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.StructType):
            A SQL query can be parameterized. In PLAN mode, these
            parameters can be undeclared. This indicates the field names
            and types for those undeclared parameters in the SQL query.
            For example, a SQL query like
            ``"SELECT * FROM Users where UserId = @userId and UserName = @userName "``
            could return a ``undeclared_parameters`` value like:

            ::

                "fields": [
                  { "name": "UserId", "type": { "code": "INT64" } },
                  { "name": "UserName", "type": { "code": "STRING" } },
                ]
    """

    row_type: gs_type.StructType = proto.Field(
        proto.MESSAGE,
        number=1,
        message=gs_type.StructType,
    )
    transaction: gs_transaction.Transaction = proto.Field(
        proto.MESSAGE,
        number=2,
        message=gs_transaction.Transaction,
    )
    undeclared_parameters: gs_type.StructType = proto.Field(
        proto.MESSAGE,
        number=3,
        message=gs_type.StructType,
    )


class ResultSetStats(proto.Message):
    r"""Additional statistics about a
    [ResultSet][google.spanner.v1.ResultSet] or
    [PartialResultSet][google.spanner.v1.PartialResultSet].

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        query_plan (googlecloudsdk.generated_clients.gapic_clients.spanner_v1.types.QueryPlan):
            [QueryPlan][google.spanner.v1.QueryPlan] for the query
            associated with this result.
        query_stats (google.protobuf.struct_pb2.Struct):
            Aggregated statistics from the execution of the query. Only
            present when the query is profiled. For example, a query
            could return the statistics as follows:

            ::

                {
                  "rows_returned": "3",
                  "elapsed_time": "1.22 secs",
                  "cpu_time": "1.19 secs"
                }
        row_count_exact (int):
            Standard DML returns an exact count of rows
            that were modified.

            This field is a member of `oneof`_ ``row_count``.
        row_count_lower_bound (int):
            Partitioned DML does not offer exactly-once
            semantics, so it returns a lower bound of the
            rows modified.

            This field is a member of `oneof`_ ``row_count``.
    """

    query_plan: gs_query_plan.QueryPlan = proto.Field(
        proto.MESSAGE,
        number=1,
        message=gs_query_plan.QueryPlan,
    )
    query_stats: struct_pb2.Struct = proto.Field(
        proto.MESSAGE,
        number=2,
        message=struct_pb2.Struct,
    )
    row_count_exact: int = proto.Field(
        proto.INT64,
        number=3,
        oneof='row_count',
    )
    row_count_lower_bound: int = proto.Field(
        proto.INT64,
        number=4,
        oneof='row_count',
    )


__all__ = tuple(sorted(__protobuf__.manifest))

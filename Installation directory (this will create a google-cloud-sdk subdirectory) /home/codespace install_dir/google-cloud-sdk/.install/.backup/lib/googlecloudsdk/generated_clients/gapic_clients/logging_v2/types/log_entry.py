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

from google.api import monitored_resource_pb2  # type: ignore
from google.logging.type import http_request_pb2  # type: ignore
from google.logging.type import log_severity_pb2  # type: ignore
from cloudsdk.google.protobuf import any_pb2  # type: ignore
from cloudsdk.google.protobuf import struct_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore


__protobuf__ = proto.module(
    package='google.logging.v2',
    manifest={
        'LogEntry',
        'LogErrorGroup',
        'LogEntryOperation',
        'LogEntrySourceLocation',
        'LogSplit',
    },
)


class LogEntry(proto.Message):
    r"""An individual entry in a log.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        log_name (str):
            Required. The resource name of the log to which this log
            entry belongs:

            ::

                "projects/[PROJECT_ID]/logs/[LOG_ID]"
                "organizations/[ORGANIZATION_ID]/logs/[LOG_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/logs/[LOG_ID]"
                "folders/[FOLDER_ID]/logs/[LOG_ID]"

            A project number may be used in place of PROJECT_ID. The
            project number is translated to its corresponding PROJECT_ID
            internally and the ``log_name`` field will contain
            PROJECT_ID in queries and exports.

            ``[LOG_ID]`` must be URL-encoded within ``log_name``.
            Example:
            ``"organizations/1234567890/logs/cloudresourcemanager.googleapis.com%2Factivity"``.

            ``[LOG_ID]`` must be less than 512 characters long and can
            only include the following characters: upper and lower case
            alphanumeric characters, forward-slash, underscore, hyphen,
            and period.

            For backward compatibility, if ``log_name`` begins with a
            forward-slash, such as ``/projects/...``, then the log entry
            is processed as usual, but the forward-slash is removed.
            Listing the log entry will not show the leading slash and
            filtering for a log name with a leading slash will never
            return any results.
        resource (google.api.monitored_resource_pb2.MonitoredResource):
            Required. The monitored resource that
            produced this log entry.
            Example: a log entry that reports a database
            error would be associated with the monitored
            resource designating the particular database
            that reported the error.
        proto_payload (google.protobuf.any_pb2.Any):
            The log entry payload, represented as a
            protocol buffer. Some Google Cloud Platform
            services use this field for their log entry
            payloads.

            The following protocol buffer types are
            supported; user-defined types are not supported:

            "type.googleapis.com/google.cloud.audit.AuditLog"
            "type.googleapis.com/google.appengine.logging.v1.RequestLog".

            This field is a member of `oneof`_ ``payload``.
        text_payload (str):
            The log entry payload, represented as a
            Unicode string (UTF-8).

            This field is a member of `oneof`_ ``payload``.
        json_payload (google.protobuf.struct_pb2.Struct):
            The log entry payload, represented as a
            structure that is expressed as a JSON object.

            This field is a member of `oneof`_ ``payload``.
        timestamp (google.protobuf.timestamp_pb2.Timestamp):
            Optional. The time the event described by the log entry
            occurred. This time is used to compute the log entry's age
            and to enforce the logs retention period. If this field is
            omitted in a new log entry, then Logging assigns it the
            current time. Timestamps have nanosecond accuracy, but
            trailing zeros in the fractional seconds might be omitted
            when the timestamp is displayed.

            Incoming log entries must have timestamps that don't exceed
            the `logs retention
            period <https://cloud.google.com/logging/quotas#logs_retention_periods>`__
            in the past, and that don't exceed 24 hours in the future.
            Log entries outside those time boundaries are rejected by
            Logging.
        receive_timestamp (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The time the log entry was
            received by Logging.
        severity (google.logging.type.log_severity_pb2.LogSeverity):
            Optional. The severity of the log entry. The default value
            is ``LogSeverity.DEFAULT``.
        insert_id (str):
            Optional. A unique identifier for the log entry. If you
            provide a value, then Logging considers other log entries in
            the same project, with the same ``timestamp``, and with the
            same ``insert_id`` to be duplicates which are removed in a
            single query result. However, there are no guarantees of
            de-duplication in the export of logs.

            If the ``insert_id`` is omitted when writing a log entry,
            the Logging API assigns its own unique identifier in this
            field.

            In queries, the ``insert_id`` is also used to order log
            entries that have the same ``log_name`` and ``timestamp``
            values.
        http_request (google.logging.type.http_request_pb2.HttpRequest):
            Optional. Information about the HTTP request
            associated with this log entry, if applicable.
        labels (MutableMapping[str, str]):
            Optional. A map of key, value pairs that provides additional
            information about the log entry. The labels can be
            user-defined or system-defined.

            User-defined labels are arbitrary key, value pairs that you
            can use to classify logs.

            System-defined labels are defined by GCP services for
            platform logs. They have two components - a service
            namespace component and the attribute name. For example:
            ``compute.googleapis.com/resource_name``.

            Cloud Logging truncates label keys that exceed 512 B and
            label values that exceed 64 KB upon their associated log
            entry being written. The truncation is indicated by an
            ellipsis at the end of the character string.
        metadata (google.api.monitored_resource_pb2.MonitoredResourceMetadata):
            Output only. Deprecated. This field is not
            used by Logging. Any value written to it is
            cleared.
        operation (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogEntryOperation):
            Optional. Information about an operation
            associated with the log entry, if applicable.
        trace (str):
            Optional. The REST resource name of the trace being written
            to `Cloud Trace <https://cloud.google.com/trace>`__ in
            association with this log entry. For example, if your trace
            data is stored in the Cloud project "my-trace-project" and
            if the service that is creating the log entry receives a
            trace header that includes the trace ID "12345", then the
            service should use "projects/my-trace-project/traces/12345".

            The ``trace`` field provides the link between logs and
            traces. By using this field, you can navigate from a log
            entry to a trace.
        span_id (str):
            Optional. The ID of the `Cloud
            Trace <https://cloud.google.com/trace>`__ span associated
            with the current operation in which the log is being
            written. For example, if a span has the REST resource name
            of
            "projects/some-project/traces/some-trace/spans/some-span-id",
            then the ``span_id`` field is "some-span-id".

            A
            `Span <https://cloud.google.com/trace/docs/reference/v2/rest/v2/projects.traces/batchWrite#Span>`__
            represents a single operation within a trace. Whereas a
            trace may involve multiple different microservices running
            on multiple different machines, a span generally corresponds
            to a single logical operation being performed in a single
            instance of a microservice on one specific machine. Spans
            are the nodes within the tree that is a trace.

            Applications that are `instrumented for
            tracing <https://cloud.google.com/trace/docs/setup>`__ will
            generally assign a new, unique span ID on each incoming
            request. It is also common to create and record additional
            spans corresponding to internal processing elements as well
            as issuing requests to dependencies.

            The span ID is expected to be a 16-character, hexadecimal
            encoding of an 8-byte array and should not be zero. It
            should be unique within the trace and should, ideally, be
            generated in a manner that is uniformly random.

            Example values:

            -  ``000000000000004a``
            -  ``7a2190356c3fc94b``
            -  ``0000f00300090021``
            -  ``d39223e101960076``
        trace_sampled (bool):
            Optional. The sampling decision of the span associated with
            the log entry at the time the log entry was created. This
            field corresponds to `the sampled flag in the W3C
            trace-context
            specification <https://www.w3.org/TR/trace-context/#sampled-flag>`__.
            A non-sampled ``trace`` value is still useful as a request
            correlation identifier. The default is False.
        source_location (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogEntrySourceLocation):
            Optional. Source code location information
            associated with the log entry, if any.
        split (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogSplit):
            Optional. Information indicating this
            LogEntry is part of a sequence of multiple log
            entries split from a single LogEntry.
        error_groups (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogErrorGroup]):
            Output only. The `Error
            Reporting <https://cloud.google.com/error-reporting>`__
            error groups associated with this LogEntry. Error Reporting
            sets the values for this field during error group creation.

            For more information, see `View error
            details <https://cloud.google.com/error-reporting/docs/viewing-errors#view_error_details>`__

            This field isn't available during `log
            routing <https://cloud.google.com/logging/docs/routing/overview>`__
    """

    log_name: str = proto.Field(
        proto.STRING,
        number=12,
    )
    resource: monitored_resource_pb2.MonitoredResource = proto.Field(
        proto.MESSAGE,
        number=8,
        message=monitored_resource_pb2.MonitoredResource,
    )
    proto_payload: any_pb2.Any = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof='payload',
        message=any_pb2.Any,
    )
    text_payload: str = proto.Field(
        proto.STRING,
        number=3,
        oneof='payload',
    )
    json_payload: struct_pb2.Struct = proto.Field(
        proto.MESSAGE,
        number=6,
        oneof='payload',
        message=struct_pb2.Struct,
    )
    timestamp: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=9,
        message=timestamp_pb2.Timestamp,
    )
    receive_timestamp: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=24,
        message=timestamp_pb2.Timestamp,
    )
    severity: log_severity_pb2.LogSeverity = proto.Field(
        proto.ENUM,
        number=10,
        enum=log_severity_pb2.LogSeverity,
    )
    insert_id: str = proto.Field(
        proto.STRING,
        number=4,
    )
    http_request: http_request_pb2.HttpRequest = proto.Field(
        proto.MESSAGE,
        number=7,
        message=http_request_pb2.HttpRequest,
    )
    labels: MutableMapping[str, str] = proto.MapField(
        proto.STRING,
        proto.STRING,
        number=11,
    )
    metadata: monitored_resource_pb2.MonitoredResourceMetadata = proto.Field(
        proto.MESSAGE,
        number=25,
        message=monitored_resource_pb2.MonitoredResourceMetadata,
    )
    operation: 'LogEntryOperation' = proto.Field(
        proto.MESSAGE,
        number=15,
        message='LogEntryOperation',
    )
    trace: str = proto.Field(
        proto.STRING,
        number=22,
    )
    span_id: str = proto.Field(
        proto.STRING,
        number=27,
    )
    trace_sampled: bool = proto.Field(
        proto.BOOL,
        number=30,
    )
    source_location: 'LogEntrySourceLocation' = proto.Field(
        proto.MESSAGE,
        number=23,
        message='LogEntrySourceLocation',
    )
    split: 'LogSplit' = proto.Field(
        proto.MESSAGE,
        number=35,
        message='LogSplit',
    )
    error_groups: MutableSequence['LogErrorGroup'] = proto.RepeatedField(
        proto.MESSAGE,
        number=36,
        message='LogErrorGroup',
    )


class LogErrorGroup(proto.Message):
    r"""Contains metadata that associates the LogEntry to Error
    Reporting error groups.

    Attributes:
        id (str):
            The id is a unique identifier for a particular error group;
            it is the last part of the error group resource name:
            ``/project/[PROJECT_ID]/errors/[ERROR_GROUP_ID]``. Example:
            ``COShysOX0r_51QE``. The id is derived from key parts of the
            error-log content and is treated as Service Data. For
            information about how Service Data is handled, see `Google
            Cloud Privacy
            Notice <https://cloud.google.com/terms/cloud-privacy-notice>`__.
    """

    id: str = proto.Field(
        proto.STRING,
        number=1,
    )


class LogEntryOperation(proto.Message):
    r"""Additional information about a potentially long-running
    operation with which a log entry is associated.

    Attributes:
        id (str):
            Optional. An arbitrary operation identifier.
            Log entries with the same identifier are assumed
            to be part of the same operation.
        producer (str):
            Optional. An arbitrary producer identifier. The combination
            of ``id`` and ``producer`` must be globally unique. Examples
            for ``producer``: ``"MyDivision.MyBigCompany.com"``,
            ``"github.com/MyProject/MyApplication"``.
        first (bool):
            Optional. Set this to True if this is the
            first log entry in the operation.
        last (bool):
            Optional. Set this to True if this is the
            last log entry in the operation.
    """

    id: str = proto.Field(
        proto.STRING,
        number=1,
    )
    producer: str = proto.Field(
        proto.STRING,
        number=2,
    )
    first: bool = proto.Field(
        proto.BOOL,
        number=3,
    )
    last: bool = proto.Field(
        proto.BOOL,
        number=4,
    )


class LogEntrySourceLocation(proto.Message):
    r"""Additional information about the source code location that
    produced the log entry.

    Attributes:
        file (str):
            Optional. Source file name. Depending on the
            runtime environment, this might be a simple name
            or a fully-qualified name.
        line (int):
            Optional. Line within the source file.
            1-based; 0 indicates no line number available.
        function (str):
            Optional. Human-readable name of the function or method
            being invoked, with optional context such as the class or
            package name. This information may be used in contexts such
            as the logs viewer, where a file and line number are less
            meaningful. The format can vary by language. For example:
            ``qual.if.ied.Class.method`` (Java), ``dir/package.func``
            (Go), ``function`` (Python).
    """

    file: str = proto.Field(
        proto.STRING,
        number=1,
    )
    line: int = proto.Field(
        proto.INT64,
        number=2,
    )
    function: str = proto.Field(
        proto.STRING,
        number=3,
    )


class LogSplit(proto.Message):
    r"""Additional information used to correlate multiple log
    entries. Used when a single LogEntry would exceed the Google
    Cloud Logging size limit and is split across multiple log
    entries.

    Attributes:
        uid (str):
            A globally unique identifier for all log entries in a
            sequence of split log entries. All log entries with the same
            \|LogSplit.uid\| are assumed to be part of the same sequence
            of split log entries.
        index (int):
            The index of this LogEntry in the sequence of split log
            entries. Log entries are given \|index\| values 0, 1, ...,
            n-1 for a sequence of n log entries.
        total_splits (int):
            The total number of log entries that the
            original LogEntry was split into.
    """

    uid: str = proto.Field(
        proto.STRING,
        number=1,
    )
    index: int = proto.Field(
        proto.INT32,
        number=2,
    )
    total_splits: int = proto.Field(
        proto.INT32,
        number=3,
    )


__all__ = tuple(sorted(__protobuf__.manifest))

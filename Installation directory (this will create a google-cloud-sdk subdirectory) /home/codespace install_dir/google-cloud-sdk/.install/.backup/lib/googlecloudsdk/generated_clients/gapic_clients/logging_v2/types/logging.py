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
from cloudsdk.google.protobuf import duration_pb2  # type: ignore
from google.rpc import status_pb2  # type: ignore
from googlecloudsdk.generated_clients.gapic_clients.logging_v2.types import log_entry


__protobuf__ = proto.module(
    package='google.logging.v2',
    manifest={
        'DeleteLogRequest',
        'WriteLogEntriesRequest',
        'WriteLogEntriesResponse',
        'WriteLogEntriesPartialErrors',
        'ListLogEntriesRequest',
        'ListLogEntriesResponse',
        'ListMonitoredResourceDescriptorsRequest',
        'ListMonitoredResourceDescriptorsResponse',
        'ListLogsRequest',
        'ListLogsResponse',
        'TailLogEntriesRequest',
        'TailLogEntriesResponse',
    },
)


class DeleteLogRequest(proto.Message):
    r"""The parameters to DeleteLog.

    Attributes:
        log_name (str):
            Required. The resource name of the log to delete:

            -  ``projects/[PROJECT_ID]/logs/[LOG_ID]``
            -  ``organizations/[ORGANIZATION_ID]/logs/[LOG_ID]``
            -  ``billingAccounts/[BILLING_ACCOUNT_ID]/logs/[LOG_ID]``
            -  ``folders/[FOLDER_ID]/logs/[LOG_ID]``

            ``[LOG_ID]`` must be URL-encoded. For example,
            ``"projects/my-project-id/logs/syslog"``,
            ``"organizations/123/logs/cloudaudit.googleapis.com%2Factivity"``.

            For more information about log names, see
            [LogEntry][google.logging.v2.LogEntry].
    """

    log_name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class WriteLogEntriesRequest(proto.Message):
    r"""The parameters to WriteLogEntries.

    Attributes:
        log_name (str):
            Optional. A default log resource name that is assigned to
            all log entries in ``entries`` that do not specify a value
            for ``log_name``:

            -  ``projects/[PROJECT_ID]/logs/[LOG_ID]``
            -  ``organizations/[ORGANIZATION_ID]/logs/[LOG_ID]``
            -  ``billingAccounts/[BILLING_ACCOUNT_ID]/logs/[LOG_ID]``
            -  ``folders/[FOLDER_ID]/logs/[LOG_ID]``

            ``[LOG_ID]`` must be URL-encoded. For example:

            ::

                "projects/my-project-id/logs/syslog"
                "organizations/123/logs/cloudaudit.googleapis.com%2Factivity"

            The permission ``logging.logEntries.create`` is needed on
            each project, organization, billing account, or folder that
            is receiving new log entries, whether the resource is
            specified in ``logName`` or in an individual log entry.
        resource (google.api.monitored_resource_pb2.MonitoredResource):
            Optional. A default monitored resource object that is
            assigned to all log entries in ``entries`` that do not
            specify a value for ``resource``. Example:

            ::

                { "type": "gce_instance",
                  "labels": {
                    "zone": "us-central1-a", "instance_id": "00000000000000000000" }}

            See [LogEntry][google.logging.v2.LogEntry].
        labels (MutableMapping[str, str]):
            Optional. Default labels that are added to the ``labels``
            field of all log entries in ``entries``. If a log entry
            already has a label with the same key as a label in this
            parameter, then the log entry's label is not changed. See
            [LogEntry][google.logging.v2.LogEntry].
        entries (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogEntry]):
            Required. The log entries to send to Logging. The order of
            log entries in this list does not matter. Values supplied in
            this method's ``log_name``, ``resource``, and ``labels``
            fields are copied into those log entries in this list that
            do not include values for their corresponding fields. For
            more information, see the
            [LogEntry][google.logging.v2.LogEntry] type.

            If the ``timestamp`` or ``insert_id`` fields are missing in
            log entries, then this method supplies the current time or a
            unique identifier, respectively. The supplied values are
            chosen so that, among the log entries that did not supply
            their own values, the entries earlier in the list will sort
            before the entries later in the list. See the
            ``entries.list`` method.

            Log entries with timestamps that are more than the `logs
            retention
            period <https://cloud.google.com/logging/quotas>`__ in the
            past or more than 24 hours in the future will not be
            available when calling ``entries.list``. However, those log
            entries can still be `exported with
            LogSinks <https://cloud.google.com/logging/docs/api/tasks/exporting-logs>`__.

            To improve throughput and to avoid exceeding the `quota
            limit <https://cloud.google.com/logging/quotas>`__ for calls
            to ``entries.write``, you should try to include several log
            entries in this list, rather than calling this method for
            each individual log entry.
        partial_success (bool):
            Optional. Whether a batch's valid entries should be written
            even if some other entry failed due to a permanent error
            such as INVALID_ARGUMENT or PERMISSION_DENIED. If any entry
            failed, then the response status is the response status of
            one of the failed entries. The response will include error
            details in ``WriteLogEntriesPartialErrors.log_entry_errors``
            keyed by the entries' zero-based index in the ``entries``.
            Failed requests for which no entries are written will not
            include per-entry errors.
        dry_run (bool):
            Optional. If true, the request should expect
            normal response, but the entries won't be
            persisted nor exported. Useful for checking
            whether the logging API endpoints are working
            properly before sending valuable data.
    """

    log_name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    resource: monitored_resource_pb2.MonitoredResource = proto.Field(
        proto.MESSAGE,
        number=2,
        message=monitored_resource_pb2.MonitoredResource,
    )
    labels: MutableMapping[str, str] = proto.MapField(
        proto.STRING,
        proto.STRING,
        number=3,
    )
    entries: MutableSequence[log_entry.LogEntry] = proto.RepeatedField(
        proto.MESSAGE,
        number=4,
        message=log_entry.LogEntry,
    )
    partial_success: bool = proto.Field(
        proto.BOOL,
        number=5,
    )
    dry_run: bool = proto.Field(
        proto.BOOL,
        number=6,
    )


class WriteLogEntriesResponse(proto.Message):
    r"""Result returned from WriteLogEntries.
    """


class WriteLogEntriesPartialErrors(proto.Message):
    r"""Error details for WriteLogEntries with partial success.

    Attributes:
        log_entry_errors (MutableMapping[int, google.rpc.status_pb2.Status]):
            When ``WriteLogEntriesRequest.partial_success`` is true,
            records the error status for entries that were not written
            due to a permanent error, keyed by the entry's zero-based
            index in ``WriteLogEntriesRequest.entries``.

            Failed requests for which no entries are written will not
            include per-entry errors.
    """

    log_entry_errors: MutableMapping[int, status_pb2.Status] = proto.MapField(
        proto.INT32,
        proto.MESSAGE,
        number=1,
        message=status_pb2.Status,
    )


class ListLogEntriesRequest(proto.Message):
    r"""The parameters to ``ListLogEntries``.

    Attributes:
        project_ids (MutableSequence[str]):
            Optional. Deprecated. Use ``resource_names`` instead. One or
            more project identifiers or project numbers from which to
            retrieve log entries. Example: ``"my-project-1A"``.
        resource_names (MutableSequence[str]):
            Required. Names of one or more parent resources from which
            to retrieve log entries:

            -  ``projects/[PROJECT_ID]``
            -  ``organizations/[ORGANIZATION_ID]``
            -  ``billingAccounts/[BILLING_ACCOUNT_ID]``
            -  ``folders/[FOLDER_ID]``

            May alternatively be one or more views:

            -  ``projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``
            -  ``organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``
            -  ``billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``
            -  ``folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``

            Projects listed in the ``project_ids`` field are added to
            this list. A maximum of 100 resources may be specified in a
            single request.
        filter (str):
            Optional. A filter that chooses which log entries to return.
            For more information, see [Logging query language]
            (https://cloud.google.com/logging/docs/view/logging-query-language).

            Only log entries that match the filter are returned. An
            empty filter matches all log entries in the resources listed
            in ``resource_names``. Referencing a parent resource that is
            not listed in ``resource_names`` will cause the filter to
            return no results. The maximum length of a filter is 20,000
            characters.
        order_by (str):
            Optional. How the results should be sorted. Presently, the
            only permitted values are ``"timestamp asc"`` (default) and
            ``"timestamp desc"``. The first option returns entries in
            order of increasing values of ``LogEntry.timestamp`` (oldest
            first), and the second option returns entries in order of
            decreasing timestamps (newest first). Entries with equal
            timestamps are returned in order of their ``insert_id``
            values.
        page_size (int):
            Optional. The maximum number of results to return from this
            request. Default is 50. If the value is negative, the
            request is rejected.

            The presence of ``next_page_token`` in the response
            indicates that more results might be available.
        page_token (str):
            Optional. If present, then retrieve the next batch of
            results from the preceding call to this method.
            ``page_token`` must be the value of ``next_page_token`` from
            the previous response. The values of other method parameters
            should be identical to those in the previous call.
    """

    project_ids: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=1,
    )
    resource_names: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=8,
    )
    filter: str = proto.Field(
        proto.STRING,
        number=2,
    )
    order_by: str = proto.Field(
        proto.STRING,
        number=3,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=4,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=5,
    )


class ListLogEntriesResponse(proto.Message):
    r"""Result returned from ``ListLogEntries``.

    Attributes:
        entries (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogEntry]):
            A list of log entries. If ``entries`` is empty,
            ``nextPageToken`` may still be returned, indicating that
            more entries may exist. See ``nextPageToken`` for more
            information.
        next_page_token (str):
            If there might be more results than those appearing in this
            response, then ``nextPageToken`` is included. To get the
            next set of results, call this method again using the value
            of ``nextPageToken`` as ``pageToken``.

            If a value for ``next_page_token`` appears and the
            ``entries`` field is empty, it means that the search found
            no log entries so far but it did not have time to search all
            the possible log entries. Retry the method with this value
            for ``page_token`` to continue the search. Alternatively,
            consider speeding up the search by changing your filter to
            specify a single log name or resource type, or to narrow the
            time range of the search.
    """

    @property
    def raw_page(self):
        return self

    entries: MutableSequence[log_entry.LogEntry] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message=log_entry.LogEntry,
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class ListMonitoredResourceDescriptorsRequest(proto.Message):
    r"""The parameters to ListMonitoredResourceDescriptors

    Attributes:
        page_size (int):
            Optional. The maximum number of results to return from this
            request. Non-positive values are ignored. The presence of
            ``nextPageToken`` in the response indicates that more
            results might be available.
        page_token (str):
            Optional. If present, then retrieve the next batch of
            results from the preceding call to this method.
            ``pageToken`` must be the value of ``nextPageToken`` from
            the previous response. The values of other method parameters
            should be identical to those in the previous call.
    """

    page_size: int = proto.Field(
        proto.INT32,
        number=1,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class ListMonitoredResourceDescriptorsResponse(proto.Message):
    r"""Result returned from ListMonitoredResourceDescriptors.

    Attributes:
        resource_descriptors (MutableSequence[google.api.monitored_resource_pb2.MonitoredResourceDescriptor]):
            A list of resource descriptors.
        next_page_token (str):
            If there might be more results than those appearing in this
            response, then ``nextPageToken`` is included. To get the
            next set of results, call this method again using the value
            of ``nextPageToken`` as ``pageToken``.
    """

    @property
    def raw_page(self):
        return self

    resource_descriptors: MutableSequence[monitored_resource_pb2.MonitoredResourceDescriptor] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message=monitored_resource_pb2.MonitoredResourceDescriptor,
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class ListLogsRequest(proto.Message):
    r"""The parameters to ListLogs.

    Attributes:
        parent (str):
            Required. The resource name to list logs for:

            -  ``projects/[PROJECT_ID]``
            -  ``organizations/[ORGANIZATION_ID]``
            -  ``billingAccounts/[BILLING_ACCOUNT_ID]``
            -  ``folders/[FOLDER_ID]``
        resource_names (MutableSequence[str]):
            Optional. List of resource names to list logs for:

            -  ``projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``
            -  ``organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``
            -  ``billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``
            -  ``folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``

            To support legacy queries, it could also be:

            -  ``projects/[PROJECT_ID]``
            -  ``organizations/[ORGANIZATION_ID]``
            -  ``billingAccounts/[BILLING_ACCOUNT_ID]``
            -  ``folders/[FOLDER_ID]``

            The resource name in the ``parent`` field is added to this
            list.
        page_size (int):
            Optional. The maximum number of results to return from this
            request. Non-positive values are ignored. The presence of
            ``nextPageToken`` in the response indicates that more
            results might be available.
        page_token (str):
            Optional. If present, then retrieve the next batch of
            results from the preceding call to this method.
            ``pageToken`` must be the value of ``nextPageToken`` from
            the previous response. The values of other method parameters
            should be identical to those in the previous call.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    resource_names: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=8,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=2,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=3,
    )


class ListLogsResponse(proto.Message):
    r"""Result returned from ListLogs.

    Attributes:
        log_names (MutableSequence[str]):
            A list of log names. For example,
            ``"projects/my-project/logs/syslog"`` or
            ``"organizations/123/logs/cloudresourcemanager.googleapis.com%2Factivity"``.
        next_page_token (str):
            If there might be more results than those appearing in this
            response, then ``nextPageToken`` is included. To get the
            next set of results, call this method again using the value
            of ``nextPageToken`` as ``pageToken``.
    """

    @property
    def raw_page(self):
        return self

    log_names: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=3,
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class TailLogEntriesRequest(proto.Message):
    r"""The parameters to ``TailLogEntries``.

    Attributes:
        resource_names (MutableSequence[str]):
            Required. Name of a parent resource from which to retrieve
            log entries:

            -  ``projects/[PROJECT_ID]``
            -  ``organizations/[ORGANIZATION_ID]``
            -  ``billingAccounts/[BILLING_ACCOUNT_ID]``
            -  ``folders/[FOLDER_ID]``

            May alternatively be one or more views:

            -  ``projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``
            -  ``organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``
            -  ``billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``
            -  ``folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]``
        filter (str):
            Optional. Only log entries that match the filter are
            returned. An empty filter matches all log entries in the
            resources listed in ``resource_names``. Referencing a parent
            resource that is not listed in ``resource_names`` will cause
            the filter to return no results. The maximum length of a
            filter is 20,000 characters.
        buffer_window (google.protobuf.duration_pb2.Duration):
            Optional. The amount of time to buffer log
            entries at the server before being returned to
            prevent out of order results due to late
            arriving log entries. Valid values are between
            0-60000 milliseconds. Defaults to 2000
            milliseconds.
    """

    resource_names: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=1,
    )
    filter: str = proto.Field(
        proto.STRING,
        number=2,
    )
    buffer_window: duration_pb2.Duration = proto.Field(
        proto.MESSAGE,
        number=3,
        message=duration_pb2.Duration,
    )


class TailLogEntriesResponse(proto.Message):
    r"""Result returned from ``TailLogEntries``.

    Attributes:
        entries (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogEntry]):
            A list of log entries. Each response in the stream will
            order entries with increasing values of
            ``LogEntry.timestamp``. Ordering is not guaranteed between
            separate responses.
        suppression_info (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.TailLogEntriesResponse.SuppressionInfo]):
            If entries that otherwise would have been
            included in the session were not sent back to
            the client, counts of relevant entries omitted
            from the session with the reason that they were
            not included. There will be at most one of each
            reason per response. The counts represent the
            number of suppressed entries since the last
            streamed response.
    """

    class SuppressionInfo(proto.Message):
        r"""Information about entries that were omitted from the session.

        Attributes:
            reason (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.TailLogEntriesResponse.SuppressionInfo.Reason):
                The reason that entries were omitted from the
                session.
            suppressed_count (int):
                A lower bound on the count of entries omitted due to
                ``reason``.
        """
        class Reason(proto.Enum):
            r"""An indicator of why entries were omitted.

            Values:
                REASON_UNSPECIFIED (0):
                    Unexpected default.
                RATE_LIMIT (1):
                    Indicates suppression occurred due to relevant entries being
                    received in excess of rate limits. For quotas and limits,
                    see `Logging API quotas and
                    limits <https://cloud.google.com/logging/quotas#api-limits>`__.
                NOT_CONSUMED (2):
                    Indicates suppression occurred due to the
                    client not consuming responses quickly enough.
            """
            REASON_UNSPECIFIED = 0
            RATE_LIMIT = 1
            NOT_CONSUMED = 2

        reason: 'TailLogEntriesResponse.SuppressionInfo.Reason' = proto.Field(
            proto.ENUM,
            number=1,
            enum='TailLogEntriesResponse.SuppressionInfo.Reason',
        )
        suppressed_count: int = proto.Field(
            proto.INT32,
            number=2,
        )

    entries: MutableSequence[log_entry.LogEntry] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message=log_entry.LogEntry,
    )
    suppression_info: MutableSequence[SuppressionInfo] = proto.RepeatedField(
        proto.MESSAGE,
        number=2,
        message=SuppressionInfo,
    )


__all__ = tuple(sorted(__protobuf__.manifest))

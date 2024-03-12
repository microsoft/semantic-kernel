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

from cloudsdk.google.protobuf import field_mask_pb2  # type: ignore
from cloudsdk.google.protobuf import timestamp_pb2  # type: ignore


__protobuf__ = proto.module(
    package='google.logging.v2',
    manifest={
        'LifecycleState',
        'IndexType',
        'OperationState',
        'IndexConfig',
        'LogBucket',
        'LogView',
        'LogExclusion',
        'BigQueryOptions',
        'LogSink',
        'BigQueryDataset',
        'Link',
        'CmekSettings',
        'Settings',
        'LoggingQuery',
        'OpsAnalyticsQuery',
        'SavedQuery',
        'RecentQuery',
        'ListBucketsRequest',
        'ListBucketsResponse',
        'GetBucketRequest',
        'CreateBucketRequest',
        'UpdateBucketRequest',
        'DeleteBucketRequest',
        'UndeleteBucketRequest',
        'ListViewsRequest',
        'ListViewsResponse',
        'GetViewRequest',
        'CreateViewRequest',
        'UpdateViewRequest',
        'DeleteViewRequest',
        'ListExclusionsRequest',
        'ListExclusionsResponse',
        'GetExclusionRequest',
        'CreateExclusionRequest',
        'UpdateExclusionRequest',
        'DeleteExclusionRequest',
        'ListSinksRequest',
        'ListSinksResponse',
        'GetSinkRequest',
        'CreateSinkRequest',
        'UpdateSinkRequest',
        'DeleteSinkRequest',
        'ListLinksRequest',
        'ListLinksResponse',
        'GetLinkRequest',
        'CreateLinkRequest',
        'DeleteLinkRequest',
        'GetCmekSettingsRequest',
        'UpdateCmekSettingsRequest',
        'GetSettingsRequest',
        'UpdateSettingsRequest',
        'ListSavedQueriesRequest',
        'ListSavedQueriesResponse',
        'CreateSavedQueryRequest',
        'DeleteSavedQueryRequest',
        'ListRecentQueriesRequest',
        'ListRecentQueriesResponse',
        'CopyLogEntriesRequest',
        'CopyLogEntriesResponse',
        'CopyLogEntriesMetadata',
        'LocationMetadata',
        'BucketMetadata',
        'LinkMetadata',
    },
)


class LifecycleState(proto.Enum):
    r"""LogBucket lifecycle states.

    Values:
        LIFECYCLE_STATE_UNSPECIFIED (0):
            Unspecified state. This is only used/useful
            for distinguishing unset values.
        ACTIVE (1):
            The normal and active state.
        DELETE_REQUESTED (2):
            The resource has been marked for deletion by
            the user. For some resources (e.g. buckets),
            this can be reversed by an un-delete operation.
        UPDATING (3):
            The resource has been marked for an update by
            the user. It will remain in this state until the
            update is complete.
        CREATING (4):
            The resource has been marked for creation by
            the user. It will remain in this state until the
            creation is complete.
        FAILED (5):
            The resource is in an INTERNAL error state.
    """
    LIFECYCLE_STATE_UNSPECIFIED = 0
    ACTIVE = 1
    DELETE_REQUESTED = 2
    UPDATING = 3
    CREATING = 4
    FAILED = 5


class IndexType(proto.Enum):
    r"""IndexType is used for custom indexing. It describes the type
    of an indexed field.

    Values:
        INDEX_TYPE_UNSPECIFIED (0):
            The index's type is unspecified.
        INDEX_TYPE_STRING (1):
            The index is a string-type index.
        INDEX_TYPE_INTEGER (2):
            The index is a integer-type index.
    """
    INDEX_TYPE_UNSPECIFIED = 0
    INDEX_TYPE_STRING = 1
    INDEX_TYPE_INTEGER = 2


class OperationState(proto.Enum):
    r"""List of different operation states.
    High level state of the operation. This is used to report the
    job's current state to the user. Once a long running operation
    is created, the current state of the operation can be queried
    even before the operation is finished and the final result is
    available.

    Values:
        OPERATION_STATE_UNSPECIFIED (0):
            Should not be used.
        OPERATION_STATE_SCHEDULED (1):
            The operation is scheduled.
        OPERATION_STATE_WAITING_FOR_PERMISSIONS (2):
            Waiting for necessary permissions.
        OPERATION_STATE_RUNNING (3):
            The operation is running.
        OPERATION_STATE_SUCCEEDED (4):
            The operation was completed successfully.
        OPERATION_STATE_FAILED (5):
            The operation failed.
        OPERATION_STATE_CANCELLED (6):
            The operation was cancelled by the user.
        OPERATION_STATE_PENDING (7):
            The operation is waiting for quota.
    """
    OPERATION_STATE_UNSPECIFIED = 0
    OPERATION_STATE_SCHEDULED = 1
    OPERATION_STATE_WAITING_FOR_PERMISSIONS = 2
    OPERATION_STATE_RUNNING = 3
    OPERATION_STATE_SUCCEEDED = 4
    OPERATION_STATE_FAILED = 5
    OPERATION_STATE_CANCELLED = 6
    OPERATION_STATE_PENDING = 7


class IndexConfig(proto.Message):
    r"""Configuration for an indexed field.

    Attributes:
        field_path (str):
            Required. The LogEntry field path to index.

            Note that some paths are automatically indexed, and other
            paths are not eligible for indexing. See `indexing
            documentation <https://cloud.google.com/logging/docs/view/advanced-queries#indexed-fields>`__
            for details.

            For example: ``jsonPayload.request.status``
        type_ (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.IndexType):
            Required. The type of data in this index.
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The timestamp when the index was
            last modified.
            This is used to return the timestamp, and will
            be ignored if supplied during update.
    """

    field_path: str = proto.Field(
        proto.STRING,
        number=1,
    )
    type_: 'IndexType' = proto.Field(
        proto.ENUM,
        number=2,
        enum='IndexType',
    )
    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=3,
        message=timestamp_pb2.Timestamp,
    )


class LogBucket(proto.Message):
    r"""Describes a repository in which log entries are stored.

    Attributes:
        name (str):
            Output only. The resource name of the bucket.

            For example:

            ``projects/my-project/locations/global/buckets/my-bucket``

            For a list of supported locations, see `Supported
            Regions <https://cloud.google.com/logging/docs/region-support>`__

            For the location of ``global`` it is unspecified where log
            entries are actually stored.

            After a bucket has been created, the location cannot be
            changed.
        description (str):
            Optional. Describes this bucket.
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The creation timestamp of the
            bucket. This is not set for any of the default
            buckets.
        update_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The last update timestamp of the
            bucket.
        retention_days (int):
            Optional. Logs will be retained by default
            for this amount of time, after which they will
            automatically be deleted. The minimum retention
            period is 1 day. If this value is set to zero at
            bucket creation time, the default time of 30
            days will be used.
        locked (bool):
            Optional. Whether the bucket is locked.

            The retention period on a locked bucket cannot
            be changed. Locked buckets may only be deleted
            if they are empty.
        lifecycle_state (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LifecycleState):
            Output only. The bucket lifecycle state.
        analytics_enabled (bool):
            Optional. Whether log analytics is enabled
            for this bucket.
            Once enabled, log analytics features cannot be
            disabled.
        restricted_fields (MutableSequence[str]):
            Optional. Log entry field paths that are denied access in
            this bucket.

            The following fields and their children are eligible:
            ``textPayload``, ``jsonPayload``, ``protoPayload``,
            ``httpRequest``, ``labels``, ``sourceLocation``.

            Restricting a repeated field will restrict all values.
            Adding a parent will block all child fields. (e.g.
            ``foo.bar`` will block ``foo.bar.baz``)
        index_configs (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.IndexConfig]):
            Optional. A list of indexed fields and
            related configuration data.
        cmek_settings (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CmekSettings):
            Optional. The CMEK settings of the log
            bucket. If present, new log entries written to
            this log bucket are encrypted using the CMEK key
            provided in this configuration. If a log bucket
            has CMEK settings, the CMEK settings cannot be
            disabled later by updating the log bucket.
            Changing the KMS key is allowed.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    description: str = proto.Field(
        proto.STRING,
        number=3,
    )
    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=4,
        message=timestamp_pb2.Timestamp,
    )
    update_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=5,
        message=timestamp_pb2.Timestamp,
    )
    retention_days: int = proto.Field(
        proto.INT32,
        number=11,
    )
    locked: bool = proto.Field(
        proto.BOOL,
        number=9,
    )
    lifecycle_state: 'LifecycleState' = proto.Field(
        proto.ENUM,
        number=12,
        enum='LifecycleState',
    )
    analytics_enabled: bool = proto.Field(
        proto.BOOL,
        number=14,
    )
    restricted_fields: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=15,
    )
    index_configs: MutableSequence['IndexConfig'] = proto.RepeatedField(
        proto.MESSAGE,
        number=17,
        message='IndexConfig',
    )
    cmek_settings: 'CmekSettings' = proto.Field(
        proto.MESSAGE,
        number=19,
        message='CmekSettings',
    )


class LogView(proto.Message):
    r"""Describes a view over log entries in a bucket.

    Attributes:
        name (str):
            Output only. The resource name of the view.

            For example:

            ``projects/my-project/locations/global/buckets/my-bucket/views/my-view``
        description (str):
            Optional. Describes this view.
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The creation timestamp of the
            view.
        update_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The last update timestamp of the
            view.
        filter (str):
            Optional. Filter that restricts which log entries in a
            bucket are visible in this view.

            Filters must be logical conjunctions that use the AND
            operator, and they can use any of the following qualifiers:

            -  ``SOURCE()``, which specifies a project, folder,
               organization, or billing account of origin.
            -  ``resource.type``, which specifies the resource type.
            -  ``LOG_ID()``, which identifies the log.

            They can also use the negations of these qualifiers with the
            NOT operator.

            For example:

            SOURCE("projects/myproject") AND resource.type =
            "gce_instance" AND NOT LOG_ID("stdout")
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    description: str = proto.Field(
        proto.STRING,
        number=3,
    )
    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=4,
        message=timestamp_pb2.Timestamp,
    )
    update_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=5,
        message=timestamp_pb2.Timestamp,
    )
    filter: str = proto.Field(
        proto.STRING,
        number=7,
    )


class LogExclusion(proto.Message):
    r"""Specifies a set of log entries that are filtered out by a sink. If
    your Google Cloud resource receives a large volume of log entries,
    you can use exclusions to reduce your chargeable logs. Note that
    exclusions on organization-level and folder-level sinks don't apply
    to child resources. Note also that you cannot modify the \_Required
    sink or exclude logs from it.

    Attributes:
        name (str):
            Output only. A client-assigned identifier, such as
            ``"load-balancer-exclusion"``. Identifiers are limited to
            100 characters and can include only letters, digits,
            underscores, hyphens, and periods. First character has to be
            alphanumeric.
        description (str):
            Optional. A description of this exclusion.
        filter (str):
            Required. An `advanced logs
            filter <https://cloud.google.com/logging/docs/view/advanced-queries>`__
            that matches the log entries to be excluded. By using the
            `sample
            function <https://cloud.google.com/logging/docs/view/advanced-queries#sample>`__,
            you can exclude less than 100% of the matching log entries.

            For example, the following query matches 99% of low-severity
            log entries from Google Cloud Storage buckets:

            ``resource.type=gcs_bucket severity<ERROR sample(insertId, 0.99)``
        disabled (bool):
            Optional. If set to True, then this exclusion is disabled
            and it does not exclude any log entries. You can [update an
            exclusion][google.logging.v2.ConfigServiceV2.UpdateExclusion]
            to change the value of this field.
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The creation timestamp of the
            exclusion.
            This field may not be present for older
            exclusions.
        update_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The last update timestamp of the
            exclusion.
            This field may not be present for older
            exclusions.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    description: str = proto.Field(
        proto.STRING,
        number=2,
    )
    filter: str = proto.Field(
        proto.STRING,
        number=3,
    )
    disabled: bool = proto.Field(
        proto.BOOL,
        number=4,
    )
    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=5,
        message=timestamp_pb2.Timestamp,
    )
    update_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=6,
        message=timestamp_pb2.Timestamp,
    )


class BigQueryOptions(proto.Message):
    r"""Options that change functionality of a sink exporting data to
    BigQuery.

    Attributes:
        use_partitioned_tables (bool):
            Optional. Whether to use `BigQuery's partition
            tables <https://cloud.google.com/bigquery/docs/partitioned-tables>`__.
            By default, Cloud Logging creates dated tables based on the
            log entries' timestamps, e.g. syslog_20170523. With
            partitioned tables the date suffix is no longer present and
            `special query
            syntax <https://cloud.google.com/bigquery/docs/querying-partitioned-tables>`__
            has to be used instead. In both cases, tables are sharded
            based on UTC timezone.
        uses_timestamp_column_partitioning (bool):
            Output only. True if new timestamp column based partitioning
            is in use, false if legacy ingress-time partitioning is in
            use.

            All new sinks will have this field set true and will use
            timestamp column based partitioning. If
            use_partitioned_tables is false, this value has no meaning
            and will be false. Legacy sinks using partitioned tables
            will have this field set to false.
    """

    use_partitioned_tables: bool = proto.Field(
        proto.BOOL,
        number=1,
    )
    uses_timestamp_column_partitioning: bool = proto.Field(
        proto.BOOL,
        number=3,
    )


class LogSink(proto.Message):
    r"""Describes a sink used to export log entries to one of the following
    destinations:

    -  a Cloud Logging log bucket,
    -  a Cloud Storage bucket,
    -  a BigQuery dataset,
    -  a Pub/Sub topic,
    -  a Cloud project.

    A logs filter controls which log entries are exported. The sink must
    be created within a project, organization, billing account, or
    folder.


    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        name (str):
            Output only. The client-assigned sink identifier, unique
            within the project.

            For example: ``"my-syslog-errors-to-pubsub"``.

            Sink identifiers are limited to 100 characters and can
            include only the following characters:

            -  upper and lower-case alphanumeric characters,
            -  underscores,
            -  hyphens,
            -  periods.

            First character has to be alphanumeric.
        resource_name (str):
            Output only. The resource name of the sink.

            ::

                "projects/[PROJECT_ID]/sinks/[SINK_NAME]
                "organizations/[ORGANIZATION_ID]/sinks/[SINK_NAME]
                "billingAccounts/[BILLING_ACCOUNT_ID]/sinks/[SINK_NAME]
                "folders/[FOLDER_ID]/sinks/[SINK_NAME]

            For example: projects/my_project/sinks/SINK_NAME
        destination (str):
            Required. The export destination:

            ::

                "storage.googleapis.com/[GCS_BUCKET]"
                "bigquery.googleapis.com/projects/[PROJECT_ID]/datasets/[DATASET]"
                "pubsub.googleapis.com/projects/[PROJECT_ID]/topics/[TOPIC_ID]"
                "logging.googleapis.com/projects/[PROJECT_ID]"
                "logging.googleapis.com/projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"

            The sink's ``writer_identity``, set when the sink is
            created, must have permission to write to the destination or
            else the log entries are not exported. For more information,
            see `Exporting Logs with
            Sinks <https://cloud.google.com/logging/docs/api/tasks/exporting-logs>`__.
        filter (str):
            Optional. An `advanced logs
            filter <https://cloud.google.com/logging/docs/view/advanced-queries>`__.
            The only exported log entries are those that are in the
            resource owning the sink and that match the filter.

            For example:

            ``logName="projects/[PROJECT_ID]/logs/[LOG_ID]" AND severity>=ERROR``
        description (str):
            Optional. A description of this sink.

            The maximum length of the description is 8000
            characters.
        disabled (bool):
            Optional. If set to true, then this sink is
            disabled and it does not export any log entries.
        exclusions (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogExclusion]):
            Optional. Log entries that match any of these exclusion
            filters will not be exported.

            If a log entry is matched by both ``filter`` and one of
            ``exclusion_filters`` it will not be exported.
        output_version_format (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogSink.VersionFormat):
            Deprecated. This field is unused.
        writer_identity (str):
            Output only. An IAM identity-a service account or
            group-under which Cloud Logging writes the exported log
            entries to the sink's destination. This field is either set
            by specifying ``custom_writer_identity`` or set
            automatically by
            [sinks.create][google.logging.v2.ConfigServiceV2.CreateSink]
            and
            [sinks.update][google.logging.v2.ConfigServiceV2.UpdateSink]
            based on the value of ``unique_writer_identity`` in those
            methods.

            Until you grant this identity write-access to the
            destination, log entry exports from this sink will fail. For
            more information, see `Granting Access for a
            Resource <https://cloud.google.com/iam/docs/granting-roles-to-service-accounts#granting_access_to_a_service_account_for_a_resource>`__.
            Consult the destination service's documentation to determine
            the appropriate IAM roles to assign to the identity.

            Sinks that have a destination that is a log bucket in the
            same project as the sink cannot have a writer_identity and
            no additional permissions are required.
        include_children (bool):
            Optional. This field applies only to sinks owned by
            organizations and folders. If the field is false, the
            default, only the logs owned by the sink's parent resource
            are available for export. If the field is true, then log
            entries from all the projects, folders, and billing accounts
            contained in the sink's parent resource are also available
            for export. Whether a particular log entry from the children
            is exported depends on the sink's filter expression.

            For example, if this field is true, then the filter
            ``resource.type=gce_instance`` would export all Compute
            Engine VM instance log entries from all projects in the
            sink's parent.

            To only export entries from certain child projects, filter
            on the project part of the log name:

            logName:("projects/test-project1/" OR
            "projects/test-project2/") AND resource.type=gce_instance
        intercept_children (bool):
            Optional. This field applies only to sinks owned by
            organizations and folders.

            When the value of 'intercept_children' is true, the
            following restrictions apply:

            -  The sink must have the ``include_children`` flag set to
               true.
            -  The sink destination must be a Cloud project.

            Also, the following behaviors apply:

            -  Any logs matched by the sink won't be included by
               non-\ ``_Required`` sinks owned by child resources.
            -  The sink appears in the results of a ``ListSinks`` call
               from a child resource if the value of the ``filter``
               field in its request is either ``'in_scope("ALL")'`` or
               ``'in_scope("ANCESTOR")'``.
        bigquery_options (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.BigQueryOptions):
            Optional. Options that affect sinks exporting
            data to BigQuery.

            This field is a member of `oneof`_ ``options``.
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The creation timestamp of the
            sink.
            This field may not be present for older sinks.
        update_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The last update timestamp of the
            sink.
            This field may not be present for older sinks.
    """
    class VersionFormat(proto.Enum):
        r"""Deprecated. This is unused.

        Values:
            VERSION_FORMAT_UNSPECIFIED (0):
                An unspecified format version that will
                default to V2.
            V2 (1):
                ``LogEntry`` version 2 format.
            V1 (2):
                ``LogEntry`` version 1 format.
        """
        VERSION_FORMAT_UNSPECIFIED = 0
        V2 = 1
        V1 = 2

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    resource_name: str = proto.Field(
        proto.STRING,
        number=23,
    )
    destination: str = proto.Field(
        proto.STRING,
        number=3,
    )
    filter: str = proto.Field(
        proto.STRING,
        number=5,
    )
    description: str = proto.Field(
        proto.STRING,
        number=18,
    )
    disabled: bool = proto.Field(
        proto.BOOL,
        number=19,
    )
    exclusions: MutableSequence['LogExclusion'] = proto.RepeatedField(
        proto.MESSAGE,
        number=16,
        message='LogExclusion',
    )
    output_version_format: VersionFormat = proto.Field(
        proto.ENUM,
        number=6,
        enum=VersionFormat,
    )
    writer_identity: str = proto.Field(
        proto.STRING,
        number=8,
    )
    include_children: bool = proto.Field(
        proto.BOOL,
        number=9,
    )
    intercept_children: bool = proto.Field(
        proto.BOOL,
        number=24,
    )
    bigquery_options: 'BigQueryOptions' = proto.Field(
        proto.MESSAGE,
        number=12,
        oneof='options',
        message='BigQueryOptions',
    )
    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=13,
        message=timestamp_pb2.Timestamp,
    )
    update_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=14,
        message=timestamp_pb2.Timestamp,
    )


class BigQueryDataset(proto.Message):
    r"""Describes a BigQuery dataset that was created by a link.

    Attributes:
        dataset_id (str):
            Output only. The full resource name of the BigQuery dataset.
            The DATASET_ID will match the ID of the link, so the link
            must match the naming restrictions of BigQuery datasets
            (alphanumeric characters and underscores only).

            The dataset will have a resource path of
            "bigquery.googleapis.com/projects/[PROJECT_ID]/datasets/[DATASET_ID]".
    """

    dataset_id: str = proto.Field(
        proto.STRING,
        number=1,
    )


class Link(proto.Message):
    r"""Describes a link connected to an analytics enabled bucket.

    Attributes:
        name (str):
            Output only. The resource name of the link. The name can
            have up to 100 characters. A valid link id (at the end of
            the link name) must only have alphanumeric characters and
            underscores within it.

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"

            For example:

            \`projects/my-project/locations/global/buckets/my-bucket/links/my_link
        description (str):
            Optional. Describes this link.

            The maximum length of the description is 8000
            characters.
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The creation timestamp of the
            link.
        lifecycle_state (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LifecycleState):
            Output only. The resource lifecycle state.
        bigquery_dataset (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.BigQueryDataset):
            Optional. The information of a BigQuery
            Dataset. When a link is created, a BigQuery
            dataset is created along with it, in the same
            project as the LogBucket it's linked to. This
            dataset will also have BigQuery Views
            corresponding to the LogViews in the bucket.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    description: str = proto.Field(
        proto.STRING,
        number=2,
    )
    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=3,
        message=timestamp_pb2.Timestamp,
    )
    lifecycle_state: 'LifecycleState' = proto.Field(
        proto.ENUM,
        number=4,
        enum='LifecycleState',
    )
    bigquery_dataset: 'BigQueryDataset' = proto.Field(
        proto.MESSAGE,
        number=5,
        message='BigQueryDataset',
    )


class CmekSettings(proto.Message):
    r"""Describes the customer-managed encryption key (CMEK) settings
    associated with a project, folder, organization, billing account, or
    flexible resource.

    Note: CMEK for the Log Router can currently only be configured for
    Google Cloud organizations. Once configured, it applies to all
    projects and folders in the Google Cloud organization.

    See `Enabling CMEK for Log
    Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
    for more information.

    Attributes:
        name (str):
            Output only. The resource name of the CMEK
            settings.
        kms_key_name (str):
            Optional. The resource name for the configured Cloud KMS
            key.

            KMS key name format:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION]/keyRings/[KEYRING]/cryptoKeys/[KEY]"

            For example:

            ``"projects/my-project/locations/us-central1/keyRings/my-ring/cryptoKeys/my-key"``

            To enable CMEK for the Log Router, set this field to a valid
            ``kms_key_name`` for which the associated service account
            has the needed cloudkms.cryptoKeyEncrypterDecrypter roles
            assigned for the key.

            The Cloud KMS key used by the Log Router can be updated by
            changing the ``kms_key_name`` to a new valid key name or
            disabled by setting the key name to an empty string.
            Encryption operations that are in progress will be completed
            with the key that was in use when they started. Decryption
            operations will be completed using the key that was used at
            the time of encryption unless access to that key has been
            revoked.

            To disable CMEK for the Log Router, set this field to an
            empty string.

            See `Enabling CMEK for Log
            Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
            for more information.
        kms_key_version_name (str):
            Output only. The CryptoKeyVersion resource name for the
            configured Cloud KMS key.

            KMS key name format:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION]/keyRings/[KEYRING]/cryptoKeys/[KEY]/cryptoKeyVersions/[VERSION]"

            For example:

            ``"projects/my-project/locations/us-central1/keyRings/my-ring/cryptoKeys/my-key/cryptoKeyVersions/1"``

            This is a read-only field used to convey the specific
            configured CryptoKeyVersion of ``kms_key`` that has been
            configured. It will be populated in cases where the CMEK
            settings are bound to a single key version.

            If this field is populated, the ``kms_key`` is tied to a
            specific CryptoKeyVersion.
        service_account_id (str):
            Output only. The service account that will be used by the
            Log Router to access your Cloud KMS key.

            Before enabling CMEK for Log Router, you must first assign
            the cloudkms.cryptoKeyEncrypterDecrypter role to the service
            account that the Log Router will use to access your Cloud
            KMS key. Use
            [GetCmekSettings][google.logging.v2.ConfigServiceV2.GetCmekSettings]
            to obtain the service account ID.

            See `Enabling CMEK for Log
            Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
            for more information.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    kms_key_name: str = proto.Field(
        proto.STRING,
        number=2,
    )
    kms_key_version_name: str = proto.Field(
        proto.STRING,
        number=4,
    )
    service_account_id: str = proto.Field(
        proto.STRING,
        number=3,
    )


class Settings(proto.Message):
    r"""Describes the settings associated with a project, folder,
    organization, or billing account.

    Attributes:
        name (str):
            Output only. The resource name of the
            settings.
        kms_key_name (str):
            Optional. The resource name for the configured Cloud KMS
            key.

            KMS key name format:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION]/keyRings/[KEYRING]/cryptoKeys/[KEY]"

            For example:

            ``"projects/my-project/locations/us-central1/keyRings/my-ring/cryptoKeys/my-key"``

            To enable CMEK, set this field to a valid ``kms_key_name``
            for which the associated service account has the required
            ``roles/cloudkms.cryptoKeyEncrypterDecrypter`` role assigned
            for the key.

            The Cloud KMS key used by the Log Router can be updated by
            changing the ``kms_key_name`` to a new valid key name.

            To disable CMEK for the Log Router, set this field to an
            empty string.

            See `Enabling CMEK for Log
            Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
            for more information.
        kms_service_account_id (str):
            Output only. The service account that will be used by the
            Log Router to access your Cloud KMS key.

            Before enabling CMEK, you must first assign the role
            ``roles/cloudkms.cryptoKeyEncrypterDecrypter`` to the
            service account that will be used to access your Cloud KMS
            key. Use
            [GetSettings][google.logging.v2.ConfigServiceV2.GetSettings]
            to obtain the service account ID.

            See `Enabling CMEK for Log
            Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
            for more information.
        storage_location (str):
            Optional. The storage location for the ``_Default`` and
            ``_Required`` log buckets of newly created projects and
            folders, unless the storage location is explicitly provided.

            Example value: ``europe-west1``.

            Note: this setting does not affect the location of resources
            where a location is explicitly provided when created, such
            as custom log buckets.
        disable_default_sink (bool):
            Optional. If set to true, the ``_Default`` sink in newly
            created projects and folders will created in a disabled
            state. This can be used to automatically disable log storage
            if there is already an aggregated sink configured in the
            hierarchy. The ``_Default`` sink can be re-enabled manually
            if needed.
        default_sink_config (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.Settings.DefaultSinkConfig):
            Optional. Overrides the built-in configuration for
            ``_Default`` sink.
        logging_service_account_id (str):
            Output only. The service account for the given resource
            container, such as project or folder. Log sinks use this
            service account as their ``writer_identity`` if no custom
            service account is provided in the request when calling the
            create sink method.
    """

    class DefaultSinkConfig(proto.Message):
        r"""Describes the custom ``_Default`` sink configuration that is used to
        override the built-in ``_Default`` sink configuration in newly
        created resource containers, such as projects or folders.

        Attributes:
            filter (str):
                Optional. An `advanced logs
                filter <https://cloud.google.com/logging/docs/view/advanced-queries>`__.
                The only exported log entries are those that are in the
                resource owning the sink and that match the filter.

                For example:

                ``logName="projects/[PROJECT_ID]/logs/[LOG_ID]" AND severity>=ERROR``

                To match all logs, don't add exclusions and use the
                following line as the value of ``filter``:

                ``logName:*``

                Cannot be empty or unset when the value of ``mode`` is
                ``OVERWRITE``.
            exclusions (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogExclusion]):
                Optional. Specifies the set of exclusions to be added to the
                ``_Default`` sink in newly created resource containers.
            mode (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.Settings.DefaultSinkConfig.FilterWriteMode):
                Required. Determines the behavior to apply to the built-in
                ``_Default`` sink inclusion filter.

                Exclusions are always appended, as built-in ``_Default``
                sinks have no exclusions.
        """
        class FilterWriteMode(proto.Enum):
            r"""Behavior to apply to the built-in ``_Default`` sink inclusion
            filter.

            Values:
                FILTER_WRITE_MODE_UNSPECIFIED (0):
                    The filter's write mode is unspecified. This
                    mode must not be used.
                APPEND (1):
                    The contents of ``filter`` will be appended to the built-in
                    ``_Default`` sink filter. Using the append mode with an
                    empty filter will keep the sink inclusion filter unchanged.
                OVERWRITE (2):
                    The contents of ``filter`` will overwrite the built-in
                    ``_Default`` sink filter.
            """
            FILTER_WRITE_MODE_UNSPECIFIED = 0
            APPEND = 1
            OVERWRITE = 2

        filter: str = proto.Field(
            proto.STRING,
            number=1,
        )
        exclusions: MutableSequence['LogExclusion'] = proto.RepeatedField(
            proto.MESSAGE,
            number=2,
            message='LogExclusion',
        )
        mode: 'Settings.DefaultSinkConfig.FilterWriteMode' = proto.Field(
            proto.ENUM,
            number=3,
            enum='Settings.DefaultSinkConfig.FilterWriteMode',
        )

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    kms_key_name: str = proto.Field(
        proto.STRING,
        number=2,
    )
    kms_service_account_id: str = proto.Field(
        proto.STRING,
        number=3,
    )
    storage_location: str = proto.Field(
        proto.STRING,
        number=4,
    )
    disable_default_sink: bool = proto.Field(
        proto.BOOL,
        number=5,
    )
    default_sink_config: DefaultSinkConfig = proto.Field(
        proto.MESSAGE,
        number=6,
        message=DefaultSinkConfig,
    )
    logging_service_account_id: str = proto.Field(
        proto.STRING,
        number=7,
    )


class LoggingQuery(proto.Message):
    r"""Describes a Cloud Logging query that can be run in Logs
    Explorer UI or via the logging API.

    In addition to the query itself, additional information may be
    stored to capture the display configuration and other UI state
    used in association with analysis of query results.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        filter (str):
            Required. An `advanced query using the Logging Query
            Language <https://cloud.google.com/logging/docs/view/logging-query-language>`__.
            The maximum length of the filter is 20000 characters.
        summary_fields (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LoggingQuery.SummaryField]):
            Optional. The set of summary fields to
            display for this saved query.
        summary_field_start (int):
            Characters will be counted from the start of
            the string.

            This field is a member of `oneof`_ ``summary_field_width``.
        summary_field_end (int):
            Characters will be counted from the end of
            the string.

            This field is a member of `oneof`_ ``summary_field_width``.
    """

    class SummaryField(proto.Message):
        r"""A field from the LogEntry that is `added to the summary
        line <https://cloud.google.com/logging/docs/view/logs-explorer-interface#add-summary-fields>`__
        for a query in the Logs Explorer.

        Attributes:
            field (str):
                Optional. The field from the LogEntry to include in the
                summary line, for example ``resource.type`` or
                ``jsonPayload.name``.
        """

        field: str = proto.Field(
            proto.STRING,
            number=1,
        )

    filter: str = proto.Field(
        proto.STRING,
        number=1,
    )
    summary_fields: MutableSequence[SummaryField] = proto.RepeatedField(
        proto.MESSAGE,
        number=2,
        message=SummaryField,
    )
    summary_field_start: int = proto.Field(
        proto.INT32,
        number=3,
        oneof='summary_field_width',
    )
    summary_field_end: int = proto.Field(
        proto.INT32,
        number=4,
        oneof='summary_field_width',
    )


class OpsAnalyticsQuery(proto.Message):
    r"""Describes an analytics query that can be run in the Log
    Analytics page of Google Cloud console.

    Preview: This is a preview feature and may be subject to change
    before final release.

    Attributes:
        sql_query_text (str):
            Required. A logs analytics SQL query, which
            generally follows BigQuery format.

            This is the SQL query that appears in the Log
            Analytics UI's query editor.
    """

    sql_query_text: str = proto.Field(
        proto.STRING,
        number=2,
    )


class SavedQuery(proto.Message):
    r"""Describes a query that has been saved by a user.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        name (str):
            Output only. Resource name of the saved query.

            In the format:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/savedQueries/[QUERY_ID]"

            For a list of supported locations, see `Supported
            Regions <https://cloud.google.com/logging/docs/region-support#bucket-regions>`__

            After the saved query is created, the location cannot be
            changed.

            If the user doesn't provide a [QUERY_ID], the system will
            generate an alphanumeric ID.
        display_name (str):
            Required. The user specified title for the
            SavedQuery.
        description (str):
            Optional. A human readable description of the
            saved query.
        logging_query (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LoggingQuery):
            Logging query that can be executed in Logs
            Explorer or via Logging API.

            This field is a member of `oneof`_ ``query_oneof``.
        ops_analytics_query (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.OpsAnalyticsQuery):
            Analytics query that can be executed in Log
            Analytics.

            This field is a member of `oneof`_ ``query_oneof``.
        create_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The timestamp when the saved
            query was created.
        update_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The timestamp when the saved
            query was last updated.
        visibility (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.SavedQuery.Visibility):
            Required. The visibility status of this
            query, which determines its ownership.
    """
    class Visibility(proto.Enum):
        r"""Saved query visibility.

        Values:
            VISIBILITY_UNSPECIFIED (0):
                The saved query visibility is unspecified. A
                ``CreateSavedQuery`` request with an unspecified visibility
                will be rejected.
            PRIVATE (1):
                The saved query is only visible to the user
                that created it.
            SHARED (2):
                The saved query is visible to anyone in the
                project.
        """
        VISIBILITY_UNSPECIFIED = 0
        PRIVATE = 1
        SHARED = 2

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    display_name: str = proto.Field(
        proto.STRING,
        number=2,
    )
    description: str = proto.Field(
        proto.STRING,
        number=3,
    )
    logging_query: 'LoggingQuery' = proto.Field(
        proto.MESSAGE,
        number=4,
        oneof='query_oneof',
        message='LoggingQuery',
    )
    ops_analytics_query: 'OpsAnalyticsQuery' = proto.Field(
        proto.MESSAGE,
        number=10,
        oneof='query_oneof',
        message='OpsAnalyticsQuery',
    )
    create_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=5,
        message=timestamp_pb2.Timestamp,
    )
    update_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=6,
        message=timestamp_pb2.Timestamp,
    )
    visibility: Visibility = proto.Field(
        proto.ENUM,
        number=9,
        enum=Visibility,
    )


class RecentQuery(proto.Message):
    r"""Describes a recent query executed on the Logs Explorer or Log
    Analytics page within the last ~ 30 days.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        name (str):
            Output only. Resource name of the recent query.

            In the format:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/recentQueries/[QUERY_ID]"

            For a list of supported locations, see `Supported
            Regions <https://cloud.google.com/logging/docs/region-support>`__

            The [QUERY_ID] is a system generated alphanumeric ID.
        logging_query (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LoggingQuery):
            Logging query that can be executed in Logs
            Explorer or via Logging API.

            This field is a member of `oneof`_ ``query_oneof``.
        ops_analytics_query (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.OpsAnalyticsQuery):
            Analytics query that can be executed in Log
            Analytics.

            This field is a member of `oneof`_ ``query_oneof``.
        last_run_time (google.protobuf.timestamp_pb2.Timestamp):
            Output only. The timestamp when this query
            was last run.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    logging_query: 'LoggingQuery' = proto.Field(
        proto.MESSAGE,
        number=2,
        oneof='query_oneof',
        message='LoggingQuery',
    )
    ops_analytics_query: 'OpsAnalyticsQuery' = proto.Field(
        proto.MESSAGE,
        number=5,
        oneof='query_oneof',
        message='OpsAnalyticsQuery',
    )
    last_run_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=3,
        message=timestamp_pb2.Timestamp,
    )


class ListBucketsRequest(proto.Message):
    r"""The parameters to ``ListBuckets``.

    Attributes:
        parent (str):
            Required. The parent resource whose buckets are to be
            listed:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]"

            Note: The locations portion of the resource must be
            specified, but supplying the character ``-`` in place of
            [LOCATION_ID] will return all buckets.
        page_token (str):
            Optional. If present, then retrieve the next batch of
            results from the preceding call to this method.
            ``pageToken`` must be the value of ``nextPageToken`` from
            the previous response. The values of other method parameters
            should be identical to those in the previous call.
        page_size (int):
            Optional. The maximum number of results to return from this
            request. Non-positive values are ignored. The presence of
            ``nextPageToken`` in the response indicates that more
            results might be available.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=3,
    )


class ListBucketsResponse(proto.Message):
    r"""The response from ListBuckets.

    Attributes:
        buckets (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket]):
            A list of buckets.
        next_page_token (str):
            If there might be more results than appear in this response,
            then ``nextPageToken`` is included. To get the next set of
            results, call the same method again using the value of
            ``nextPageToken`` as ``pageToken``.
    """

    @property
    def raw_page(self):
        return self

    buckets: MutableSequence['LogBucket'] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message='LogBucket',
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class GetBucketRequest(proto.Message):
    r"""The parameters to ``GetBucket``.

    Attributes:
        name (str):
            Required. The resource name of the bucket:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"

            For example:

            ``"projects/my-project/locations/global/buckets/my-bucket"``
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class CreateBucketRequest(proto.Message):
    r"""The parameters to ``CreateBucket``.

    Attributes:
        parent (str):
            Required. The resource in which to create the log bucket:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]"

            For example:

            ``"projects/my-project/locations/global"``
        bucket_id (str):
            Required. A client-assigned identifier such as
            ``"my-bucket"``. Identifiers are limited to 100 characters
            and can include only letters, digits, underscores, hyphens,
            and periods. Bucket identifiers must start with an
            alphanumeric character.
        bucket (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket):
            Required. The new bucket. The region
            specified in the new bucket must be compliant
            with any Location Restriction Org Policy. The
            name field in the bucket is ignored.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    bucket_id: str = proto.Field(
        proto.STRING,
        number=2,
    )
    bucket: 'LogBucket' = proto.Field(
        proto.MESSAGE,
        number=3,
        message='LogBucket',
    )


class UpdateBucketRequest(proto.Message):
    r"""The parameters to ``UpdateBucket``.

    Attributes:
        name (str):
            Required. The full resource name of the bucket to update.

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"

            For example:

            ``"projects/my-project/locations/global/buckets/my-bucket"``
        bucket (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogBucket):
            Required. The updated bucket.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Required. Field mask that specifies the fields in ``bucket``
            that need an update. A bucket field will be overwritten if,
            and only if, it is in the update mask. ``name`` and output
            only fields cannot be updated.

            For a detailed ``FieldMask`` definition, see:
            https://developers.google.com/protocol-buffers/docs/reference/google.protobuf#google.protobuf.FieldMask

            For example: ``updateMask=retention_days``
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    bucket: 'LogBucket' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='LogBucket',
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=4,
        message=field_mask_pb2.FieldMask,
    )


class DeleteBucketRequest(proto.Message):
    r"""The parameters to ``DeleteBucket``.

    Attributes:
        name (str):
            Required. The full resource name of the bucket to delete.

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"

            For example:

            ``"projects/my-project/locations/global/buckets/my-bucket"``
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class UndeleteBucketRequest(proto.Message):
    r"""The parameters to ``UndeleteBucket``.

    Attributes:
        name (str):
            Required. The full resource name of the bucket to undelete.

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"

            For example:

            ``"projects/my-project/locations/global/buckets/my-bucket"``
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ListViewsRequest(proto.Message):
    r"""The parameters to ``ListViews``.

    Attributes:
        parent (str):
            Required. The bucket whose views are to be listed:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]".
        page_token (str):
            Optional. If present, then retrieve the next batch of
            results from the preceding call to this method.
            ``pageToken`` must be the value of ``nextPageToken`` from
            the previous response. The values of other method parameters
            should be identical to those in the previous call.
        page_size (int):
            Optional. The maximum number of results to return from this
            request.

            Non-positive values are ignored. The presence of
            ``nextPageToken`` in the response indicates that more
            results might be available.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=3,
    )


class ListViewsResponse(proto.Message):
    r"""The response from ListViews.

    Attributes:
        views (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogView]):
            A list of views.
        next_page_token (str):
            If there might be more results than appear in this response,
            then ``nextPageToken`` is included. To get the next set of
            results, call the same method again using the value of
            ``nextPageToken`` as ``pageToken``.
    """

    @property
    def raw_page(self):
        return self

    views: MutableSequence['LogView'] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message='LogView',
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class GetViewRequest(proto.Message):
    r"""The parameters to ``GetView``.

    Attributes:
        name (str):
            Required. The resource name of the policy:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]"

            For example:

            ``"projects/my-project/locations/global/buckets/my-bucket/views/my-view"``
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class CreateViewRequest(proto.Message):
    r"""The parameters to ``CreateView``.

    Attributes:
        parent (str):
            Required. The bucket in which to create the view

            ::

                `"projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"`

            For example:

            ``"projects/my-project/locations/global/buckets/my-bucket"``
        view_id (str):
            Required. A client-assigned identifier such as
            ``"my-view"``. Identifiers are limited to 100 characters and
            can include only letters, digits, underscores, hyphens, and
            periods.
        view (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogView):
            Required. The new view.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    view_id: str = proto.Field(
        proto.STRING,
        number=2,
    )
    view: 'LogView' = proto.Field(
        proto.MESSAGE,
        number=3,
        message='LogView',
    )


class UpdateViewRequest(proto.Message):
    r"""The parameters to ``UpdateView``.

    Attributes:
        name (str):
            Required. The full resource name of the view to update

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]"

            For example:

            ``"projects/my-project/locations/global/buckets/my-bucket/views/my-view"``
        view (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogView):
            Required. The updated view.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Optional. Field mask that specifies the fields in ``view``
            that need an update. A field will be overwritten if, and
            only if, it is in the update mask. ``name`` and output only
            fields cannot be updated.

            For a detailed ``FieldMask`` definition, see
            https://developers.google.com/protocol-buffers/docs/reference/google.protobuf#google.protobuf.FieldMask

            For example: ``updateMask=filter``
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    view: 'LogView' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='LogView',
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=4,
        message=field_mask_pb2.FieldMask,
    )


class DeleteViewRequest(proto.Message):
    r"""The parameters to ``DeleteView``.

    Attributes:
        name (str):
            Required. The full resource name of the view to delete:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/views/[VIEW_ID]"

            For example:

            ::

               `"projects/my-project/locations/global/buckets/my-bucket/views/my-view"`
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ListExclusionsRequest(proto.Message):
    r"""The parameters to ``ListExclusions``.

    Attributes:
        parent (str):
            Required. The parent resource whose exclusions are to be
            listed.

            ::

                "projects/[PROJECT_ID]"
                "organizations/[ORGANIZATION_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]"
                "folders/[FOLDER_ID]".
        page_token (str):
            Optional. If present, then retrieve the next batch of
            results from the preceding call to this method.
            ``pageToken`` must be the value of ``nextPageToken`` from
            the previous response. The values of other method parameters
            should be identical to those in the previous call.
        page_size (int):
            Optional. The maximum number of results to return from this
            request. Non-positive values are ignored. The presence of
            ``nextPageToken`` in the response indicates that more
            results might be available.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=3,
    )


class ListExclusionsResponse(proto.Message):
    r"""Result returned from ``ListExclusions``.

    Attributes:
        exclusions (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogExclusion]):
            A list of exclusions.
        next_page_token (str):
            If there might be more results than appear in this response,
            then ``nextPageToken`` is included. To get the next set of
            results, call the same method again using the value of
            ``nextPageToken`` as ``pageToken``.
    """

    @property
    def raw_page(self):
        return self

    exclusions: MutableSequence['LogExclusion'] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message='LogExclusion',
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class GetExclusionRequest(proto.Message):
    r"""The parameters to ``GetExclusion``.

    Attributes:
        name (str):
            Required. The resource name of an existing exclusion:

            ::

                "projects/[PROJECT_ID]/exclusions/[EXCLUSION_ID]"
                "organizations/[ORGANIZATION_ID]/exclusions/[EXCLUSION_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/exclusions/[EXCLUSION_ID]"
                "folders/[FOLDER_ID]/exclusions/[EXCLUSION_ID]"

            For example:

            ``"projects/my-project/exclusions/my-exclusion"``
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class CreateExclusionRequest(proto.Message):
    r"""The parameters to ``CreateExclusion``.

    Attributes:
        parent (str):
            Required. The parent resource in which to create the
            exclusion:

            ::

                "projects/[PROJECT_ID]"
                "organizations/[ORGANIZATION_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]"
                "folders/[FOLDER_ID]"

            For examples:

            ``"projects/my-logging-project"``
            ``"organizations/123456789"``
        exclusion (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogExclusion):
            Required. The new exclusion, whose ``name`` parameter is an
            exclusion name that is not already used in the parent
            resource.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    exclusion: 'LogExclusion' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='LogExclusion',
    )


class UpdateExclusionRequest(proto.Message):
    r"""The parameters to ``UpdateExclusion``.

    Attributes:
        name (str):
            Required. The resource name of the exclusion to update:

            ::

                "projects/[PROJECT_ID]/exclusions/[EXCLUSION_ID]"
                "organizations/[ORGANIZATION_ID]/exclusions/[EXCLUSION_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/exclusions/[EXCLUSION_ID]"
                "folders/[FOLDER_ID]/exclusions/[EXCLUSION_ID]"

            For example:

            ``"projects/my-project/exclusions/my-exclusion"``
        exclusion (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogExclusion):
            Required. New values for the existing exclusion. Only the
            fields specified in ``update_mask`` are relevant.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Required. A non-empty list of fields to change in the
            existing exclusion. New values for the fields are taken from
            the corresponding fields in the
            [LogExclusion][google.logging.v2.LogExclusion] included in
            this request. Fields not mentioned in ``update_mask`` are
            not changed and are ignored in the request.

            For example, to change the filter and description of an
            exclusion, specify an ``update_mask`` of
            ``"filter,description"``.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    exclusion: 'LogExclusion' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='LogExclusion',
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=3,
        message=field_mask_pb2.FieldMask,
    )


class DeleteExclusionRequest(proto.Message):
    r"""The parameters to ``DeleteExclusion``.

    Attributes:
        name (str):
            Required. The resource name of an existing exclusion to
            delete:

            ::

                "projects/[PROJECT_ID]/exclusions/[EXCLUSION_ID]"
                "organizations/[ORGANIZATION_ID]/exclusions/[EXCLUSION_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/exclusions/[EXCLUSION_ID]"
                "folders/[FOLDER_ID]/exclusions/[EXCLUSION_ID]"

            For example:

            ``"projects/my-project/exclusions/my-exclusion"``
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ListSinksRequest(proto.Message):
    r"""The parameters to ``ListSinks``.

    Attributes:
        parent (str):
            Required. The parent resource whose sinks are to be listed:

            ::

                "projects/[PROJECT_ID]"
                "organizations/[ORGANIZATION_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]"
                "folders/[FOLDER_ID]".
        page_token (str):
            Optional. If present, then retrieve the next batch of
            results from the preceding call to this method.
            ``pageToken`` must be the value of ``nextPageToken`` from
            the previous response. The values of other method parameters
            should be identical to those in the previous call.
        page_size (int):
            Optional. The maximum number of results to return from this
            request. Non-positive values are ignored. The presence of
            ``nextPageToken`` in the response indicates that more
            results might be available.
        filter (str):
            Optional. A filter expression to constrain the sinks
            returned. Today, this only supports the following strings:

            -  ``''``
            -  ``'in_scope("ALL")'``,
            -  ``'in_scope("ANCESTOR")'``,
            -  ``'in_scope("DEFAULT")'``.

            Description of scopes below. ALL: Includes all of the sinks
            which can be returned in any other scope. ANCESTOR: Includes
            intercepting sinks owned by ancestor resources. DEFAULT:
            Includes sinks owned by ``parent``.

            When the empty string is provided, then the filter
            'in_scope("DEFAULT")' is applied.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=3,
    )
    filter: str = proto.Field(
        proto.STRING,
        number=5,
    )


class ListSinksResponse(proto.Message):
    r"""Result returned from ``ListSinks``.

    Attributes:
        sinks (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogSink]):
            A list of sinks.
        next_page_token (str):
            If there might be more results than appear in this response,
            then ``nextPageToken`` is included. To get the next set of
            results, call the same method again using the value of
            ``nextPageToken`` as ``pageToken``.
    """

    @property
    def raw_page(self):
        return self

    sinks: MutableSequence['LogSink'] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message='LogSink',
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class GetSinkRequest(proto.Message):
    r"""The parameters to ``GetSink``.

    Attributes:
        sink_name (str):
            Required. The resource name of the sink:

            ::

                "projects/[PROJECT_ID]/sinks/[SINK_ID]"
                "organizations/[ORGANIZATION_ID]/sinks/[SINK_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/sinks/[SINK_ID]"
                "folders/[FOLDER_ID]/sinks/[SINK_ID]"

            For example:

            ``"projects/my-project/sinks/my-sink"``
    """

    sink_name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class CreateSinkRequest(proto.Message):
    r"""The parameters to ``CreateSink``.

    Attributes:
        parent (str):
            Required. The resource in which to create the sink:

            ::

                "projects/[PROJECT_ID]"
                "organizations/[ORGANIZATION_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]"
                "folders/[FOLDER_ID]"

            For examples:

            ``"projects/my-project"`` ``"organizations/123456789"``
        sink (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogSink):
            Required. The new sink, whose ``name`` parameter is a sink
            identifier that is not already in use.
        unique_writer_identity (bool):
            Optional. Determines the kind of IAM identity returned as
            ``writer_identity`` in the new sink. If this value is
            omitted or set to false, and if the sink's parent is a
            project, then the value returned as ``writer_identity`` is
            the same group or service account used by Cloud Logging
            before the addition of writer identities to this API. The
            sink's destination must be in the same project as the sink
            itself.

            If this field is set to true, or if the sink is owned by a
            non-project resource such as an organization, then the value
            of ``writer_identity`` will be a `service
            agent <https://cloud.google.com/iam/docs/service-account-types#service-agents>`__
            used by the sinks with the same parent. For more
            information, see ``writer_identity`` in
            [LogSink][google.logging.v2.LogSink].
        custom_writer_identity (str):
            Optional. A service account provided by the caller that will
            be used to write the log entries. The format must be
            ``serviceAccount:some@email``. This field can only be
            specified if you are routing logs to a destination outside
            this sink's project. If not specified, a Logging service
            account will automatically be generated.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    sink: 'LogSink' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='LogSink',
    )
    unique_writer_identity: bool = proto.Field(
        proto.BOOL,
        number=3,
    )
    custom_writer_identity: str = proto.Field(
        proto.STRING,
        number=4,
    )


class UpdateSinkRequest(proto.Message):
    r"""The parameters to ``UpdateSink``.

    Attributes:
        sink_name (str):
            Required. The full resource name of the sink to update,
            including the parent resource and the sink identifier:

            ::

                "projects/[PROJECT_ID]/sinks/[SINK_ID]"
                "organizations/[ORGANIZATION_ID]/sinks/[SINK_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/sinks/[SINK_ID]"
                "folders/[FOLDER_ID]/sinks/[SINK_ID]"

            For example:

            ``"projects/my-project/sinks/my-sink"``
        sink (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.LogSink):
            Required. The updated sink, whose name is the same
            identifier that appears as part of ``sink_name``.
        unique_writer_identity (bool):
            Optional. See
            [sinks.create][google.logging.v2.ConfigServiceV2.CreateSink]
            for a description of this field. When updating a sink, the
            effect of this field on the value of ``writer_identity`` in
            the updated sink depends on both the old and new values of
            this field:

            -  If the old and new values of this field are both false or
               both true, then there is no change to the sink's
               ``writer_identity``.
            -  If the old value is false and the new value is true, then
               ``writer_identity`` is changed to a `service
               agent <https://cloud.google.com/iam/docs/service-account-types#service-agents>`__
               owned by Cloud Logging.
            -  It is an error if the old value is true and the new value
               is set to false or defaulted to false.
        custom_writer_identity (str):
            Optional. A service account provided by the caller that will
            be used to write the log entries. The format must be
            ``serviceAccount:some@email``. This field can only be
            specified if you are routing logs to a destination outside
            this sink's project. If not specified, a Logging service
            account will automatically be generated.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Optional. Field mask that specifies the fields in ``sink``
            that need an update. A sink field will be overwritten if,
            and only if, it is in the update mask. ``name`` and output
            only fields cannot be updated.

            An empty ``updateMask`` is temporarily treated as using the
            following mask for backwards compatibility purposes:

            ``destination,filter,includeChildren``

            At some point in the future, behavior will be removed and
            specifying an empty ``updateMask`` will be an error.

            For a detailed ``FieldMask`` definition, see
            https://developers.google.com/protocol-buffers/docs/reference/google.protobuf#google.protobuf.FieldMask

            For example: ``updateMask=filter``
    """

    sink_name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    sink: 'LogSink' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='LogSink',
    )
    unique_writer_identity: bool = proto.Field(
        proto.BOOL,
        number=3,
    )
    custom_writer_identity: str = proto.Field(
        proto.STRING,
        number=5,
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=4,
        message=field_mask_pb2.FieldMask,
    )


class DeleteSinkRequest(proto.Message):
    r"""The parameters to ``DeleteSink``.

    Attributes:
        sink_name (str):
            Required. The full resource name of the sink to delete,
            including the parent resource and the sink identifier:

            ::

                "projects/[PROJECT_ID]/sinks/[SINK_ID]"
                "organizations/[ORGANIZATION_ID]/sinks/[SINK_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/sinks/[SINK_ID]"
                "folders/[FOLDER_ID]/sinks/[SINK_ID]"

            For example:

            ``"projects/my-project/sinks/my-sink"``
    """

    sink_name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ListLinksRequest(proto.Message):
    r"""The parameters to ListLinks.

    Attributes:
        parent (str):
            Required. The parent resource whose links are to be listed:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]".
        page_token (str):
            Optional. If present, then retrieve the next batch of
            results from the preceding call to this method.
            ``pageToken`` must be the value of ``nextPageToken`` from
            the previous response.
        page_size (int):
            Optional. The maximum number of results to
            return from this request.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=3,
    )


class ListLinksResponse(proto.Message):
    r"""The response from ListLinks.

    Attributes:
        links (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.Link]):
            A list of links.
        next_page_token (str):
            If there might be more results than those appearing in this
            response, then ``nextPageToken`` is included. To get the
            next set of results, call the same method again using the
            value of ``nextPageToken`` as ``pageToken``.
    """

    @property
    def raw_page(self):
        return self

    links: MutableSequence['Link'] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message='Link',
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )


class GetLinkRequest(proto.Message):
    r"""The parameters to GetLink.

    Attributes:
        name (str):
            Required. The resource name of the link:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]".
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class CreateLinkRequest(proto.Message):
    r"""The parameters to CreateLink.

    Attributes:
        parent (str):
            Required. The full resource name of the bucket to create a
            link for.

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]".
        link (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.Link):
            Required. The new link.
        link_id (str):
            Required. The ID to use for the link. The link_id can have
            up to 100 characters. A valid link_id must only have
            alphanumeric characters and underscores within it.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    link: 'Link' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='Link',
    )
    link_id: str = proto.Field(
        proto.STRING,
        number=3,
    )


class DeleteLinkRequest(proto.Message):
    r"""The parameters to DeleteLink.

    Attributes:
        name (str):
            Required. The full resource name of the link to delete.

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]/buckets/[BUCKET_ID]/links/[LINK_ID]".
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class GetCmekSettingsRequest(proto.Message):
    r"""The parameters to
    [GetCmekSettings][google.logging.v2.ConfigServiceV2.GetCmekSettings].

    See `Enabling CMEK for Log
    Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
    for more information.

    Attributes:
        name (str):
            Required. The resource for which to retrieve CMEK settings.

            ::

                "projects/[PROJECT_ID]/cmekSettings"
                "organizations/[ORGANIZATION_ID]/cmekSettings"
                "billingAccounts/[BILLING_ACCOUNT_ID]/cmekSettings"
                "folders/[FOLDER_ID]/cmekSettings"

            For example:

            ``"organizations/12345/cmekSettings"``

            Note: CMEK for the Log Router can be configured for Google
            Cloud projects, folders, organizations, and billing
            accounts. Once configured for an organization, it applies to
            all projects and folders in the Google Cloud organization.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class UpdateCmekSettingsRequest(proto.Message):
    r"""The parameters to
    [UpdateCmekSettings][google.logging.v2.ConfigServiceV2.UpdateCmekSettings].

    See `Enabling CMEK for Log
    Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
    for more information.

    Attributes:
        name (str):
            Required. The resource name for the CMEK settings to update.

            ::

                "projects/[PROJECT_ID]/cmekSettings"
                "organizations/[ORGANIZATION_ID]/cmekSettings"
                "billingAccounts/[BILLING_ACCOUNT_ID]/cmekSettings"
                "folders/[FOLDER_ID]/cmekSettings"

            For example:

            ``"organizations/12345/cmekSettings"``

            Note: CMEK for the Log Router can currently only be
            configured for Google Cloud organizations. Once configured,
            it applies to all projects and folders in the Google Cloud
            organization.
        cmek_settings (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CmekSettings):
            Required. The CMEK settings to update.

            See `Enabling CMEK for Log
            Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
            for more information.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Optional. Field mask identifying which fields from
            ``cmek_settings`` should be updated. A field will be
            overwritten if and only if it is in the update mask. Output
            only fields cannot be updated.

            See [FieldMask][google.protobuf.FieldMask] for more
            information.

            For example: ``"updateMask=kmsKeyName"``
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    cmek_settings: 'CmekSettings' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='CmekSettings',
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=3,
        message=field_mask_pb2.FieldMask,
    )


class GetSettingsRequest(proto.Message):
    r"""The parameters to
    [GetSettings][google.logging.v2.ConfigServiceV2.GetSettings].

    See [View default resource settings for Logging]
    (https://cloud.google.com/logging/docs/default-settings#view-org-settings)
    for more information.

    Attributes:
        name (str):
            Required. The resource for which to retrieve settings.

            ::

                "projects/[PROJECT_ID]/settings"
                "organizations/[ORGANIZATION_ID]/settings"
                "billingAccounts/[BILLING_ACCOUNT_ID]/settings"
                "folders/[FOLDER_ID]/settings"

            For example:

            ``"organizations/12345/settings"``

            Note: Settings can be retrieved for Google Cloud projects,
            folders, organizations, and billing accounts.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class UpdateSettingsRequest(proto.Message):
    r"""The parameters to
    [UpdateSettings][google.logging.v2.ConfigServiceV2.UpdateSettings].

    See [Configure default settings for organizations and folders]
    (https://cloud.google.com/logging/docs/default-settings) for more
    information.

    Attributes:
        name (str):
            Required. The resource name for the settings to update.

            ::

                "organizations/[ORGANIZATION_ID]/settings"

            For example:

            ``"organizations/12345/settings"``
        settings (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.Settings):
            Required. The settings to update.

            See `Enabling CMEK for Log
            Router <https://cloud.google.com/logging/docs/routing/managed-encryption>`__
            for more information.
        update_mask (google.protobuf.field_mask_pb2.FieldMask):
            Optional. Field mask identifying which fields from
            ``settings`` should be updated. A field will be overwritten
            if and only if it is in the update mask. Output only fields
            cannot be updated.

            See [FieldMask][google.protobuf.FieldMask] for more
            information.

            For example: ``"updateMask=kmsKeyName"``
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    settings: 'Settings' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='Settings',
    )
    update_mask: field_mask_pb2.FieldMask = proto.Field(
        proto.MESSAGE,
        number=3,
        message=field_mask_pb2.FieldMask,
    )


class ListSavedQueriesRequest(proto.Message):
    r"""The parameters to 'ListSavedQueries'.

    Attributes:
        parent (str):
            Required. The resource to which the listed queries belong.

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]"

            For example:

            ::

                "projects/my-project/locations/us-central1"

            Note: The locations portion of the resource must be
            specified. To get a list of all saved queries, a wildcard
            character ``-`` can be used for [LOCATION_ID], for example:

            ::

                "projects/my-project/locations/-".
        page_token (str):
            Optional. If present, then retrieve the next batch of
            results from the preceding call to this method.
            ``pageToken`` must be the value of ``nextPageToken`` from
            the previous response. The values of other method parameters
            should be identical to those in the previous call.
        page_size (int):
            Optional. The maximum number of results to return from this
            request.

            Non-positive values are ignored. The presence of
            ``nextPageToken`` in the response indicates that more
            results might be available.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=3,
    )


class ListSavedQueriesResponse(proto.Message):
    r"""The response from ListSavedQueries.

    Attributes:
        saved_queries (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.SavedQuery]):
            A list of saved queries.
        next_page_token (str):
            If there might be more results than appear in this response,
            then ``nextPageToken`` is included. To get the next set of
            results, call the same method again using the value of
            ``nextPageToken`` as ``pageToken``.
        unreachable (MutableSequence[str]):
            The unreachable resources. It can be either 1) a saved query
            if a specific query is unreachable or 2) a location if a
            specific location is unreachabe.

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/savedQueries/[QUERY_ID]"
                "projects/[PROJECT_ID]/locations/[LOCATION_ID]"

            For example:

            ::

                "projects/my-project/locations/global/savedQueries/12345678"
                "projects/my-project/locations/global"

            If there are unreachable resources, the response will first
            return pages that contain saved queries, and then return
            pages that contain the unreachable resources.
    """

    @property
    def raw_page(self):
        return self

    saved_queries: MutableSequence['SavedQuery'] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message='SavedQuery',
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )
    unreachable: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=3,
    )


class CreateSavedQueryRequest(proto.Message):
    r"""The parameters to 'CreateSavedQuery'.

    Attributes:
        parent (str):
            Required. The parent resource in which to create the saved
            query:

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]"

            For example:

            ::

                "projects/my-project/locations/global"
                "organizations/123456789/locations/us-central1".
        saved_query_id (str):
            Optional. The ID to use for the saved query, which will
            become the final component of the saved query's resource
            name.

            If the ``saved_query_id`` is not provided, the system will
            generate an alphanumeric ID.

            The ``saved_query_id`` is limited to 100 characters and can
            include only the following characters:

            -  upper and lower-case alphanumeric characters,
            -  underscores,
            -  hyphens,
            -  periods.

            First character has to be alphanumeric.
        saved_query (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.SavedQuery):
            Required. The new saved query.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    saved_query_id: str = proto.Field(
        proto.STRING,
        number=3,
    )
    saved_query: 'SavedQuery' = proto.Field(
        proto.MESSAGE,
        number=2,
        message='SavedQuery',
    )


class DeleteSavedQueryRequest(proto.Message):
    r"""The parameters to 'DeleteSavedQuery'.

    Attributes:
        name (str):
            Required. The full resource name of the saved query to
            delete.

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/savedQueries/[QUERY_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]/savedQueries/[QUERY_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]/savedQueries/[QUERY_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]/savedQueries/[QUERY_ID]"

            For example:

            ::

                "projects/my-project/locations/global/savedQueries/my-saved-query".
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )


class ListRecentQueriesRequest(proto.Message):
    r"""The parameters to 'ListRecentQueries'.

    Attributes:
        parent (str):
            Required. The resource to which the listed queries belong.

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]"
                "organizations/[ORGANIZATION_ID]/locations/[LOCATION_ID]"
                "billingAccounts/[BILLING_ACCOUNT_ID]/locations/[LOCATION_ID]"
                "folders/[FOLDER_ID]/locations/[LOCATION_ID]"

            For example:

            ``projects/my-project/locations/us-central1``

            Note: The location portion of the resource must be
            specified, but supplying the character ``-`` in place of
            [LOCATION_ID] will return all recent queries.
        page_token (str):
            Optional. If present, then retrieve the next batch of
            results from the preceding call to this method.
            ``pageToken`` must be the value of ``nextPageToken`` from
            the previous response. The values of other method parameters
            should be identical to those in the previous call.
        page_size (int):
            Optional. The maximum number of results to return from this
            request. Non-positive values are ignored. The presence of
            ``nextPageToken`` in the response indicates that more
            results might be available.
    """

    parent: str = proto.Field(
        proto.STRING,
        number=1,
    )
    page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )
    page_size: int = proto.Field(
        proto.INT32,
        number=3,
    )


class ListRecentQueriesResponse(proto.Message):
    r"""The response from ListRecentQueries.

    Attributes:
        recent_queries (MutableSequence[googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.RecentQuery]):
            A list of recent queries.
        next_page_token (str):
            If there might be more results than appear in this response,
            then ``nextPageToken`` is included. To get the next set of
            results, call the same method again using the value of
            ``nextPageToken`` as ``pageToken``.
        unreachable (MutableSequence[str]):
            The unreachable resources. Each resource can be either 1) a
            saved query if a specific query is unreachable or 2) a
            location if a specific location is unreachable.

            ::

                "projects/[PROJECT_ID]/locations/[LOCATION_ID]/recentQueries/[QUERY_ID]"
                "projects/[PROJECT_ID]/locations/[LOCATION_ID]"

            For example:

            ``"projects/my-project/locations/global/recentQueries/12345678"``
            ``"projects/my-project/locations/global"``

            If there are unreachable resources, the response will first
            return pages that contain recent queries, and then return
            pages that contain the unreachable resources.
    """

    @property
    def raw_page(self):
        return self

    recent_queries: MutableSequence['RecentQuery'] = proto.RepeatedField(
        proto.MESSAGE,
        number=1,
        message='RecentQuery',
    )
    next_page_token: str = proto.Field(
        proto.STRING,
        number=2,
    )
    unreachable: MutableSequence[str] = proto.RepeatedField(
        proto.STRING,
        number=3,
    )


class CopyLogEntriesRequest(proto.Message):
    r"""The parameters to CopyLogEntries.

    Attributes:
        name (str):
            Required. Log bucket from which to copy log entries.

            For example:

            ``"projects/my-project/locations/global/buckets/my-source-bucket"``
        filter (str):
            Optional. A filter specifying which log
            entries to copy. The filter must be no more than
            20k characters. An empty filter matches all log
            entries.
        destination (str):
            Required. Destination to which to copy log
            entries.
    """

    name: str = proto.Field(
        proto.STRING,
        number=1,
    )
    filter: str = proto.Field(
        proto.STRING,
        number=3,
    )
    destination: str = proto.Field(
        proto.STRING,
        number=4,
    )


class CopyLogEntriesResponse(proto.Message):
    r"""Response type for CopyLogEntries long running operations.

    Attributes:
        log_entries_copied_count (int):
            Number of log entries copied.
    """

    log_entries_copied_count: int = proto.Field(
        proto.INT64,
        number=1,
    )


class CopyLogEntriesMetadata(proto.Message):
    r"""Metadata for CopyLogEntries long running operations.

    Attributes:
        start_time (google.protobuf.timestamp_pb2.Timestamp):
            The create time of an operation.
        end_time (google.protobuf.timestamp_pb2.Timestamp):
            The end time of an operation.
        state (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.OperationState):
            Output only. State of an operation.
        cancellation_requested (bool):
            Identifies whether the user has requested
            cancellation of the operation.
        request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CopyLogEntriesRequest):
            CopyLogEntries RPC request. This field is
            deprecated and not used.
        progress (int):
            Estimated progress of the operation (0 -
            100%).
        writer_identity (str):
            The IAM identity of a service account that must be granted
            access to the destination.

            If the service account is not granted permission to the
            destination within an hour, the operation will be cancelled.

            For example: ``"serviceAccount:foo@bar.com"``
        source (str):
            Source from which to copy log entries.

            For example, a log bucket:

            ``"projects/my-project/locations/global/buckets/my-source-bucket"``
        destination (str):
            Destination to which to copy log entries.

            For example, a Cloud Storage bucket:

            ``"storage.googleapis.com/my-cloud-storage-bucket"``
        verb (str):
            Name of the verb executed by the operation.

            For example,

            ``"copy"``
    """

    start_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=1,
        message=timestamp_pb2.Timestamp,
    )
    end_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=2,
        message=timestamp_pb2.Timestamp,
    )
    state: 'OperationState' = proto.Field(
        proto.ENUM,
        number=3,
        enum='OperationState',
    )
    cancellation_requested: bool = proto.Field(
        proto.BOOL,
        number=4,
    )
    request: 'CopyLogEntriesRequest' = proto.Field(
        proto.MESSAGE,
        number=5,
        message='CopyLogEntriesRequest',
    )
    progress: int = proto.Field(
        proto.INT32,
        number=6,
    )
    writer_identity: str = proto.Field(
        proto.STRING,
        number=7,
    )
    source: str = proto.Field(
        proto.STRING,
        number=8,
    )
    destination: str = proto.Field(
        proto.STRING,
        number=9,
    )
    verb: str = proto.Field(
        proto.STRING,
        number=10,
    )


class LocationMetadata(proto.Message):
    r"""Cloud Logging specific location metadata.

    Attributes:
        log_analytics_enabled (bool):
            Indicates whether or not Log Analytics
            features are supported in the given location.
    """

    log_analytics_enabled: bool = proto.Field(
        proto.BOOL,
        number=1,
    )


class BucketMetadata(proto.Message):
    r"""Metadata for LongRunningUpdateBucket Operations.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        start_time (google.protobuf.timestamp_pb2.Timestamp):
            The create time of an operation.
        end_time (google.protobuf.timestamp_pb2.Timestamp):
            The end time of an operation.
        state (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.OperationState):
            Output only. State of an operation.
        create_bucket_request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateBucketRequest):
            LongRunningCreateBucket RPC request.

            This field is a member of `oneof`_ ``request``.
        update_bucket_request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.UpdateBucketRequest):
            LongRunningUpdateBucket RPC request.

            This field is a member of `oneof`_ ``request``.
    """

    start_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=1,
        message=timestamp_pb2.Timestamp,
    )
    end_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=2,
        message=timestamp_pb2.Timestamp,
    )
    state: 'OperationState' = proto.Field(
        proto.ENUM,
        number=3,
        enum='OperationState',
    )
    create_bucket_request: 'CreateBucketRequest' = proto.Field(
        proto.MESSAGE,
        number=4,
        oneof='request',
        message='CreateBucketRequest',
    )
    update_bucket_request: 'UpdateBucketRequest' = proto.Field(
        proto.MESSAGE,
        number=5,
        oneof='request',
        message='UpdateBucketRequest',
    )


class LinkMetadata(proto.Message):
    r"""Metadata for long running Link operations.

    This message has `oneof`_ fields (mutually exclusive fields).
    For each oneof, at most one member field can be set at the same time.
    Setting any member of the oneof automatically clears all other
    members.

    .. _oneof: https://proto-plus-python.readthedocs.io/en/stable/fields.html#oneofs-mutually-exclusive-fields

    Attributes:
        start_time (google.protobuf.timestamp_pb2.Timestamp):
            The start time of an operation.
        end_time (google.protobuf.timestamp_pb2.Timestamp):
            The end time of an operation.
        state (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.OperationState):
            Output only. State of an operation.
        create_link_request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.CreateLinkRequest):
            CreateLink RPC request.

            This field is a member of `oneof`_ ``request``.
        delete_link_request (googlecloudsdk.generated_clients.gapic_clients.logging_v2.types.DeleteLinkRequest):
            DeleteLink RPC request.

            This field is a member of `oneof`_ ``request``.
    """

    start_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=1,
        message=timestamp_pb2.Timestamp,
    )
    end_time: timestamp_pb2.Timestamp = proto.Field(
        proto.MESSAGE,
        number=2,
        message=timestamp_pb2.Timestamp,
    )
    state: 'OperationState' = proto.Field(
        proto.ENUM,
        number=3,
        enum='OperationState',
    )
    create_link_request: 'CreateLinkRequest' = proto.Field(
        proto.MESSAGE,
        number=4,
        oneof='request',
        message='CreateLinkRequest',
    )
    delete_link_request: 'DeleteLinkRequest' = proto.Field(
        proto.MESSAGE,
        number=5,
        oneof='request',
        message='DeleteLinkRequest',
    )


__all__ = tuple(sorted(__protobuf__.manifest))

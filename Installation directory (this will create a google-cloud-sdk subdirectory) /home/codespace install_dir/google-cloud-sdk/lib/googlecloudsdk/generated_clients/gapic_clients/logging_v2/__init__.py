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
from googlecloudsdk.generated_clients.gapic_clients.logging_v2 import gapic_version as package_version

__version__ = package_version.__version__


from .services.config_service_v2 import ConfigServiceV2Client
from .services.config_service_v2 import ConfigServiceV2AsyncClient
from .services.logging_service_v2 import LoggingServiceV2Client
from .services.logging_service_v2 import LoggingServiceV2AsyncClient
from .services.metrics_service_v2 import MetricsServiceV2Client
from .services.metrics_service_v2 import MetricsServiceV2AsyncClient

from .types.log_entry import LogEntry
from .types.log_entry import LogEntryOperation
from .types.log_entry import LogEntrySourceLocation
from .types.log_entry import LogErrorGroup
from .types.log_entry import LogSplit
from .types.logging import DeleteLogRequest
from .types.logging import ListLogEntriesRequest
from .types.logging import ListLogEntriesResponse
from .types.logging import ListLogsRequest
from .types.logging import ListLogsResponse
from .types.logging import ListMonitoredResourceDescriptorsRequest
from .types.logging import ListMonitoredResourceDescriptorsResponse
from .types.logging import TailLogEntriesRequest
from .types.logging import TailLogEntriesResponse
from .types.logging import WriteLogEntriesPartialErrors
from .types.logging import WriteLogEntriesRequest
from .types.logging import WriteLogEntriesResponse
from .types.logging_config import BigQueryDataset
from .types.logging_config import BigQueryOptions
from .types.logging_config import BucketMetadata
from .types.logging_config import CmekSettings
from .types.logging_config import CopyLogEntriesMetadata
from .types.logging_config import CopyLogEntriesRequest
from .types.logging_config import CopyLogEntriesResponse
from .types.logging_config import CreateBucketRequest
from .types.logging_config import CreateExclusionRequest
from .types.logging_config import CreateLinkRequest
from .types.logging_config import CreateSavedQueryRequest
from .types.logging_config import CreateSinkRequest
from .types.logging_config import CreateViewRequest
from .types.logging_config import DeleteBucketRequest
from .types.logging_config import DeleteExclusionRequest
from .types.logging_config import DeleteLinkRequest
from .types.logging_config import DeleteSavedQueryRequest
from .types.logging_config import DeleteSinkRequest
from .types.logging_config import DeleteViewRequest
from .types.logging_config import GetBucketRequest
from .types.logging_config import GetCmekSettingsRequest
from .types.logging_config import GetExclusionRequest
from .types.logging_config import GetLinkRequest
from .types.logging_config import GetSettingsRequest
from .types.logging_config import GetSinkRequest
from .types.logging_config import GetViewRequest
from .types.logging_config import IndexConfig
from .types.logging_config import Link
from .types.logging_config import LinkMetadata
from .types.logging_config import ListBucketsRequest
from .types.logging_config import ListBucketsResponse
from .types.logging_config import ListExclusionsRequest
from .types.logging_config import ListExclusionsResponse
from .types.logging_config import ListLinksRequest
from .types.logging_config import ListLinksResponse
from .types.logging_config import ListRecentQueriesRequest
from .types.logging_config import ListRecentQueriesResponse
from .types.logging_config import ListSavedQueriesRequest
from .types.logging_config import ListSavedQueriesResponse
from .types.logging_config import ListSinksRequest
from .types.logging_config import ListSinksResponse
from .types.logging_config import ListViewsRequest
from .types.logging_config import ListViewsResponse
from .types.logging_config import LocationMetadata
from .types.logging_config import LogBucket
from .types.logging_config import LogExclusion
from .types.logging_config import LoggingQuery
from .types.logging_config import LogSink
from .types.logging_config import LogView
from .types.logging_config import OpsAnalyticsQuery
from .types.logging_config import RecentQuery
from .types.logging_config import SavedQuery
from .types.logging_config import Settings
from .types.logging_config import UndeleteBucketRequest
from .types.logging_config import UpdateBucketRequest
from .types.logging_config import UpdateCmekSettingsRequest
from .types.logging_config import UpdateExclusionRequest
from .types.logging_config import UpdateSettingsRequest
from .types.logging_config import UpdateSinkRequest
from .types.logging_config import UpdateViewRequest
from .types.logging_config import IndexType
from .types.logging_config import LifecycleState
from .types.logging_config import OperationState
from .types.logging_metrics import CreateLogMetricRequest
from .types.logging_metrics import DeleteLogMetricRequest
from .types.logging_metrics import GetLogMetricRequest
from .types.logging_metrics import ListLogMetricsRequest
from .types.logging_metrics import ListLogMetricsResponse
from .types.logging_metrics import LogMetric
from .types.logging_metrics import UpdateLogMetricRequest

__all__ = (
    'ConfigServiceV2AsyncClient',
    'LoggingServiceV2AsyncClient',
    'MetricsServiceV2AsyncClient',
'BigQueryDataset',
'BigQueryOptions',
'BucketMetadata',
'CmekSettings',
'ConfigServiceV2Client',
'CopyLogEntriesMetadata',
'CopyLogEntriesRequest',
'CopyLogEntriesResponse',
'CreateBucketRequest',
'CreateExclusionRequest',
'CreateLinkRequest',
'CreateLogMetricRequest',
'CreateSavedQueryRequest',
'CreateSinkRequest',
'CreateViewRequest',
'DeleteBucketRequest',
'DeleteExclusionRequest',
'DeleteLinkRequest',
'DeleteLogMetricRequest',
'DeleteLogRequest',
'DeleteSavedQueryRequest',
'DeleteSinkRequest',
'DeleteViewRequest',
'GetBucketRequest',
'GetCmekSettingsRequest',
'GetExclusionRequest',
'GetLinkRequest',
'GetLogMetricRequest',
'GetSettingsRequest',
'GetSinkRequest',
'GetViewRequest',
'IndexConfig',
'IndexType',
'LifecycleState',
'Link',
'LinkMetadata',
'ListBucketsRequest',
'ListBucketsResponse',
'ListExclusionsRequest',
'ListExclusionsResponse',
'ListLinksRequest',
'ListLinksResponse',
'ListLogEntriesRequest',
'ListLogEntriesResponse',
'ListLogMetricsRequest',
'ListLogMetricsResponse',
'ListLogsRequest',
'ListLogsResponse',
'ListMonitoredResourceDescriptorsRequest',
'ListMonitoredResourceDescriptorsResponse',
'ListRecentQueriesRequest',
'ListRecentQueriesResponse',
'ListSavedQueriesRequest',
'ListSavedQueriesResponse',
'ListSinksRequest',
'ListSinksResponse',
'ListViewsRequest',
'ListViewsResponse',
'LocationMetadata',
'LogBucket',
'LogEntry',
'LogEntryOperation',
'LogEntrySourceLocation',
'LogErrorGroup',
'LogExclusion',
'LogMetric',
'LogSink',
'LogSplit',
'LogView',
'LoggingQuery',
'LoggingServiceV2Client',
'MetricsServiceV2Client',
'OperationState',
'OpsAnalyticsQuery',
'RecentQuery',
'SavedQuery',
'Settings',
'TailLogEntriesRequest',
'TailLogEntriesResponse',
'UndeleteBucketRequest',
'UpdateBucketRequest',
'UpdateCmekSettingsRequest',
'UpdateExclusionRequest',
'UpdateLogMetricRequest',
'UpdateSettingsRequest',
'UpdateSinkRequest',
'UpdateViewRequest',
'WriteLogEntriesPartialErrors',
'WriteLogEntriesRequest',
'WriteLogEntriesResponse',
)

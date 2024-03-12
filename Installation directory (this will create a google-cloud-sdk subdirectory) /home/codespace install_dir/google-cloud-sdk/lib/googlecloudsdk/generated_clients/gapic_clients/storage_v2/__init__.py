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
from googlecloudsdk.generated_clients.gapic_clients.storage_v2 import gapic_version as package_version

__version__ = package_version.__version__


from .services.storage import StorageClient
from .services.storage import StorageAsyncClient

from .types.storage import BidiWriteObjectRequest
from .types.storage import BidiWriteObjectResponse
from .types.storage import Bucket
from .types.storage import BucketAccessControl
from .types.storage import CancelResumableWriteRequest
from .types.storage import CancelResumableWriteResponse
from .types.storage import ChecksummedData
from .types.storage import CommonObjectRequestParams
from .types.storage import ComposeObjectRequest
from .types.storage import ContentRange
from .types.storage import CreateBucketRequest
from .types.storage import CreateHmacKeyRequest
from .types.storage import CreateHmacKeyResponse
from .types.storage import CreateNotificationConfigRequest
from .types.storage import CustomerEncryption
from .types.storage import DeleteBucketRequest
from .types.storage import DeleteHmacKeyRequest
from .types.storage import DeleteNotificationConfigRequest
from .types.storage import DeleteObjectRequest
from .types.storage import GetBucketRequest
from .types.storage import GetHmacKeyRequest
from .types.storage import GetNotificationConfigRequest
from .types.storage import GetObjectRequest
from .types.storage import GetServiceAccountRequest
from .types.storage import HmacKeyMetadata
from .types.storage import ListBucketsRequest
from .types.storage import ListBucketsResponse
from .types.storage import ListHmacKeysRequest
from .types.storage import ListHmacKeysResponse
from .types.storage import ListNotificationConfigsRequest
from .types.storage import ListNotificationConfigsResponse
from .types.storage import ListObjectsRequest
from .types.storage import ListObjectsResponse
from .types.storage import LockBucketRetentionPolicyRequest
from .types.storage import NotificationConfig
from .types.storage import Object
from .types.storage import ObjectAccessControl
from .types.storage import ObjectChecksums
from .types.storage import Owner
from .types.storage import ProjectTeam
from .types.storage import QueryWriteStatusRequest
from .types.storage import QueryWriteStatusResponse
from .types.storage import ReadObjectRequest
from .types.storage import ReadObjectResponse
from .types.storage import RestoreObjectRequest
from .types.storage import RewriteObjectRequest
from .types.storage import RewriteResponse
from .types.storage import ServiceAccount
from .types.storage import ServiceConstants
from .types.storage import StartResumableWriteRequest
from .types.storage import StartResumableWriteResponse
from .types.storage import UpdateBucketRequest
from .types.storage import UpdateHmacKeyRequest
from .types.storage import UpdateObjectRequest
from .types.storage import WriteObjectRequest
from .types.storage import WriteObjectResponse
from .types.storage import WriteObjectSpec

__all__ = (
    'StorageAsyncClient',
'BidiWriteObjectRequest',
'BidiWriteObjectResponse',
'Bucket',
'BucketAccessControl',
'CancelResumableWriteRequest',
'CancelResumableWriteResponse',
'ChecksummedData',
'CommonObjectRequestParams',
'ComposeObjectRequest',
'ContentRange',
'CreateBucketRequest',
'CreateHmacKeyRequest',
'CreateHmacKeyResponse',
'CreateNotificationConfigRequest',
'CustomerEncryption',
'DeleteBucketRequest',
'DeleteHmacKeyRequest',
'DeleteNotificationConfigRequest',
'DeleteObjectRequest',
'GetBucketRequest',
'GetHmacKeyRequest',
'GetNotificationConfigRequest',
'GetObjectRequest',
'GetServiceAccountRequest',
'HmacKeyMetadata',
'ListBucketsRequest',
'ListBucketsResponse',
'ListHmacKeysRequest',
'ListHmacKeysResponse',
'ListNotificationConfigsRequest',
'ListNotificationConfigsResponse',
'ListObjectsRequest',
'ListObjectsResponse',
'LockBucketRetentionPolicyRequest',
'NotificationConfig',
'Object',
'ObjectAccessControl',
'ObjectChecksums',
'Owner',
'ProjectTeam',
'QueryWriteStatusRequest',
'QueryWriteStatusResponse',
'ReadObjectRequest',
'ReadObjectResponse',
'RestoreObjectRequest',
'RewriteObjectRequest',
'RewriteResponse',
'ServiceAccount',
'ServiceConstants',
'StartResumableWriteRequest',
'StartResumableWriteResponse',
'StorageClient',
'UpdateBucketRequest',
'UpdateHmacKeyRequest',
'UpdateObjectRequest',
'WriteObjectRequest',
'WriteObjectResponse',
'WriteObjectSpec',
)

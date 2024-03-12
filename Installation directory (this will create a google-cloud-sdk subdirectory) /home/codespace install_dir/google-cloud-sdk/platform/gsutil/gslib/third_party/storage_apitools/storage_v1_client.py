# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Generated client library for storage version v1."""

import platform
import sys

from apitools.base.py import base_api

import gslib
from gslib.metrics import MetricsCollector
from gslib.third_party.storage_apitools import storage_v1_messages as messages


class StorageV1(base_api.BaseApiClient):
  """Generated client library for service storage version v1."""

  MESSAGES_MODULE = messages
  BASE_URL = u'https://www.googleapis.com/storage/v1/'

  _PACKAGE = u'storage'
  _SCOPES = [u'https://www.googleapis.com/auth/cloud-platform', u'https://www.googleapis.com/auth/cloud-platform.read-only', u'https://www.googleapis.com/auth/devstorage.full_control', u'https://www.googleapis.com/auth/devstorage.read_only', u'https://www.googleapis.com/auth/devstorage.read_write']
  _VERSION = u'v1'
  _CLIENT_ID = 'nomatter'
  _CLIENT_SECRET = 'nomatter'
  _USER_AGENT = 'apitools Python/%s' % platform.python_version()
  _USER_AGENT += gslib.USER_AGENT

  _CLIENT_CLASS_NAME = u'StorageV1'
  _URL_VERSION = u'v1'
  _API_KEY = None

  def __init__(self, url='', credentials=None,
               get_credentials=True, http=None, model=None,
               log_request=False, log_response=False,
               credentials_args=None, default_global_params=None,
               version=_VERSION,
               additional_http_headers=None, response_encoding=None):
    """Create a new storage handle."""
    url = url or self.BASE_URL
    super(StorageV1, self).__init__(
        url, credentials=credentials,
        get_credentials=get_credentials, http=http, model=model,
        log_request=log_request, log_response=log_response,
        credentials_args=credentials_args,
        default_global_params=default_global_params,
        additional_http_headers=additional_http_headers,
        response_encoding=response_encoding)
    self._version = version
    self.bucketAccessControls = self.BucketAccessControlsService(self)
    self.buckets = self.BucketsService(self)
    self.channels = self.ChannelsService(self)
    self.defaultObjectAccessControls = self.DefaultObjectAccessControlsService(self)
    self.notifications = self.NotificationsService(self)
    self.objectAccessControls = self.ObjectAccessControlsService(self)
    self.objects = self.ObjectsService(self)
    self.projects_serviceAccount = self.ProjectsServiceAccountService(self)
    self.projects = self.ProjectsService(self)
    self.hmacKeys = self.HmacKeysService(self)

  class BucketAccessControlsService(base_api.BaseApiService):
    """Service class for the bucketAccessControls resource."""

    _NAME = u'bucketAccessControls'

    def __init__(self, client):
      super(StorageV1.BucketAccessControlsService, self).__init__(client)
      self._upload_configs = {
          }

    def Delete(self, request, global_params=None):
      r"""Permanently deletes the ACL entry for the specified entity on the specified bucket.

      Args:
        request: (StorageBucketAccessControlsDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (StorageBucketAccessControlsDeleteResponse) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    Delete.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'DELETE',
        method_id=u'storage.bucketAccessControls.delete',
        ordered_params=[u'bucket', u'entity'],
        path_params=[u'bucket', u'entity'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/acl/{entity}',
        request_field='',
        request_type_name=u'StorageBucketAccessControlsDeleteRequest',
        response_type_name=u'StorageBucketAccessControlsDeleteResponse',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      r"""Returns the ACL entry for the specified entity on the specified bucket.

      Args:
        request: (StorageBucketAccessControlsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (BucketAccessControl) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.bucketAccessControls.get',
        ordered_params=[u'bucket', u'entity'],
        path_params=[u'bucket', u'entity'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/acl/{entity}',
        request_field='',
        request_type_name=u'StorageBucketAccessControlsGetRequest',
        response_type_name=u'BucketAccessControl',
        supports_download=False,
    )

    def Insert(self, request, global_params=None):
      r"""Creates a new ACL entry on the specified bucket.

      Args:
        request: (StorageBucketAccessControlsInsertRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (BucketAccessControl) The response message.
      """
      config = self.GetMethodConfig('Insert')
      return self._RunMethod(
          config, request, global_params=global_params)

    Insert.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'storage.bucketAccessControls.insert',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/acl',
        request_field=u'bucketAccessControl',
        request_type_name=u'StorageBucketAccessControlsInsertRequest',
        response_type_name=u'BucketAccessControl',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Retrieves ACL entries on the specified bucket.

      Args:
        request: (StorageBucketAccessControlsListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (BucketAccessControls) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.bucketAccessControls.list',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/acl',
        request_field='',
        request_type_name=u'StorageBucketAccessControlsListRequest',
        response_type_name=u'BucketAccessControls',
        supports_download=False,
    )

    def Patch(self, request, global_params=None):
      r"""Patches an ACL entry on the specified bucket.

      Args:
        request: (StorageBucketAccessControlsPatchRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (BucketAccessControl) The response message.
      """
      config = self.GetMethodConfig('Patch')
      return self._RunMethod(
          config, request, global_params=global_params)

    Patch.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PATCH',
        method_id=u'storage.bucketAccessControls.patch',
        ordered_params=[u'bucket', u'entity'],
        path_params=[u'bucket', u'entity'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/acl/{entity}',
        request_field=u'bucketAccessControl',
        request_type_name=u'StorageBucketAccessControlsPatchRequest',
        response_type_name=u'BucketAccessControl',
        supports_download=False,
    )

    def Update(self, request, global_params=None):
      r"""Updates an ACL entry on the specified bucket.

      Args:
        request: (StorageBucketAccessControlsUpdateRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (BucketAccessControl) The response message.
      """
      config = self.GetMethodConfig('Update')
      return self._RunMethod(
          config, request, global_params=global_params)

    Update.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PUT',
        method_id=u'storage.bucketAccessControls.update',
        ordered_params=[u'bucket', u'entity'],
        path_params=[u'bucket', u'entity'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/acl/{entity}',
        request_field=u'bucketAccessControl',
        request_type_name=u'StorageBucketAccessControlsUpdateRequest',
        response_type_name=u'BucketAccessControl',
        supports_download=False,
    )

  class BucketsService(base_api.BaseApiService):
    """Service class for the buckets resource."""

    _NAME = u'buckets'

    def __init__(self, client):
      super(StorageV1.BucketsService, self).__init__(client)
      self._upload_configs = {
          }

    def Delete(self, request, global_params=None):
      r"""Permanently deletes an empty bucket.

      Args:
        request: (StorageBucketsDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (StorageBucketsDeleteResponse) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    Delete.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'DELETE',
        method_id=u'storage.buckets.delete',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'ifMetagenerationMatch', u'ifMetagenerationNotMatch', u'userProject'],
        relative_path=u'b/{bucket}',
        request_field='',
        request_type_name=u'StorageBucketsDeleteRequest',
        response_type_name=u'StorageBucketsDeleteResponse',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      r"""Returns metadata for the specified bucket.

      Args:
        request: (StorageBucketsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Bucket) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.buckets.get',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'ifMetagenerationMatch', u'ifMetagenerationNotMatch', u'projection', u'userProject'],
        relative_path=u'b/{bucket}',
        request_field='',
        request_type_name=u'StorageBucketsGetRequest',
        response_type_name=u'Bucket',
        supports_download=False,
    )

    def GetIamPolicy(self, request, global_params=None):
      r"""Returns an IAM policy for the specified bucket.

      Args:
        request: (StorageBucketsGetIamPolicyRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Policy) The response message.
      """
      config = self.GetMethodConfig('GetIamPolicy')
      return self._RunMethod(
          config, request, global_params=global_params)

    GetIamPolicy.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.buckets.getIamPolicy',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'provisionalUserProject', u'optionsRequestedPolicyVersion', u'userProject'],
        relative_path=u'b/{bucket}/iam',
        request_field='',
        request_type_name=u'StorageBucketsGetIamPolicyRequest',
        response_type_name=u'Policy',
        supports_download=False,
    )

    def Insert(self, request, global_params=None):
      r"""Creates a new bucket.

      Args:
        request: (StorageBucketsInsertRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Bucket) The response message.
      """
      config = self.GetMethodConfig('Insert')
      return self._RunMethod(
          config, request, global_params=global_params)

    Insert.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'storage.buckets.insert',
        ordered_params=[u'project'],
        path_params=[],
        query_params=[u'predefinedAcl', u'predefinedDefaultObjectAcl', u'project', u'projection', u'userProject'],
        relative_path=u'b',
        request_field=u'bucket',
        request_type_name=u'StorageBucketsInsertRequest',
        response_type_name=u'Bucket',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Retrieves a list of buckets for a given project.

      Args:
        request: (StorageBucketsListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Buckets) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.buckets.list',
        ordered_params=[u'project'],
        path_params=[],
        query_params=[u'maxResults', u'pageToken', u'prefix', u'project', u'projection', u'userProject'],
        relative_path=u'b',
        request_field='',
        request_type_name=u'StorageBucketsListRequest',
        response_type_name=u'Buckets',
        supports_download=False,
    )

    def ListChannels(self, request, global_params=None):
      r"""List active object change notification channels for this bucket.

      Args:
        request: (StorageBucketsListChannelsRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Channels) The response message.
      """
      config = self.GetMethodConfig('ListChannels')
      return self._RunMethod(
          config, request, global_params=global_params)

    ListChannels.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.buckets.listChannels',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/channels',
        request_field='',
        request_type_name=u'StorageBucketsListChannelsRequest',
        response_type_name=u'Channels',
        supports_download=False,
    )

    def LockRetentionPolicy(self, request, global_params=None):
      r"""Locks retention policy on a bucket.

      Args:
        request: (StorageBucketsLockRetentionPolicyRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Bucket) The response message.
      """
      config = self.GetMethodConfig('LockRetentionPolicy')
      return self._RunMethod(
          config, request, global_params=global_params)

    LockRetentionPolicy.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'storage.buckets.lockRetentionPolicy',
        ordered_params=[u'bucket', u'ifMetagenerationMatch'],
        path_params=[u'bucket'],
        query_params=[u'ifMetagenerationMatch', u'userProject'],
        relative_path=u'b/{bucket}/lockRetentionPolicy',
        request_field='',
        request_type_name=u'StorageBucketsLockRetentionPolicyRequest',
        response_type_name=u'Bucket',
        supports_download=False,
    )

    def Patch(self, request, global_params=None):
      r"""Patches a bucket. Changes to the bucket will be readable immediately after writing, but configuration changes may take time to propagate.

      Args:
        request: (StorageBucketsPatchRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Bucket) The response message.
      """
      config = self.GetMethodConfig('Patch')
      return self._RunMethod(
          config, request, global_params=global_params)

    Patch.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PATCH',
        method_id=u'storage.buckets.patch',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'ifMetagenerationMatch', u'ifMetagenerationNotMatch', u'predefinedAcl', u'predefinedDefaultObjectAcl', u'projection', u'userProject'],
        relative_path=u'b/{bucket}',
        request_field=u'bucketResource',
        request_type_name=u'StorageBucketsPatchRequest',
        response_type_name=u'Bucket',
        supports_download=False,
    )

    def SetIamPolicy(self, request, global_params=None):
      r"""Updates an IAM policy for the specified bucket.

      Args:
        request: (StorageBucketsSetIamPolicyRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Policy) The response message.
      """
      config = self.GetMethodConfig('SetIamPolicy')
      return self._RunMethod(
          config, request, global_params=global_params)

    SetIamPolicy.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PUT',
        method_id=u'storage.buckets.setIamPolicy',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/iam',
        request_field=u'policy',
        request_type_name=u'StorageBucketsSetIamPolicyRequest',
        response_type_name=u'Policy',
        supports_download=False,
    )

    def TestIamPermissions(self, request, global_params=None):
      r"""Tests a set of permissions on the given bucket to see which, if any, are held by the caller.

      Args:
        request: (StorageBucketsTestIamPermissionsRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (TestIamPermissionsResponse) The response message.
      """
      config = self.GetMethodConfig('TestIamPermissions')
      return self._RunMethod(
          config, request, global_params=global_params)

    TestIamPermissions.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.buckets.testIamPermissions',
        ordered_params=[u'bucket', u'permissions'],
        path_params=[u'bucket'],
        query_params=[u'permissions', u'userProject'],
        relative_path=u'b/{bucket}/iam/testPermissions',
        request_field='',
        request_type_name=u'StorageBucketsTestIamPermissionsRequest',
        response_type_name=u'TestIamPermissionsResponse',
        supports_download=False,
    )

    def Update(self, request, global_params=None):
      r"""Updates a bucket. Changes to the bucket will be readable immediately after writing, but configuration changes may take time to propagate.

      Args:
        request: (StorageBucketsUpdateRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Bucket) The response message.
      """
      config = self.GetMethodConfig('Update')
      return self._RunMethod(
          config, request, global_params=global_params)

    Update.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PUT',
        method_id=u'storage.buckets.update',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'ifMetagenerationMatch', u'ifMetagenerationNotMatch', u'predefinedAcl', u'predefinedDefaultObjectAcl', u'projection', u'userProject'],
        relative_path=u'b/{bucket}',
        request_field=u'bucketResource',
        request_type_name=u'StorageBucketsUpdateRequest',
        response_type_name=u'Bucket',
        supports_download=False,
    )

  class ChannelsService(base_api.BaseApiService):
    """Service class for the channels resource."""

    _NAME = u'channels'

    def __init__(self, client):
      super(StorageV1.ChannelsService, self).__init__(client)
      self._upload_configs = {
          }

    def Stop(self, request, global_params=None):
      r"""Stop watching resources through this channel.

      Args:
        request: (Channel) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (StorageChannelsStopResponse) The response message.
      """
      config = self.GetMethodConfig('Stop')
      return self._RunMethod(
          config, request, global_params=global_params)

    Stop.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'storage.channels.stop',
        ordered_params=[],
        path_params=[],
        query_params=[],
        relative_path=u'channels/stop',
        request_field='<request>',
        request_type_name=u'Channel',
        response_type_name=u'StorageChannelsStopResponse',
        supports_download=False,
    )

  class DefaultObjectAccessControlsService(base_api.BaseApiService):
    """Service class for the defaultObjectAccessControls resource."""

    _NAME = u'defaultObjectAccessControls'

    def __init__(self, client):
      super(StorageV1.DefaultObjectAccessControlsService, self).__init__(client)
      self._upload_configs = {
          }

    def Delete(self, request, global_params=None):
      r"""Permanently deletes the default object ACL entry for the specified entity on the specified bucket.

      Args:
        request: (StorageDefaultObjectAccessControlsDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (StorageDefaultObjectAccessControlsDeleteResponse) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    Delete.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'DELETE',
        method_id=u'storage.defaultObjectAccessControls.delete',
        ordered_params=[u'bucket', u'entity'],
        path_params=[u'bucket', u'entity'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/defaultObjectAcl/{entity}',
        request_field='',
        request_type_name=u'StorageDefaultObjectAccessControlsDeleteRequest',
        response_type_name=u'StorageDefaultObjectAccessControlsDeleteResponse',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      r"""Returns the default object ACL entry for the specified entity on the specified bucket.

      Args:
        request: (StorageDefaultObjectAccessControlsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ObjectAccessControl) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.defaultObjectAccessControls.get',
        ordered_params=[u'bucket', u'entity'],
        path_params=[u'bucket', u'entity'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/defaultObjectAcl/{entity}',
        request_field='',
        request_type_name=u'StorageDefaultObjectAccessControlsGetRequest',
        response_type_name=u'ObjectAccessControl',
        supports_download=False,
    )

    def Insert(self, request, global_params=None):
      r"""Creates a new default object ACL entry on the specified bucket.

      Args:
        request: (StorageDefaultObjectAccessControlsInsertRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ObjectAccessControl) The response message.
      """
      config = self.GetMethodConfig('Insert')
      return self._RunMethod(
          config, request, global_params=global_params)

    Insert.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'storage.defaultObjectAccessControls.insert',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/defaultObjectAcl',
        request_field=u'objectAccessControl',
        request_type_name=u'StorageDefaultObjectAccessControlsInsertRequest',
        response_type_name=u'ObjectAccessControl',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Retrieves default object ACL entries on the specified bucket.

      Args:
        request: (StorageDefaultObjectAccessControlsListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ObjectAccessControls) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.defaultObjectAccessControls.list',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'ifMetagenerationMatch', u'ifMetagenerationNotMatch', u'userProject'],
        relative_path=u'b/{bucket}/defaultObjectAcl',
        request_field='',
        request_type_name=u'StorageDefaultObjectAccessControlsListRequest',
        response_type_name=u'ObjectAccessControls',
        supports_download=False,
    )

    def Patch(self, request, global_params=None):
      r"""Patches a default object ACL entry on the specified bucket.

      Args:
        request: (StorageDefaultObjectAccessControlsPatchRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ObjectAccessControl) The response message.
      """
      config = self.GetMethodConfig('Patch')
      return self._RunMethod(
          config, request, global_params=global_params)

    Patch.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PATCH',
        method_id=u'storage.defaultObjectAccessControls.patch',
        ordered_params=[u'bucket', u'entity'],
        path_params=[u'bucket', u'entity'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/defaultObjectAcl/{entity}',
        request_field=u'objectAccessControl',
        request_type_name=u'StorageDefaultObjectAccessControlsPatchRequest',
        response_type_name=u'ObjectAccessControl',
        supports_download=False,
    )

    def Update(self, request, global_params=None):
      r"""Updates a default object ACL entry on the specified bucket.

      Args:
        request: (StorageDefaultObjectAccessControlsUpdateRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ObjectAccessControl) The response message.
      """
      config = self.GetMethodConfig('Update')
      return self._RunMethod(
          config, request, global_params=global_params)

    Update.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PUT',
        method_id=u'storage.defaultObjectAccessControls.update',
        ordered_params=[u'bucket', u'entity'],
        path_params=[u'bucket', u'entity'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/defaultObjectAcl/{entity}',
        request_field=u'objectAccessControl',
        request_type_name=u'StorageDefaultObjectAccessControlsUpdateRequest',
        response_type_name=u'ObjectAccessControl',
        supports_download=False,
    )

  class NotificationsService(base_api.BaseApiService):
    """Service class for the notifications resource."""

    _NAME = u'notifications'

    def __init__(self, client):
      super(StorageV1.NotificationsService, self).__init__(client)
      self._upload_configs = {
          }

    def Delete(self, request, global_params=None):
      r"""Permanently deletes a notification subscription.

      Args:
        request: (StorageNotificationsDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (StorageNotificationsDeleteResponse) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    Delete.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'DELETE',
        method_id=u'storage.notifications.delete',
        ordered_params=[u'bucket', u'notification'],
        path_params=[u'bucket', u'notification'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/notificationConfigs/{notification}',
        request_field='',
        request_type_name=u'StorageNotificationsDeleteRequest',
        response_type_name=u'StorageNotificationsDeleteResponse',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      r"""View a notification configuration.

      Args:
        request: (StorageNotificationsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Notification) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.notifications.get',
        ordered_params=[u'bucket', u'notification'],
        path_params=[u'bucket', u'notification'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/notificationConfigs/{notification}',
        request_field='',
        request_type_name=u'StorageNotificationsGetRequest',
        response_type_name=u'Notification',
        supports_download=False,
    )

    def Insert(self, request, global_params=None):
      r"""Creates a notification subscription for a given bucket.

      Args:
        request: (StorageNotificationsInsertRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Notification) The response message.
      """
      config = self.GetMethodConfig('Insert')
      return self._RunMethod(
          config, request, global_params=global_params)

    Insert.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'storage.notifications.insert',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/notificationConfigs',
        request_field=u'notification',
        request_type_name=u'StorageNotificationsInsertRequest',
        response_type_name=u'Notification',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Retrieves a list of notification subscriptions for a given bucket.

      Args:
        request: (StorageNotificationsListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Notifications) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.notifications.list',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'userProject'],
        relative_path=u'b/{bucket}/notificationConfigs',
        request_field='',
        request_type_name=u'StorageNotificationsListRequest',
        response_type_name=u'Notifications',
        supports_download=False,
    )

  class ObjectAccessControlsService(base_api.BaseApiService):
    """Service class for the objectAccessControls resource."""

    _NAME = u'objectAccessControls'

    def __init__(self, client):
      super(StorageV1.ObjectAccessControlsService, self).__init__(client)
      self._upload_configs = {
          }

    def Delete(self, request, global_params=None):
      r"""Permanently deletes the ACL entry for the specified entity on the specified object.

      Args:
        request: (StorageObjectAccessControlsDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (StorageObjectAccessControlsDeleteResponse) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    Delete.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'DELETE',
        method_id=u'storage.objectAccessControls.delete',
        ordered_params=[u'bucket', u'object', u'entity'],
        path_params=[u'bucket', u'entity', u'object'],
        query_params=[u'generation', u'userProject'],
        relative_path=u'b/{bucket}/o/{object}/acl/{entity}',
        request_field='',
        request_type_name=u'StorageObjectAccessControlsDeleteRequest',
        response_type_name=u'StorageObjectAccessControlsDeleteResponse',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      r"""Returns the ACL entry for the specified entity on the specified object.

      Args:
        request: (StorageObjectAccessControlsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ObjectAccessControl) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.objectAccessControls.get',
        ordered_params=[u'bucket', u'object', u'entity'],
        path_params=[u'bucket', u'entity', u'object'],
        query_params=[u'generation', u'userProject'],
        relative_path=u'b/{bucket}/o/{object}/acl/{entity}',
        request_field='',
        request_type_name=u'StorageObjectAccessControlsGetRequest',
        response_type_name=u'ObjectAccessControl',
        supports_download=False,
    )

    def Insert(self, request, global_params=None):
      r"""Creates a new ACL entry on the specified object.

      Args:
        request: (StorageObjectAccessControlsInsertRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ObjectAccessControl) The response message.
      """
      config = self.GetMethodConfig('Insert')
      return self._RunMethod(
          config, request, global_params=global_params)

    Insert.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'storage.objectAccessControls.insert',
        ordered_params=[u'bucket', u'object'],
        path_params=[u'bucket', u'object'],
        query_params=[u'generation', u'userProject'],
        relative_path=u'b/{bucket}/o/{object}/acl',
        request_field=u'objectAccessControl',
        request_type_name=u'StorageObjectAccessControlsInsertRequest',
        response_type_name=u'ObjectAccessControl',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Retrieves ACL entries on the specified object.

      Args:
        request: (StorageObjectAccessControlsListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ObjectAccessControls) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.objectAccessControls.list',
        ordered_params=[u'bucket', u'object'],
        path_params=[u'bucket', u'object'],
        query_params=[u'generation', u'userProject'],
        relative_path=u'b/{bucket}/o/{object}/acl',
        request_field='',
        request_type_name=u'StorageObjectAccessControlsListRequest',
        response_type_name=u'ObjectAccessControls',
        supports_download=False,
    )

    def Patch(self, request, global_params=None):
      r"""Patches an ACL entry on the specified object.

      Args:
        request: (StorageObjectAccessControlsPatchRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ObjectAccessControl) The response message.
      """
      config = self.GetMethodConfig('Patch')
      return self._RunMethod(
          config, request, global_params=global_params)

    Patch.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PATCH',
        method_id=u'storage.objectAccessControls.patch',
        ordered_params=[u'bucket', u'object', u'entity'],
        path_params=[u'bucket', u'entity', u'object'],
        query_params=[u'generation', u'userProject'],
        relative_path=u'b/{bucket}/o/{object}/acl/{entity}',
        request_field=u'objectAccessControl',
        request_type_name=u'StorageObjectAccessControlsPatchRequest',
        response_type_name=u'ObjectAccessControl',
        supports_download=False,
    )

    def Update(self, request, global_params=None):
      r"""Updates an ACL entry on the specified object.

      Args:
        request: (StorageObjectAccessControlsUpdateRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ObjectAccessControl) The response message.
      """
      config = self.GetMethodConfig('Update')
      return self._RunMethod(
          config, request, global_params=global_params)

    Update.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PUT',
        method_id=u'storage.objectAccessControls.update',
        ordered_params=[u'bucket', u'object', u'entity'],
        path_params=[u'bucket', u'entity', u'object'],
        query_params=[u'generation', u'userProject'],
        relative_path=u'b/{bucket}/o/{object}/acl/{entity}',
        request_field=u'objectAccessControl',
        request_type_name=u'StorageObjectAccessControlsUpdateRequest',
        response_type_name=u'ObjectAccessControl',
        supports_download=False,
    )

  class ObjectsService(base_api.BaseApiService):
    """Service class for the objects resource."""

    _NAME = u'objects'

    def __init__(self, client):
      super(StorageV1.ObjectsService, self).__init__(client)
      self._upload_configs = {
          'Insert': base_api.ApiUploadInfo(
              accept=['*/*'],
              max_size=None,
              resumable_multipart=True,
              resumable_path=u'/resumable/upload/storage/' + self._client._version + '/b/{bucket}/o',
              simple_multipart=True,
              simple_path=u'/upload/storage/' + self._client._version + '/b/{bucket}/o',
          ),
          }

    def Compose(self, request, global_params=None):
      r"""Concatenates a list of existing objects into a new object in the same bucket.

      Args:
        request: (StorageObjectsComposeRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Object) The response message.
      """
      config = self.GetMethodConfig('Compose')
      return self._RunMethod(
          config, request, global_params=global_params)

    Compose.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'storage.objects.compose',
        ordered_params=[u'destinationBucket', u'destinationObject'],
        path_params=[u'destinationBucket', u'destinationObject'],
        query_params=[u'destinationPredefinedAcl', u'ifGenerationMatch', u'ifMetagenerationMatch', u'kmsKeyName', u'userProject'],
        relative_path=u'b/{destinationBucket}/o/{destinationObject}/compose',
        request_field=u'composeRequest',
        request_type_name=u'StorageObjectsComposeRequest',
        response_type_name=u'Object',
        supports_download=False,
    )

    def Copy(self, request, global_params=None):
      r"""Copies a source object to a destination object. Optionally overrides metadata.

      Args:
        request: (StorageObjectsCopyRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Object) The response message.
      """
      config = self.GetMethodConfig('Copy')
      return self._RunMethod(
          config, request, global_params=global_params)

    Copy.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'storage.objects.copy',
        ordered_params=[u'sourceBucket', u'sourceObject', u'destinationBucket', u'destinationObject'],
        path_params=[u'destinationBucket', u'destinationObject', u'sourceBucket', u'sourceObject'],
        query_params=[u'destinationPredefinedAcl', u'ifGenerationMatch', u'ifGenerationNotMatch', u'ifMetagenerationMatch', u'ifMetagenerationNotMatch', u'ifSourceGenerationMatch', u'ifSourceGenerationNotMatch', u'ifSourceMetagenerationMatch', u'ifSourceMetagenerationNotMatch', u'projection', u'sourceGeneration', u'userProject'],
        relative_path=u'b/{sourceBucket}/o/{sourceObject}/copyTo/b/{destinationBucket}/o/{destinationObject}',
        request_field=u'object',
        request_type_name=u'StorageObjectsCopyRequest',
        response_type_name=u'Object',
        supports_download=False,
    )

    def Delete(self, request, global_params=None):
      r"""Deletes an object and its metadata. Deletions are permanent if versioning is not enabled for the bucket, or if the generation parameter is used.

      Args:
        request: (StorageObjectsDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (StorageObjectsDeleteResponse) The response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(
          config, request, global_params=global_params)

    Delete.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'DELETE',
        method_id=u'storage.objects.delete',
        ordered_params=[u'bucket', u'object'],
        path_params=[u'bucket', u'object'],
        query_params=[u'generation', u'ifGenerationMatch', u'ifGenerationNotMatch', u'ifMetagenerationMatch', u'ifMetagenerationNotMatch', u'userProject'],
        relative_path=u'b/{bucket}/o/{object}',
        request_field='',
        request_type_name=u'StorageObjectsDeleteRequest',
        response_type_name=u'StorageObjectsDeleteResponse',
        supports_download=False,
    )

    def Get(self, request, global_params=None, download=None):
      r"""Retrieves an object or its metadata.

      Args:
        request: (StorageObjectsGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
        download: (Download, default: None) If present, download
            data from the request via this stream.
      Returns:
        (Object) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params,
          download=download)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.objects.get',
        ordered_params=[u'bucket', u'object'],
        path_params=[u'bucket', u'object'],
        query_params=[u'generation', u'ifGenerationMatch', u'ifGenerationNotMatch', u'ifMetagenerationMatch', u'ifMetagenerationNotMatch', u'projection', u'userProject'],
        relative_path=u'b/{bucket}/o/{object}',
        request_field='',
        request_type_name=u'StorageObjectsGetRequest',
        response_type_name=u'Object',
        supports_download=True,
    )

    def GetIamPolicy(self, request, global_params=None):
      r"""Returns an IAM policy for the specified object.

      Args:
        request: (StorageObjectsGetIamPolicyRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Policy) The response message.
      """
      config = self.GetMethodConfig('GetIamPolicy')
      return self._RunMethod(
          config, request, global_params=global_params)

    GetIamPolicy.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.objects.getIamPolicy',
        ordered_params=[u'bucket', u'object'],
        path_params=[u'bucket', u'object'],
        query_params=[u'generation', u'userProject'],
        relative_path=u'b/{bucket}/o/{object}/iam',
        request_field='',
        request_type_name=u'StorageObjectsGetIamPolicyRequest',
        response_type_name=u'Policy',
        supports_download=False,
    )

    def Insert(self, request, global_params=None, upload=None):
      r"""Stores a new object and metadata.

      Args:
        request: (StorageObjectsInsertRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
        upload: (Upload, default: None) If present, upload
            this stream with the request.
      Returns:
        (Object) The response message.
      """
      config = self.GetMethodConfig('Insert')
      upload_config = self.GetUploadConfig('Insert')
      return self._RunMethod(
          config, request, global_params=global_params,
          upload=upload, upload_config=upload_config)

    Insert.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'storage.objects.insert',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'contentEncoding', u'ifGenerationMatch', u'ifGenerationNotMatch', u'ifMetagenerationMatch', u'ifMetagenerationNotMatch', u'kmsKeyName', u'name', u'predefinedAcl', u'projection', u'userProject'],
        relative_path=u'b/{bucket}/o',
        request_field=u'object',
        request_type_name=u'StorageObjectsInsertRequest',
        response_type_name=u'Object',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      r"""Retrieves a list of objects matching the criteria.

      Args:
        request: (StorageObjectsListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Objects) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(
          config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.objects.list',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'delimiter', u'includeTrailingDelimiter', u'maxResults', u'pageToken', u'prefix', u'projection', u'userProject', u'versions'],
        relative_path=u'b/{bucket}/o',
        request_field='',
        request_type_name=u'StorageObjectsListRequest',
        response_type_name=u'Objects',
        supports_download=False,
    )

    def Patch(self, request, global_params=None):
      r"""Patches an object's metadata.

      Args:
        request: (StorageObjectsPatchRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Object) The response message.
      """
      config = self.GetMethodConfig('Patch')
      return self._RunMethod(
          config, request, global_params=global_params)

    Patch.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PATCH',
        method_id=u'storage.objects.patch',
        ordered_params=[u'bucket', u'object'],
        path_params=[u'bucket', u'object'],
        query_params=[u'generation', u'ifGenerationMatch', u'ifGenerationNotMatch', u'ifMetagenerationMatch', u'ifMetagenerationNotMatch', u'predefinedAcl', u'projection', u'userProject'],
        relative_path=u'b/{bucket}/o/{object}',
        request_field=u'objectResource',
        request_type_name=u'StorageObjectsPatchRequest',
        response_type_name=u'Object',
        supports_download=False,
    )

    def Rewrite(self, request, global_params=None):
      r"""Rewrites a source object to a destination object. Optionally overrides metadata.

      Args:
        request: (StorageObjectsRewriteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (RewriteResponse) The response message.
      """
      config = self.GetMethodConfig('Rewrite')
      return self._RunMethod(
          config, request, global_params=global_params)

    Rewrite.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'storage.objects.rewrite',
        ordered_params=[u'sourceBucket', u'sourceObject', u'destinationBucket', u'destinationObject'],
        path_params=[u'destinationBucket', u'destinationObject', u'sourceBucket', u'sourceObject'],
        query_params=[u'destinationKmsKeyName', u'destinationPredefinedAcl', u'ifGenerationMatch', u'ifGenerationNotMatch', u'ifMetagenerationMatch', u'ifMetagenerationNotMatch', u'ifSourceGenerationMatch', u'ifSourceGenerationNotMatch', u'ifSourceMetagenerationMatch', u'ifSourceMetagenerationNotMatch', u'maxBytesRewrittenPerCall', u'projection', u'rewriteToken', u'sourceGeneration', u'userProject'],
        relative_path=u'b/{sourceBucket}/o/{sourceObject}/rewriteTo/b/{destinationBucket}/o/{destinationObject}',
        request_field=u'object',
        request_type_name=u'StorageObjectsRewriteRequest',
        response_type_name=u'RewriteResponse',
        supports_download=False,
    )

    def SetIamPolicy(self, request, global_params=None):
      r"""Updates an IAM policy for the specified object.

      Args:
        request: (StorageObjectsSetIamPolicyRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Policy) The response message.
      """
      config = self.GetMethodConfig('SetIamPolicy')
      return self._RunMethod(
          config, request, global_params=global_params)

    SetIamPolicy.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PUT',
        method_id=u'storage.objects.setIamPolicy',
        ordered_params=[u'bucket', u'object'],
        path_params=[u'bucket', u'object'],
        query_params=[u'generation', u'userProject'],
        relative_path=u'b/{bucket}/o/{object}/iam',
        request_field=u'policy',
        request_type_name=u'StorageObjectsSetIamPolicyRequest',
        response_type_name=u'Policy',
        supports_download=False,
    )

    def TestIamPermissions(self, request, global_params=None):
      r"""Tests a set of permissions on the given object to see which, if any, are held by the caller.

      Args:
        request: (StorageObjectsTestIamPermissionsRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (TestIamPermissionsResponse) The response message.
      """
      config = self.GetMethodConfig('TestIamPermissions')
      return self._RunMethod(
          config, request, global_params=global_params)

    TestIamPermissions.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.objects.testIamPermissions',
        ordered_params=[u'bucket', u'object', u'permissions'],
        path_params=[u'bucket', u'object'],
        query_params=[u'generation', u'permissions', u'userProject'],
        relative_path=u'b/{bucket}/o/{object}/iam/testPermissions',
        request_field='',
        request_type_name=u'StorageObjectsTestIamPermissionsRequest',
        response_type_name=u'TestIamPermissionsResponse',
        supports_download=False,
    )

    def Update(self, request, global_params=None):
      r"""Updates an object's metadata.

      Args:
        request: (StorageObjectsUpdateRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Object) The response message.
      """
      config = self.GetMethodConfig('Update')
      return self._RunMethod(
          config, request, global_params=global_params)

    Update.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PUT',
        method_id=u'storage.objects.update',
        ordered_params=[u'bucket', u'object'],
        path_params=[u'bucket', u'object'],
        query_params=[u'generation', u'ifGenerationMatch', u'ifGenerationNotMatch', u'ifMetagenerationMatch', u'ifMetagenerationNotMatch', u'predefinedAcl', u'projection', u'userProject'],
        relative_path=u'b/{bucket}/o/{object}',
        request_field=u'objectResource',
        request_type_name=u'StorageObjectsUpdateRequest',
        response_type_name=u'Object',
        supports_download=False,
    )

    def WatchAll(self, request, global_params=None):
      r"""Watch for changes on all objects in a bucket.

      Args:
        request: (StorageObjectsWatchAllRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (Channel) The response message.
      """
      config = self.GetMethodConfig('WatchAll')
      return self._RunMethod(
          config, request, global_params=global_params)

    WatchAll.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'storage.objects.watchAll',
        ordered_params=[u'bucket'],
        path_params=[u'bucket'],
        query_params=[u'delimiter', u'includeTrailingDelimiter', u'maxResults', u'pageToken', u'prefix', u'projection', u'userProject', u'versions'],
        relative_path=u'b/{bucket}/o/watch',
        request_field=u'channel',
        request_type_name=u'StorageObjectsWatchAllRequest',
        response_type_name=u'Channel',
        supports_download=False,
    )

  class ProjectsServiceAccountService(base_api.BaseApiService):
    """Service class for the projects_serviceAccount resource."""

    _NAME = u'projects_serviceAccount'

    def __init__(self, client):
      super(StorageV1.ProjectsServiceAccountService, self).__init__(client)
      self._upload_configs = {
          }

    def Get(self, request, global_params=None):
      r"""Get the email address of this project's Google Cloud Storage service account.

      Args:
        request: (StorageProjectsServiceAccountGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments
      Returns:
        (ServiceAccount) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(
          config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.projects.serviceAccount.get',
        ordered_params=[u'projectId'],
        path_params=[u'projectId'],
        query_params=[u'userProject'],
        relative_path=u'projects/{projectId}/serviceAccount',
        request_field='',
        request_type_name=u'StorageProjectsServiceAccountGetRequest',
        response_type_name=u'ServiceAccount',
        supports_download=False,
    )

  class ProjectsService(base_api.BaseApiService):
    """Service class for the projects resource."""

    _NAME = u'projects'

    def __init__(self, client):
      super(StorageV1.ProjectsService, self).__init__(client)
      self._upload_configs = {
          }

  class HmacKeysService(base_api.BaseApiService):
    """Service class for the project_hmacKeys resource."""

    _NAME = u'projects_hmacKeys'

    def Create(self, request, global_params=None):
      """Creates HMAC key for a service account.

      Args:
        request: (StorageProjectsHmacKeysCreateRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments

      Returns:
        (HmacKey) The response message.
      """
      config = self.GetMethodConfig('Create')
      return self._RunMethod(config, request, global_params=global_params)

    Create.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'POST',
        method_id=u'storage.projects.hmacKeys.create',
        ordered_params=[u'serviceAccountEmail', u'projectId'],
        path_params=[u'projectId'],
        query_params=[u'serviceAccountEmail'],
        relative_path=u'projects/{projectId}/hmacKeys',
        request_field='',
        request_type_name=u'StorageProjectsHmacKeysCreateRequest',
        response_type_name=u'HmacKey',
        supports_download=False,
    )

    def Delete(self, request, global_params=None):
      """Deletes an HMAC key.

      Args:
        request: (StorageProjectsHmacKeysDeleteRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments

      Returns:
        (HmacKeyDeleteResponse) The empty response message.
      """
      config = self.GetMethodConfig('Delete')
      return self._RunMethod(config, request, global_params=global_params)

    Delete.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'DELETE',
        method_id=u'storage.projects.hmacKeys.delete',
        ordered_params=[u'accessId', u'projectId'],
        path_params=[u'accessId', u'projectId'],
        query_params=[],
        relative_path=u'projects/{projectId}/hmacKeys/{accessId}',
        request_field='',
        request_type_name=u'StorageProjectsHmacKeysDeleteRequest',
        response_type_name=u'HmacKeysDeleteResponse',
        supports_download=False,
    )

    def Get(self, request, global_params=None):
      """Retrieves an HMAC key's metadata

      Args:
        request: (StorageProjectsHmacKeysGetRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments

      Returns:
        (HmacKeyMetadata) The response message.
      """
      config = self.GetMethodConfig('Get')
      return self._RunMethod(config, request, global_params=global_params)

    Get.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.projects.hmacKeys.get',
        ordered_params=[u'accessId', u'projectId'],
        path_params=[u'accessId', u'projectId'],
        relative_path=u'projects/{projectId}/hmacKeys/{accessId}',
        request_field='',
        request_type_name=u'StorageProjectsHmacKeysGetRequest',
        response_type_name=u'HmacKeyMetadata',
        supports_download=False,
    )

    def List(self, request, global_params=None):
      """Retrieves a list of HMAC keys matching the criteria.

      Args:
        request: (StorageProjectsHmacKeysListRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments

      Returns:
        (HmacKeyMetadataList) The response message.
      """
      config = self.GetMethodConfig('List')
      return self._RunMethod(config, request, global_params=global_params)

    List.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'GET',
        method_id=u'storage.projects.hmacKeys.get',
        ordered_params=[
            u'projectId',
            u'serviceAccountEmail',
            u'showDeletedKeys',
            u'maxResults',
            u'pageToken',
        ],
        path_params=[u'projectId'],
        query_params=[
            u'serviceAccountEmail', u'showDeletedKeys', u'maxResults',
            u'pageToken'
        ],
        relative_path=u'projects/{projectId}/hmacKeys',
        request_field='',
        request_type_name=u'StorageProjectsHmacKeysListRequest',
        response_type_name=u'HmacKeyMetadataList',
        supports_download=False,
    )

    def Update(self, request, global_params=None):
      """Updates the state of an HMAC key.

      Args:
        request: (StorageProjectsHmacKeysUpdateRequest) input message
        global_params: (StandardQueryParameters, default: None) global arguments

      Returns:
        (HmacKeyMetadata) The response message.
      """
      config = self.GetMethodConfig('Update')
      return self._RunMethod(config, request, global_params=global_params)

    Update.method_config = lambda: base_api.ApiMethodInfo(
        http_method=u'PUT',
        method_id=u'storage.projects.hmacKeys.update',
        ordered_params=[u'accessId', u'projectId'],
        path_params=[u'accessId', u'projectId'],
        query_params=[],
        relative_path=u'projects/{projectId}/hmacKeys/{accessId}',
        request_field='resource',
        request_type_name=u'StorageProjectsHmacKeysUpdateRequest',
        response_type_name=u'HmacKeyMetadata',
        supports_download=False,
    )

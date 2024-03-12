# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Client for interacting with Google Cloud Storage.

Implements CloudApi for the GCS JSON API. Example functions include listing
buckets, uploading objects, and setting lifecycle conditions.

TODO(b/160601969): Update class with remaining API methods for ls and cp.
    Note, this class has not been tested against the GCS API yet.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import errno
import json
import uuid

from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import list_pager
from apitools.base.py import transfer as apitools_transfer
from googlecloudsdk.api_lib.storage import cloud_api
from googlecloudsdk.api_lib.storage import errors as cloud_errors
from googlecloudsdk.api_lib.storage import gcs_iam_util
from googlecloudsdk.api_lib.storage import headers_util
from googlecloudsdk.api_lib.storage.gcs_json import download
from googlecloudsdk.api_lib.storage.gcs_json import error_util
from googlecloudsdk.api_lib.storage.gcs_json import metadata_util
from googlecloudsdk.api_lib.storage.gcs_json import patch_apitools_messages
from googlecloudsdk.api_lib.storage.gcs_json import upload
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.storage import encryption_util
from googlecloudsdk.command_lib.storage import errors as command_errors
from googlecloudsdk.command_lib.storage import gzip_util
from googlecloudsdk.command_lib.storage import posix_util
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import tracker_file_util
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage.resources import gcs_resource_reference
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks.cp import copy_util
from googlecloudsdk.command_lib.storage.tasks.cp import download_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import requests
from googlecloudsdk.core.credentials import transports
from googlecloudsdk.core.util import scaled_integer
import six
from six.moves import urllib


# TODO(b/171296237): Remove this when fixes are submitted in apitools.
patch_apitools_messages.patch()


# Call the progress callback every PROGRESS_CALLBACK_THRESHOLD bytes to
# improve performance.
KB = 1024  # Bytes.
MINIMUM_PROGRESS_CALLBACK_THRESHOLD = 512 * KB

_NOTIFICATION_PAYLOAD_FORMAT_KEY_TO_API_CONSTANT = {
    cloud_api.NotificationPayloadFormat.JSON: 'JSON_API_V1',
    cloud_api.NotificationPayloadFormat.NONE: 'NONE',
}


def _get_download_link(object_resource):
  """Generates link https://cloud.google.com/storage/docs/request-endpoints."""
  custom_endpoint = properties.VALUES.api_endpoint_overrides.storage.Get()
  if custom_endpoint:
    base = custom_endpoint.replace('storage/v1/', '')
  else:
    base = core_apis.UniversifyAddress('https://storage.googleapis.com/')
  url_string = '{}download/storage/{}/b/{}/o/{}?alt=media'.format(
      base,
      properties.VALUES.storage.json_api_version.Get(),
      object_resource.bucket,
      # We need to change the default `safe` so that `/` is escaped.
      # Copying GCS client library that treats `~` as safe without explanation.
      # https://github.com/googleapis/python-storage/commit/47f59ce9bf5bab6b5afbe26efde3449a6abfd90b
      urllib.parse.quote(object_resource.name.encode('utf-8'), safe=b'~'),
  )
  if object_resource.generation:
    return url_string + '&generation={}'.format(object_resource.generation)
  return url_string


def get_download_serialization_data(object_resource, progress):
  """Generates download serialization data for Apitools.

  Args:
    object_resource (resource_reference.ObjectResource): Used to get metadata.
    progress (int): Represents how much of download is complete.

  Returns:
    JSON string for use with Apitools.
  """
  if object_resource.metadata:
    download_link = object_resource.metadata.mediaLink
  else:
    download_link = _get_download_link(object_resource)
  serialization_dict = {
      'auto_transfer': False,  # Apitools JSON API feature not used.
      'progress': progress,
      'total_size': object_resource.size,
      'url': download_link,  # HTTP download link.
  }
  return json.dumps(serialization_dict)


class _StorageStreamResponseHandler(requests.ResponseHandler):
  """Handler for writing the streaming response to the download stream."""

  def __init__(self):
    """Initializes response handler for requests downloads."""
    super(_StorageStreamResponseHandler, self).__init__(use_stream=True)
    self._stream = None
    self._digesters = {}
    self._processed_bytes = 0,
    self._progress_callback = None
    self._size = None

    self._chunk_size = scaled_integer.ParseInteger(
        properties.VALUES.storage.download_chunk_size.Get())
    # If progress callbacks is called more frequently than every 512 KB, it
    # can degrate performance.
    self._progress_callback_threshold = max(MINIMUM_PROGRESS_CALLBACK_THRESHOLD,
                                            self._chunk_size)

  def update_destination_info(self,
                              stream,
                              size,
                              digesters=None,
                              download_strategy=None,
                              processed_bytes=0,
                              progress_callback=None):
    """Updates the stream handler with destination information.

    The download_http_client object is stored on the gcs_api object. This allows
    resusing the same http_client when the gcs_api is cached using
    threading.local, which improves performance.
    Since this same object gets used for multiple downloads, we need to update
    the stream handler with the current active download's destination.

    Args:
      stream (stream): Local stream to write downloaded data to.
      size (int): The amount of data in bytes to be downloaded.
      digesters (dict<HashAlgorithm, hashlib object> | None): For updating hash
        digests of downloaded objects on the fly.
      download_strategy (DownloadStrategy): Indicates if user wants to retry
        download on failures.
      processed_bytes (int): For keeping track of how much progress has been
        made.
      progress_callback (func<int>): Accepts processed_bytes and submits
        progress info for aggregation.
    """
    self._stream = stream
    self._size = size
    self._digesters = digesters if digesters is not None else {}
    # ONE_SHOT strategy may need to break out of Apitools's automatic retries.
    self._download_strategy = download_strategy
    self._processed_bytes = processed_bytes
    self._progress_callback = progress_callback
    self._start_byte = self._processed_bytes

  def handle(self, source_stream):
    if self._stream is None:
      raise command_errors.Error('Stream was not found.')

    # For example, can happen if piping to a command that only reads one line.
    destination_pipe_is_broken = False
    # Start reading the raw stream.
    bytes_since_last_progress_callback = 0
    while True:
      data = source_stream.read(self._chunk_size)
      if data:
        try:
          self._stream.write(data)
        except OSError as e:
          if (e.errno == errno.EPIPE and
              self._download_strategy is cloud_api.DownloadStrategy.ONE_SHOT):
            log.info('Writing to download stream raised broken pipe error.')
            destination_pipe_is_broken = True
            break
          raise

        for hash_object in self._digesters.values():
          hash_object.update(data)

        self._processed_bytes += len(data)
        bytes_since_last_progress_callback += len(data)
        if (self._progress_callback and bytes_since_last_progress_callback >=
            self._progress_callback_threshold):
          self._progress_callback(self._processed_bytes)
          bytes_since_last_progress_callback = (
              bytes_since_last_progress_callback -
              self._progress_callback_threshold)
      else:
        if self._progress_callback and bytes_since_last_progress_callback:
          # Make a last progress callback call to update the final size.
          self._progress_callback(self._processed_bytes)
        break

    total_downloaded_data = self._processed_bytes - self._start_byte
    if self._size != total_downloaded_data and not destination_pipe_is_broken:
      # The input stream terminated before the entire content was read,
      # possibly due to a network condition.
      message = (
          'Download not completed. Target size={}, downloaded data={}'.format(
              self._size, total_downloaded_data))
      log.debug(message)
      raise cloud_errors.RetryableApiError(message)


def _get_encryption_headers(key):
  if (key and key != user_request_args_factory.CLEAR and
      key.type == encryption_util.KeyType.CSEK):
    return {
        'x-goog-encryption-algorithm': 'AES256',
        'x-goog-encryption-key': key.key,
        'x-goog-encryption-key-sha256': key.sha256,
    }
  return {}


def _update_api_version_for_uploads_if_needed(client):
  api_version = properties.VALUES.storage.json_api_version.Get()
  insert_config = client.objects._upload_configs.get('Insert')  # pylint: disable=protected-access
  if insert_config is None:
    return

  insert_config.simple_path = insert_config.simple_path.replace(
      'v1', api_version)
  insert_config.resumable_path = insert_config.resumable_path.replace(
      'v1', api_version)


class JsonClient(cloud_api.CloudApi):
  """Client for Google Cloud Storage API."""

  capabilities = {
      cloud_api.Capability.COMPOSE_OBJECTS,
      cloud_api.Capability.DAISY_CHAIN_SEEKABLE_UPLOAD_STREAM,
      cloud_api.Capability.ENCRYPTION,
      cloud_api.Capability.MANAGED_FOLDERS,
      cloud_api.Capability.RESUMABLE_UPLOAD,
      cloud_api.Capability.SLICED_DOWNLOAD,
  }

  # The API limits the number of objects that can be composed in a single call.
  # https://cloud.google.com/storage/docs/json_api/v1/objects/compose
  MAX_OBJECTS_PER_COMPOSE_CALL = 32

  def __init__(self):
    super(JsonClient, self).__init__()
    self.client = core_apis.GetClientInstance('storage', 'v1')

    _update_api_version_for_uploads_if_needed(self.client)

    self.client.overwrite_transfer_urls_with_client_base = True
    self.client.additional_http_headers = (
        headers_util.get_additional_header_dict())

    self.messages = core_apis.GetMessagesModule('storage', 'v1')
    self._stream_response_handler = _StorageStreamResponseHandler()
    self._download_http_client = None
    self._upload_http_client = None

  @contextlib.contextmanager
  def _apitools_request_headers_context(self, headers):
    if headers:
      old_headers = self.client.additional_http_headers.copy()
      self.client.additional_http_headers.update(headers)
    yield
    if headers:
      self.client.additional_http_headers = old_headers

  def _encryption_headers_context(self, key):
    return self._apitools_request_headers_context(_get_encryption_headers(key))

  def _encryption_headers_for_rewrite_call_context(self, request_config):
    additional_headers = {}
    encryption_key = getattr(request_config.resource_args, 'encryption_key',
                             None)
    additional_headers.update(_get_encryption_headers(encryption_key))

    decryption_key = getattr(request_config.resource_args, 'decryption_key',
                             None)
    if decryption_key and decryption_key.type == encryption_util.KeyType.CSEK:
      additional_headers.update({
          'x-goog-copy-source-encryption-algorithm': 'AES256',
          'x-goog-copy-source-encryption-key': decryption_key.key,
          'x-goog-copy-source-encryption-key-sha256': decryption_key.sha256,
      })
    return self._apitools_request_headers_context(additional_headers)

  def _get_projection(self, fields_scope, message_class):
    """Generate query projection from fields_scope.

    Args:
      fields_scope (FieldsScope): Used to determine projection to return.
      message_class (object): Apitools message object that contains a projection
        enum.

    Returns:
      projection (ProjectionValueValuesEnum): Determines if ACL properties
          should be returned.

    Raises:
      Error: The fields_scope isn't recognized.
    """
    try:
      if fields_scope not in cloud_api.FieldsScope:
        raise command_errors.Error('Invalid fields_scope.')
    except TypeError:
      raise command_errors.Error('Invalid fields_scope.')
    projection_enum = message_class.ProjectionValueValuesEnum

    if fields_scope == cloud_api.FieldsScope.FULL:
      return projection_enum.full
    return projection_enum.noAcl

  def _get_source_path(self, source_resource):
    """Get source path from source_resource.

    Args:
      source_resource (FileObjectResource|None): Contains the
        source StorageUrl. Can be None if source is pure stream.

    Returns:
      (str|None) Source path.
    """
    if source_resource:
      return source_resource.storage_url.versionless_url_string

    return None

  @error_util.catch_http_error_raise_gcs_api_error()
  def create_anywhere_cache(self, bucket_name, zone, admission_policy, ttl):
    """See super class."""
    request = self.messages.AnywhereCache(
        bucket=bucket_name,
        zone=zone,
        admissionPolicy=admission_policy,
        ttl=ttl
    )
    with self._apitools_request_headers_context(
        {'x-goog-gcs-idempotency-token': uuid.uuid4().hex}
    ):
      operation = self.client.anywhereCaches.Insert(request)
    return operation

  @error_util.catch_http_error_raise_gcs_api_error()
  def disable_anywhere_cache(
      self,
      bucket_name,
      anywhere_cache_id,
  ):
    """See super class."""
    request = self.messages.StorageAnywhereCachesDisableRequest(
        bucket=bucket_name,
        anywhereCacheId=anywhere_cache_id,
    )
    self.client.anywhereCaches.Disable(request)

  @error_util.catch_http_error_raise_gcs_api_error()
  def get_anywhere_cache(
      self,
      bucket_name,
      anywhere_cache_id,
  ):
    """See super class."""
    request = self.messages.StorageAnywhereCachesGetRequest(
        bucket=bucket_name,
        anywhereCacheId=anywhere_cache_id,
    )
    return metadata_util.get_anywhere_cache_resource_from_metadata(
        self.client.anywhereCaches.Get(request)
    )

  @error_util.catch_http_error_raise_gcs_api_error()
  def list_anywhere_caches(
      self,
      bucket_name,
  ):
    """See super class."""
    request = self.messages.StorageAnywhereCachesListRequest(
        bucket=bucket_name,
        pageSize=cloud_api.NUM_ITEMS_PER_LIST_PAGE,
        pageToken=None,
    )

    anywhere_cache_iterator = list_pager.YieldFromList(
        self.client.anywhereCaches,
        request,
        batch_size=cloud_api.NUM_ITEMS_PER_LIST_PAGE,
        batch_size_attribute='pageSize'
    )
    try:
      for anywhere_cache in anywhere_cache_iterator:
        yield metadata_util.get_anywhere_cache_resource_from_metadata(
            anywhere_cache
        )
    except apitools_exceptions.HttpError as e:
      core_exceptions.reraise(
          cloud_errors.translate_error(e, error_util.ERROR_TRANSLATION)
      )

  @error_util.catch_http_error_raise_gcs_api_error()
  def patch_anywhere_cache(
      self,
      bucket_name,
      anywhere_cache_id,
      admission_policy,
      ttl,
  ):
    """See super class."""
    request = self.messages.AnywhereCache(
        bucket=bucket_name,
        anywhereCacheId=anywhere_cache_id,
        admissionPolicy=admission_policy,
        ttl=ttl
    )
    with self._apitools_request_headers_context(
        {'x-goog-gcs-idempotency-token': uuid.uuid4().hex}
    ):
      operation = self.client.anywhereCaches.Update(request)
    return operation

  @error_util.catch_http_error_raise_gcs_api_error()
  def pause_anywhere_cache(self, bucket_name, anywhere_cache_id):
    """See super class."""
    request = self.messages.StorageAnywhereCachesPauseRequest(
        bucket=bucket_name,
        anywhereCacheId=anywhere_cache_id,
    )
    self.client.anywhereCaches.Pause(request)

  @error_util.catch_http_error_raise_gcs_api_error()
  def resume_anywhere_cache(self, bucket_name, anywhere_cache_id):
    """See super class."""
    request = self.messages.StorageAnywhereCachesResumeRequest(
        bucket=bucket_name,
        anywhereCacheId=anywhere_cache_id,
    )
    self.client.anywhereCaches.Resume(request)

  @error_util.catch_http_error_raise_gcs_api_error()
  def create_bucket(self,
                    bucket_resource,
                    request_config,
                    fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    projection = self._get_projection(fields_scope,
                                      self.messages.StorageBucketsInsertRequest)

    bucket_metadata = self.messages.Bucket(
        name=bucket_resource.storage_url.bucket_name)
    metadata_util.update_bucket_metadata_from_request_config(
        bucket_metadata, request_config)

    resource_args = getattr(request_config, 'resource_args', None)
    request = self.messages.StorageBucketsInsertRequest(
        bucket=bucket_metadata,
        enableObjectRetention=getattr(
            resource_args, 'enable_per_object_retention', None,
        ),
        project=properties.VALUES.core.project.GetOrFail(),
        projection=projection)

    created_bucket_metadata = self.client.buckets.Insert(request)
    return metadata_util.get_bucket_resource_from_metadata(
        created_bucket_metadata)

  @error_util.catch_http_error_raise_gcs_api_error()
  def delete_bucket(self, bucket_name, request_config):
    """See super class."""
    request = self.messages.StorageBucketsDeleteRequest(
        bucket=bucket_name,
        ifMetagenerationMatch=request_config.precondition_metageneration_match)
    # Success returns an empty body.
    # https://cloud.google.com/storage/docs/json_api/v1/buckets/delete
    self.client.buckets.Delete(request)

  @error_util.catch_http_error_raise_gcs_api_error()
  def get_bucket(self, bucket_name, fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    projection = self._get_projection(fields_scope,
                                      self.messages.StorageBucketsGetRequest)
    request = self.messages.StorageBucketsGetRequest(
        bucket=bucket_name,
        projection=projection)

    metadata = self.client.buckets.Get(request)
    return metadata_util.get_bucket_resource_from_metadata(metadata)

  @error_util.catch_http_error_raise_gcs_api_error()
  def get_bucket_iam_policy(self, bucket_name):
    """See super class."""
    global_params = self.messages.StandardQueryParameters(
        fields='bindings,etag')
    return self.client.buckets.GetIamPolicy(
        self.messages.StorageBucketsGetIamPolicyRequest(
            bucket=bucket_name,
            optionsRequestedPolicyVersion=gcs_iam_util.IAM_POLICY_VERSION),
        global_params=global_params)

  def list_buckets(self, fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    projection = self._get_projection(fields_scope,
                                      self.messages.StorageBucketsListRequest)
    request = self.messages.StorageBucketsListRequest(
        project=properties.VALUES.core.project.GetOrFail(),
        projection=projection)

    global_params = None
    if fields_scope == cloud_api.FieldsScope.SHORT:
      global_params = self.messages.StandardQueryParameters(
          fields='items/name,nextPageToken')
    # TODO(b/160238394) Decrypt metadata fields if necessary.
    bucket_iter = list_pager.YieldFromList(
        self.client.buckets,
        request,
        batch_size=cloud_api.NUM_ITEMS_PER_LIST_PAGE,
        global_params=global_params)
    try:
      for bucket in bucket_iter:
        yield metadata_util.get_bucket_resource_from_metadata(bucket)
    except apitools_exceptions.HttpError as e:
      core_exceptions.reraise(
          cloud_errors.translate_error(e, error_util.ERROR_TRANSLATION))

  @error_util.catch_http_error_raise_gcs_api_error()
  def lock_bucket_retention_policy(self, bucket_resource, request_config):
    metageneration_precondition = (
        request_config.precondition_metageneration_match or
        bucket_resource.metageneration)
    request = self.messages.StorageBucketsLockRetentionPolicyRequest(
        bucket=bucket_resource.storage_url.bucket_name,
        ifMetagenerationMatch=metageneration_precondition)
    return metadata_util.get_bucket_resource_from_metadata(
        self.client.buckets.LockRetentionPolicy(request))

  @error_util.catch_http_error_raise_gcs_api_error()
  def patch_bucket(self,
                   bucket_resource,
                   request_config,
                   fields_scope=cloud_api.FieldsScope.NO_ACL):
    """See super class."""
    projection = self._get_projection(fields_scope,
                                      self.messages.StorageBucketsPatchRequest)
    metadata = getattr(
        bucket_resource, 'metadata',
        None) or (metadata_util.get_apitools_metadata_from_url(
            bucket_resource.storage_url))
    metadata_util.update_bucket_metadata_from_request_config(
        metadata, request_config)

    cleared_fields = metadata_util.get_cleared_bucket_fields(request_config)
    if (metadata.defaultObjectAcl and metadata.defaultObjectAcl[0]
        == metadata_util.PRIVATE_DEFAULT_OBJECT_ACL):
      cleared_fields.append('defaultObjectAcl')
      metadata.defaultObjectAcl = []

    # Must null out existing ACLs to apply new ones.
    if request_config.predefined_acl_string:
      cleared_fields.append('acl')
      predefined_acl = getattr(
          self.messages.StorageBucketsPatchRequest.PredefinedAclValueValuesEnum,
          request_config.predefined_acl_string)
    else:
      predefined_acl = None

    if request_config.predefined_default_object_acl_string:
      cleared_fields.append('defaultObjectAcl')
      predefined_default_object_acl = getattr(
          self.messages.StorageBucketsPatchRequest
          .PredefinedDefaultObjectAclValueValuesEnum,
          request_config.predefined_default_object_acl_string)
    else:
      predefined_default_object_acl = None

    apitools_request = self.messages.StorageBucketsPatchRequest(
        bucket=bucket_resource.storage_url.bucket_name,
        bucketResource=metadata,
        projection=projection,
        ifMetagenerationMatch=request_config.precondition_metageneration_match,
        predefinedAcl=predefined_acl,
        predefinedDefaultObjectAcl=predefined_default_object_acl)

    with self.client.IncludeFields(cleared_fields):
      # IncludeFields nulls out field in Apitools (does not just edit them).
      return metadata_util.get_bucket_resource_from_metadata(
          self.client.buckets.Patch(apitools_request))

  @error_util.catch_http_error_raise_gcs_api_error()
  def set_bucket_iam_policy(self, bucket_name, policy):
    """See super class."""
    return self.client.buckets.SetIamPolicy(
        self.messages.StorageBucketsSetIamPolicyRequest(
            bucket=bucket_name, policy=policy))

  @error_util.catch_http_error_raise_gcs_api_error()
  def create_hmac_key(self, service_account_email):
    """See super class."""
    request = self.messages.StorageProjectsHmacKeysCreateRequest(
        projectId=properties.VALUES.core.project.GetOrFail(),
        serviceAccountEmail=service_account_email)
    return gcs_resource_reference.GcsHmacKeyResource(
        self.client.projects_hmacKeys.Create(request))

  @error_util.catch_http_error_raise_gcs_api_error()
  def delete_hmac_key(self, access_id):
    """See super class."""
    request = self.messages.StorageProjectsHmacKeysDeleteRequest(
        projectId=properties.VALUES.core.project.GetOrFail(),
        accessId=access_id)
    self.client.projects_hmacKeys.Delete(request)

  @error_util.catch_http_error_raise_gcs_api_error()
  def get_hmac_key(self, access_id):
    """See super class."""

    request = self.messages.StorageProjectsHmacKeysGetRequest(
        projectId=properties.VALUES.core.project.GetOrFail(),
        accessId=access_id)
    response = self.client.projects_hmacKeys.Get(request)
    return gcs_resource_reference.GcsHmacKeyResource(response)

  def list_hmac_keys(self, service_account_email=None, show_deleted_keys=False,
                     fields_scope=cloud_api.FieldsScope.SHORT):
    """See super class."""

    if fields_scope == cloud_api.FieldsScope.NO_ACL:
      raise command_errors.Error(
          'HMAC keys do not have ACLs.')
    if fields_scope == cloud_api.FieldsScope.FULL:
      global_params = None
    else:
      global_params = self.messages.StandardQueryParameters(
          fields='items(accessId,state,serviceAccountEmail),nextPageToken')

    request = self.messages.StorageProjectsHmacKeysListRequest(
        serviceAccountEmail=service_account_email,
        showDeletedKeys=show_deleted_keys,
        projectId=properties.VALUES.core.project.GetOrFail(),
    )

    hmac_iter = list_pager.YieldFromList(
        global_params=global_params,
        service=self.client.projects_hmacKeys,
        request=request,
        batch_size=cloud_api.NUM_ITEMS_PER_LIST_PAGE,
    )

    try:
      for hmac_key in hmac_iter:
        yield gcs_resource_reference.GcsHmacKeyResource(hmac_key)
    except apitools_exceptions.HttpError as e:
      core_exceptions.reraise(
          cloud_errors.translate_error(e, error_util.ERROR_TRANSLATION))

  @error_util.catch_http_error_raise_gcs_api_error()
  def patch_hmac_key(self, access_id, etag, state):
    """See super class."""
    updated_metadata = self.messages.HmacKeyMetadata(state=state.value)
    if etag:
      updated_metadata.etag = etag
    request = self.messages.StorageProjectsHmacKeysUpdateRequest(
        projectId=properties.VALUES.core.project.GetOrFail(),
        hmacKeyMetadata=updated_metadata,
        accessId=access_id)
    return gcs_resource_reference.GcsHmacKeyResource(
        self.client.projects_hmacKeys.Update(request))

  @error_util.catch_http_error_raise_gcs_api_error()
  def compose_objects(
      self,
      source_resources,
      destination_resource,
      request_config,
      original_source_resource=None,
      posix_to_set=None,
  ):
    """See CloudApi class for function doc strings."""

    if not source_resources:
      raise cloud_errors.GcsApiError(
          'Compose requires at least one component object.')

    if len(source_resources) > self.MAX_OBJECTS_PER_COMPOSE_CALL:
      raise cloud_errors.GcsApiError(
          'Compose was called with {} objects. The limit is {}.'.format(
              len(source_resources), self.MAX_OBJECTS_PER_COMPOSE_CALL))

    source_messages = []
    for source in source_resources:
      source_message = self.messages.ComposeRequest.SourceObjectsValueListEntry(
          name=source.storage_url.object_name)
      if source.storage_url.generation is not None:
        generation = int(source.storage_url.generation)
        source_message.generation = generation
      source_messages.append(source_message)

    base_destination_metadata = metadata_util.get_apitools_metadata_from_url(
        destination_resource.storage_url)
    if getattr(source_resources[0], 'metadata', None):
      final_destination_metadata = metadata_util.copy_object_metadata(
          source_resources[0].metadata, base_destination_metadata,
          request_config)
    else:
      final_destination_metadata = base_destination_metadata
    metadata_util.update_object_metadata_from_request_config(
        final_destination_metadata,
        request_config,
        attributes_resource=original_source_resource,
        posix_to_set=posix_to_set,
    )

    compose_request_payload = self.messages.ComposeRequest(
        sourceObjects=source_messages, destination=final_destination_metadata)

    compose_request = self.messages.StorageObjectsComposeRequest(
        composeRequest=compose_request_payload,
        destinationBucket=destination_resource.storage_url.bucket_name,
        destinationObject=destination_resource.storage_url.object_name,
        ifGenerationMatch=request_config.precondition_generation_match,
        ifMetagenerationMatch=request_config.precondition_metageneration_match)

    if request_config.resource_args:
      encryption_key = request_config.resource_args.encryption_key
      if (encryption_key and
          encryption_key != user_request_args_factory.CLEAR and
          encryption_key.type == encryption_util.KeyType.CMEK):
        compose_request.kmsKeyName = encryption_key.key

    if request_config.predefined_acl_string is not None:
      compose_request.destinationPredefinedAcl = getattr(
          self.messages.StorageObjectsComposeRequest
          .DestinationPredefinedAclValueValuesEnum,
          request_config.predefined_acl_string)

    encryption_key = getattr(request_config.resource_args, 'encryption_key',
                             None)
    with self._encryption_headers_context(encryption_key):
      return metadata_util.get_object_resource_from_metadata(
          self.client.objects.Compose(compose_request))

  @error_util.catch_http_error_raise_gcs_api_error()
  def copy_object(
      self,
      source_resource,
      destination_resource,
      request_config,
      posix_to_set=None,
      progress_callback=None,
      should_deep_copy_metadata=False,
  ):
    """See super class."""
    destination_metadata = getattr(destination_resource, 'metadata', None)
    if not destination_metadata:
      destination_metadata = metadata_util.get_apitools_metadata_from_url(
          destination_resource.storage_url)
    if source_resource.metadata:
      destination_metadata = metadata_util.copy_object_metadata(
          source_resource.metadata,
          destination_metadata,
          request_config,
          should_deep_copy=should_deep_copy_metadata)
    metadata_util.update_object_metadata_from_request_config(
        destination_metadata, request_config, posix_to_set=posix_to_set
    )

    if request_config.predefined_acl_string:
      predefined_acl = getattr(
          self.messages.StorageObjectsRewriteRequest
          .DestinationPredefinedAclValueValuesEnum,
          request_config.predefined_acl_string)
    else:
      predefined_acl = None

    if source_resource.generation is None:
      source_generation = None
    else:
      source_generation = int(source_resource.generation)

    tracker_file_path = tracker_file_util.get_tracker_file_path(
        destination_resource.storage_url,
        tracker_file_util.TrackerFileType.REWRITE,
        source_url=source_resource.storage_url)
    rewrite_parameters_hash = (
        tracker_file_util.hash_gcs_rewrite_parameters_for_tracker_file(
            source_resource,
            destination_resource,
            destination_metadata,
            request_config=request_config,
        )
    )

    resume_rewrite_token = (
        tracker_file_util.get_rewrite_token_from_tracker_file(
            tracker_file_path, rewrite_parameters_hash))
    if resume_rewrite_token:
      log.debug('Found rewrite token. Resuming copy.')
    else:
      log.debug('No rewrite token found. Starting copy from scratch.')

    max_bytes_per_call = scaled_integer.ParseInteger(
        properties.VALUES.storage.copy_chunk_size.Get())
    with self._encryption_headers_for_rewrite_call_context(request_config):
      while True:
        request = self.messages.StorageObjectsRewriteRequest(
            sourceBucket=source_resource.storage_url.bucket_name,
            sourceObject=source_resource.storage_url.object_name,
            destinationBucket=destination_resource.storage_url.bucket_name,
            destinationObject=destination_resource.storage_url.object_name,
            object=destination_metadata,
            sourceGeneration=source_generation,
            ifGenerationMatch=copy_util.get_generation_match_value(
                request_config),
            ifMetagenerationMatch=request_config
            .precondition_metageneration_match,
            destinationPredefinedAcl=predefined_acl,
            rewriteToken=resume_rewrite_token,
            maxBytesRewrittenPerCall=max_bytes_per_call)

        encryption_key = getattr(
            request_config.resource_args, 'encryption_key', None)
        if (encryption_key and
            encryption_key != user_request_args_factory.CLEAR and
            encryption_key.type == encryption_util.KeyType.CMEK):
          # This key is also provided in destination_metadata.kmsKeyName by
          # update_object_metadata_from_request_config. This has no effect on
          # the copy object request, which references the field below, and is a
          # side-effect of logic required for uploads and compose operations.
          request.destinationKmsKeyName = encryption_key.key

        rewrite_response = self.client.objects.Rewrite(request)
        processed_bytes = rewrite_response.totalBytesRewritten
        if progress_callback:
          progress_callback(processed_bytes)

        if rewrite_response.done:
          break

        if not resume_rewrite_token:
          resume_rewrite_token = rewrite_response.rewriteToken
          if source_resource.size >= scaled_integer.ParseInteger(
              properties.VALUES.storage.resumable_threshold.Get()):
            tracker_file_util.write_rewrite_tracker_file(
                tracker_file_path, rewrite_parameters_hash,
                rewrite_response.rewriteToken)

    tracker_file_util.delete_tracker_file(tracker_file_path)
    return metadata_util.get_object_resource_from_metadata(
        rewrite_response.resource)

  @error_util.catch_http_error_raise_gcs_api_error()
  def delete_object(self, object_url, request_config):
    """See super class."""
    # S3 requires a string, but GCS uses an int for generation.
    if object_url.generation is not None:
      generation = int(object_url.generation)
    else:
      generation = None

    request = self.messages.StorageObjectsDeleteRequest(
        bucket=object_url.bucket_name,
        object=object_url.object_name,
        generation=generation,
        ifGenerationMatch=request_config.precondition_generation_match,
        ifMetagenerationMatch=request_config.precondition_metageneration_match)
    # Success returns an empty body.
    # https://cloud.google.com/storage/docs/json_api/v1/objects/delete
    self.client.objects.Delete(request)

  @error_util.catch_http_error_raise_gcs_api_error()
  def download_object(self,
                      cloud_resource,
                      download_stream,
                      request_config,
                      digesters=None,
                      do_not_decompress=False,
                      download_strategy=cloud_api.DownloadStrategy.RESUMABLE,
                      progress_callback=None,
                      start_byte=0,
                      end_byte=None):
    """See super class."""
    if download_util.return_and_report_if_nothing_to_download(
        cloud_resource, progress_callback
    ):
      return None

    serialization_data = get_download_serialization_data(
        cloud_resource, start_byte)
    apitools_download = apitools_transfer.Download.FromData(
        download_stream,
        serialization_data,
        num_retries=properties.VALUES.storage.max_retries.GetInt(),
        client=self.client)

    if end_byte is None:
      calculated_end_byte = cloud_resource.size - 1
    else:
      calculated_end_byte = end_byte

    self._stream_response_handler.update_destination_info(
        stream=download_stream,
        size=calculated_end_byte - start_byte + 1,
        digesters=digesters,
        download_strategy=download_strategy,
        processed_bytes=start_byte,
        progress_callback=progress_callback,
    )

    if self._download_http_client is None:
      self._download_http_client = transports.GetApitoolsTransport(
          response_encoding=None,
          response_handler=self._stream_response_handler)
    apitools_download.bytes_http = self._download_http_client

    additional_headers = self.client.additional_http_headers
    if do_not_decompress:
      # TODO(b/161453101): Optimize handling of gzip-encoded downloads.
      additional_headers['accept-encoding'] = 'gzip'

    decryption_key = getattr(request_config.resource_args, 'decryption_key',
                             None)
    additional_headers.update(_get_encryption_headers(decryption_key))

    if download_strategy == cloud_api.DownloadStrategy.ONE_SHOT:
      server_reported_encoding = download.launch(
          apitools_download,
          start_byte=start_byte,
          end_byte=end_byte,
          additional_headers=additional_headers)
    else:
      server_reported_encoding = download.launch_retriable(
          download_stream,
          apitools_download,
          start_byte=start_byte,
          end_byte=end_byte,
          additional_headers=additional_headers)

    return server_reported_encoding

  @error_util.catch_http_error_raise_gcs_api_error()
  def get_object_iam_policy(self, bucket_name, object_name, generation=None):
    """See super class."""
    if generation:
      generation = int(generation)

    global_params = self.messages.StandardQueryParameters(
        fields='bindings,etag')
    return self.client.objects.GetIamPolicy(
        self.messages.StorageObjectsGetIamPolicyRequest(
            bucket=bucket_name, object=object_name, generation=generation),
        global_params=global_params)

  @error_util.catch_http_error_raise_gcs_api_error()
  def get_object_metadata(
      self,
      bucket_name,
      object_name,
      request_config=None,
      generation=None,
      fields_scope=cloud_api.FieldsScope.NO_ACL,
      soft_deleted=False,
  ):
    """See super class."""
    # S3 requires a string, but GCS uses an int for generation.
    if generation:
      generation = int(generation)

    projection = self._get_projection(fields_scope,
                                      self.messages.StorageObjectsGetRequest)
    global_params = None
    if fields_scope == cloud_api.FieldsScope.SHORT:
      global_params = self.messages.StandardQueryParameters(
          fields='bucket,name,size,generation'
      )

    decryption_key = getattr(
        getattr(request_config, 'resource_args', None), 'decryption_key', None)
    with self._encryption_headers_context(decryption_key):
      object_metadata = self.client.objects.Get(
          self.messages.StorageObjectsGetRequest(
              bucket=bucket_name,
              object=object_name,
              generation=generation,
              projection=projection,
              # Avoid needlessly appending "&softDeleted=False" to URL.
              softDeleted=True if soft_deleted else None,
          ),
          global_params=global_params,
      )
    return metadata_util.get_object_resource_from_metadata(object_metadata)

  def list_objects(
      self,
      bucket_name,
      prefix=None,
      delimiter=None,
      fields_scope=cloud_api.FieldsScope.NO_ACL,
      halt_on_empty_response=True,
      include_folders_as_prefixes=None,
      next_page_token=None,
      object_state=cloud_api.ObjectState.LIVE,
  ):
    """See super class."""
    projection = self._get_projection(fields_scope,
                                      self.messages.StorageObjectsListRequest)
    global_params = None
    if fields_scope == cloud_api.FieldsScope.SHORT:
      global_params = self.messages.StandardQueryParameters(
          fields='prefixes,items/name,items/size,items/generation,nextPageToken'
      )
    elif fields_scope == cloud_api.FieldsScope.RSYNC:
      global_params = self.messages.StandardQueryParameters(
          fields=(
              'prefixes,items/name,items/etag,items/size,items/generation,'
              'items/storageClass,items/timeCreated,items/metadata/{},'
              'items/metadata/{},items/metadata/{},items/metadata/{},'
              'items/metadata/{},items/crc32c,items/md5Hash,nextPageToken'
          ).format(
              posix_util.ATIME_METADATA_KEY,
              posix_util.GID_METADATA_KEY,
              posix_util.MODE_METADATA_KEY,
              posix_util.MTIME_METADATA_KEY,
              posix_util.UID_METADATA_KEY,
          )
      )

    list_result = None
    live_and_noncurrent = (
        True
        if object_state is cloud_api.ObjectState.LIVE_AND_NONCURRENT
        else None
    )
    soft_deleted = (
        True if object_state is cloud_api.ObjectState.SOFT_DELETED else None
    )
    while True:
      apitools_request = self.messages.StorageObjectsListRequest(
          bucket=bucket_name,
          prefix=prefix,
          delimiter=delimiter,
          versions=live_and_noncurrent,
          projection=projection,
          pageToken=next_page_token,
          maxResults=cloud_api.NUM_ITEMS_PER_LIST_PAGE,
          includeFoldersAsPrefixes=include_folders_as_prefixes,
          # Avoid needlessly appending "&softDeleted=False" to URL.
          softDeleted=soft_deleted,
      )

      try:
        list_result = self.client.objects.List(
            apitools_request, global_params=global_params
        )
      except apitools_exceptions.HttpError as e:
        core_exceptions.reraise(
            cloud_errors.translate_error(e, error_util.ERROR_TRANSLATION))

      next_page_token = list_result.nextPageToken
      if (
          not (list_result.items or list_result.prefixes)
          and next_page_token
          and halt_on_empty_response
      ):
        log.warning(
            (
                'Received empty list response. However, a next page token is'
                ' available. Rerun with `--exhaustive --next-page-token={}` to'
                ' pick up where you left off and exhaustively search all'
                ' objects. Making numerous LIST API calls can be expensive, and'
                ' additional objects are not guaranteed exist.'
            ).format(next_page_token)
        )
        break

      # Yield objects.
      # TODO(b/160238394) Decrypt metadata fields if necessary.
      for object_metadata in list_result.items:
        object_metadata.bucket = bucket_name
        yield metadata_util.get_object_resource_from_metadata(
            object_metadata)

      # Yield prefixes.
      for prefix_string in list_result.prefixes:
        yield resource_reference.PrefixResource(
            storage_url.CloudUrl(
                scheme=storage_url.ProviderPrefix.GCS,
                bucket_name=bucket_name,
                object_name=prefix_string),
            prefix=prefix_string)

      if not next_page_token:
        break

  @error_util.catch_http_error_raise_gcs_api_error()
  def patch_object_metadata(
      self,
      bucket_name,
      object_name,
      object_resource,
      request_config,
      fields_scope=cloud_api.FieldsScope.NO_ACL,
      generation=None,
      posix_to_set=None,
  ):
    """See super class."""
    # S3 requires a string, but GCS uses an int for generation.
    if generation:
      generation = int(generation)

    predefined_acl = None
    if request_config.predefined_acl_string:
      predefined_acl = getattr(
          self.messages.StorageObjectsPatchRequest.PredefinedAclValueValuesEnum,
          request_config.predefined_acl_string,
      )

    projection = self._get_projection(
        fields_scope, self.messages.StorageObjectsPatchRequest
    )

    object_metadata = object_resource.metadata or (
        metadata_util.get_apitools_metadata_from_url(
            object_resource.storage_url
        )
    )

    metadata_util.update_object_metadata_from_request_config(
        object_metadata, request_config, posix_to_set=posix_to_set
    )
    request = self.messages.StorageObjectsPatchRequest(
        bucket=bucket_name,
        object=object_name,
        objectResource=object_metadata,
        generation=generation,
        ifGenerationMatch=request_config.precondition_generation_match,
        ifMetagenerationMatch=request_config.precondition_metageneration_match,
        overrideUnlockedRetention=request_config.override_unlocked_retention,
        predefinedAcl=predefined_acl,
        projection=projection,
    )

    with self.client.IncludeFields(
        metadata_util.get_cleared_object_fields(request_config)
    ):
      updated_metadata = self.client.objects.Patch(request)
    return metadata_util.get_object_resource_from_metadata(updated_metadata)

  @error_util.catch_http_error_raise_gcs_api_error()
  def set_object_iam_policy(self,
                            bucket_name,
                            object_name,
                            policy,
                            generation=None):
    """See super class."""
    if generation:
      generation = int(generation)
    return self.client.objects.SetIamPolicy(
        self.messages.StorageObjectsSetIamPolicyRequest(
            bucket=bucket_name,
            object=object_name,
            generation=generation,
            policy=policy))

  @error_util.catch_http_error_raise_gcs_api_error()
  def upload_object(
      self,
      source_stream,
      destination_resource,
      request_config,
      posix_to_set=None,
      source_resource=None,
      serialization_data=None,
      tracker_callback=None,
      upload_strategy=cloud_api.UploadStrategy.SIMPLE,
  ):
    """See CloudApi class for function doc strings."""

    if self._upload_http_client is None:
      self._upload_http_client = transports.GetApitoolsTransport(
          redact_request_body_reason=(
              'Object data is not displayed to keep the log output clean.'
              ' Set log_http_show_request_body property to True to print the'
              ' body of this request.'))

    source_path = self._get_source_path(source_resource)
    should_gzip_in_flight = gzip_util.should_gzip_in_flight(
        request_config.gzip_settings, source_path)

    if should_gzip_in_flight:
      log.info(
          'Using compressed transport encoding for {}.'.format(source_path))
    if upload_strategy == cloud_api.UploadStrategy.SIMPLE:
      uploader = upload.SimpleUpload(
          self,
          self._upload_http_client,
          source_stream,
          destination_resource,
          should_gzip_in_flight,
          request_config,
          posix_to_set=posix_to_set,
          source_resource=source_resource,
      )
    elif upload_strategy == cloud_api.UploadStrategy.RESUMABLE:
      uploader = upload.ResumableUpload(
          self,
          self._upload_http_client,
          source_stream,
          destination_resource,
          should_gzip_in_flight,
          request_config,
          posix_to_set=posix_to_set,
          serialization_data=serialization_data,
          source_resource=source_resource,
          tracker_callback=tracker_callback,
      )
    elif upload_strategy == cloud_api.UploadStrategy.STREAMING:
      uploader = upload.StreamingUpload(
          self,
          self._upload_http_client,
          source_stream,
          destination_resource,
          should_gzip_in_flight,
          request_config,
          posix_to_set=posix_to_set,
          source_resource=source_resource,
      )
    else:
      raise command_errors.Error('Invalid upload strategy: {}.'.format(
          upload_strategy.value))

    encryption_key = getattr(request_config.resource_args, 'encryption_key',
                             None)
    try:
      with self._encryption_headers_context(encryption_key):
        metadata = uploader.run()
    except (
        apitools_exceptions.StreamExhausted,
        apitools_exceptions.TransferError,
    ) as error:
      raise cloud_errors.ResumableUploadAbortError(
          '{}\n This likely occurred because the file being uploaded changed '
          'size between resumable upload attempts. If this error persists, try '
          'deleting the tracker files present in {}'.format(
              str(error),
              properties.VALUES.storage.tracker_files_directory.Get()))

    return metadata_util.get_object_resource_from_metadata(metadata)

  @error_util.catch_http_error_raise_gcs_api_error()
  def create_managed_folder(self, bucket_name, managed_folder_name):
    """See CloudApi class for function doc strings."""
    folder_message = self.messages.ManagedFolder(
        bucket=bucket_name, name=managed_folder_name
    )
    response = self.client.managedFolders.Insert(folder_message)
    return metadata_util.get_managed_folder_resource_from_metadata(response)

  @error_util.catch_http_error_raise_gcs_api_error()
  def delete_managed_folder(self, bucket_name, managed_folder_name):
    """See CloudApi class for function doc strings."""
    delete_request = self.messages.StorageManagedFoldersDeleteRequest(
        bucket=bucket_name, managedFolder=managed_folder_name
    )
    self.client.managedFolders.Delete(delete_request)

  @error_util.catch_http_error_raise_gcs_api_error()
  def get_managed_folder(self, bucket_name, managed_folder_name):
    """See CloudApi class for function doc strings."""
    response = self.client.managedFolders.Get(
        self.messages.StorageManagedFoldersGetRequest(
            bucket=bucket_name, managedFolder=managed_folder_name
        )
    )
    return metadata_util.get_managed_folder_resource_from_metadata(response)

  @error_util.catch_http_error_raise_gcs_api_error()
  def get_managed_folder_iam_policy(self, bucket_name, managed_folder_name):
    """See CloudApi class for function doc strings."""
    global_params = self.messages.StandardQueryParameters(
        fields='bindings,etag',
    )
    return self.client.managedFolders.GetIamPolicy(
        self.messages.StorageManagedFoldersGetIamPolicyRequest(
            bucket=bucket_name, managedFolder=managed_folder_name
        ),
        global_params=global_params,
    )

  def list_managed_folders(self, bucket_name, prefix=None):
    """See CloudApi class for function doc strings."""
    try:
      for folder in list_pager.YieldFromList(
          self.client.managedFolders,
          self.messages.StorageManagedFoldersListRequest(
              bucket=bucket_name,
              prefix=prefix,
          ),
          batch_size=1000,
          batch_size_attribute='pageSize',
          field='items',
      ):
        yield metadata_util.get_managed_folder_resource_from_metadata(folder)
    except apitools_exceptions.HttpError as e:
      core_exceptions.reraise(
          cloud_errors.translate_error(
              e,
              error_util.ERROR_TRANSLATION,
              status_code_getter=error_util.get_status_code,
          )
      )

  @error_util.catch_http_error_raise_gcs_api_error()
  def set_managed_folder_iam_policy(
      self, bucket_name, managed_folder_name, policy
  ):
    """See CloudApi class for function doc strings."""
    return self.client.managedFolders.SetIamPolicy(
        self.messages.StorageManagedFoldersSetIamPolicyRequest(
            bucket=bucket_name, managedFolder=managed_folder_name, policy=policy
        )
    )

  @error_util.catch_http_error_raise_gcs_api_error()
  def get_service_agent(self, project_id=None, project_number=None):
    """See CloudApi class for doc strings."""
    if project_id:
      project_identifier = project_id
    elif project_number:
      project_identifier = six.text_type(project_number)
    else:
      project_identifier = properties.VALUES.core.project.GetOrFail()
    return self.client.projects_serviceAccount.Get(
        self.messages.StorageProjectsServiceAccountGetRequest(
            projectId=project_identifier)).email_address

  @error_util.catch_http_error_raise_gcs_api_error()
  def create_notification_configuration(
      self,
      url,
      pubsub_topic,
      custom_attributes=None,
      event_types=None,
      object_name_prefix=None,
      payload_format=cloud_api.NotificationPayloadFormat.JSON):
    """See CloudApi class for doc strings."""
    if not url.is_bucket():
      raise command_errors.InvalidUrlError(
          'Create notification configuration endpoint accepts only bucket URLs.'
      )
    notification_configuration = self.messages.Notification(
        topic=pubsub_topic,
        payload_format=_NOTIFICATION_PAYLOAD_FORMAT_KEY_TO_API_CONSTANT[
            payload_format])
    if custom_attributes:
      additional_properties = []
      for key, value in custom_attributes.items():
        additional_properties.append((
            self.messages.Notification.CustomAttributesValue.AdditionalProperty(
                key=key, value=value)))
      notification_configuration.custom_attributes = (
          self.messages.Notification.CustomAttributesValue(
              additionalProperties=additional_properties))
    if event_types:
      notification_configuration.event_types = [
          event_type.value for event_type in event_types
      ]
    if object_name_prefix:
      notification_configuration.object_name_prefix = object_name_prefix

    return self.client.notifications.Insert(
        self.messages.StorageNotificationsInsertRequest(
            bucket=url.bucket_name,
            notification=notification_configuration,
            userProject=properties.VALUES.core.project.GetOrFail()))

  @error_util.catch_http_error_raise_gcs_api_error()
  def delete_notification_configuration(self, url, notification_id):
    """See CloudApi class for doc strings."""
    if not url.is_bucket():
      raise command_errors.InvalidUrlError(
          'Delete notification configuration endpoint accepts only bucket URLs.'
      )
    self.client.notifications.Delete(
        self.messages.StorageNotificationsDeleteRequest(
            bucket=url.bucket_name,
            notification=notification_id,
            userProject=properties.VALUES.core.project.GetOrFail()))

  @error_util.catch_http_error_raise_gcs_api_error()
  def get_notification_configuration(self, url, notification_id):
    """See CloudApi class for doc strings."""
    if not url.is_bucket():
      raise command_errors.InvalidUrlError(
          'Get notification configuration endpoint accepts only bucket URLs.'
      )
    return self.client.notifications.Get(
        self.messages.StorageNotificationsGetRequest(
            bucket=url.bucket_name,
            notification=notification_id,
            userProject=properties.VALUES.core.project.GetOrFail()))

  @error_util.catch_http_error_raise_gcs_api_error()
  def list_notification_configurations(self, url):
    """See CloudApi class for function doc strings."""
    if not url.is_bucket():
      raise command_errors.InvalidUrlError(
          'List notification configurations endpoint accepts only bucket URLs.'
      )

    response = self.client.notifications.List(
        self.messages.StorageNotificationsListRequest(
            bucket=url.bucket_name,
            userProject=properties.VALUES.core.project.GetOrFail()))
    for notification_configuration in response.items:
      yield notification_configuration

  @error_util.catch_http_error_raise_gcs_api_error()
  def cancel_operation(self, bucket_name, operation_id):
    """See CloudApi class."""
    self.client.operations.Cancel(
        self.messages.StorageBucketsOperationsCancelRequest(
            bucket=bucket_name,
            operationId=operation_id,
        )
    )

  @error_util.catch_http_error_raise_gcs_api_error()
  def get_operation(self, bucket_name, operation_id):
    """See CloudApi class."""
    return self.client.operations.Get(
        self.messages.StorageBucketsOperationsGetRequest(
            bucket=bucket_name,
            operationId=operation_id,
        )
    )

  def list_operations(self, bucket_name, server_side_filter=None):
    """See CloudApi class."""
    request = self.messages.StorageBucketsOperationsListRequest(
        bucket=bucket_name,
        filter=server_side_filter,
    )
    operation_iterator = list_pager.YieldFromList(
        self.client.operations,
        request,
        batch_size_attribute='pageSize',
        field='operations',
    )
    try:
      for operation in operation_iterator:
        yield operation
    except apitools_exceptions.HttpError as e:
      core_exceptions.reraise(
          cloud_errors.translate_error(e, error_util.ERROR_TRANSLATION)
      )

  @error_util.catch_http_error_raise_gcs_api_error()
  def restore_object(self, url, request_config):
    """See CloudApi class."""
    if request_config.resource_args:
      preserve_acl = request_config.resource_args.preserve_acl
    else:
      preserve_acl = None

    object_metadata = self.client.objects.Restore(
        self.messages.StorageObjectsRestoreRequest(
            bucket=url.bucket_name,
            copySourceAcl=preserve_acl,
            generation=int(url.generation),
            ifGenerationMatch=request_config.precondition_generation_match,
            ifMetagenerationMatch=(
                request_config.precondition_metageneration_match
            ),
            object=url.object_name,
        )
    )
    return metadata_util.get_object_resource_from_metadata(object_metadata)

  @error_util.catch_http_error_raise_gcs_api_error()
  def bulk_restore_objects(
      self,
      bucket_url,
      object_globs,
      request_config,
      allow_overwrite=False,
      deleted_after_time=None,
      deleted_before_time=None,
  ):
    """See CloudApi class."""
    if request_config.resource_args:
      preserve_acl = request_config.resource_args.preserve_acl
    else:
      preserve_acl = None

    with self._apitools_request_headers_context(
        {'x-goog-gcs-idempotency-token': uuid.uuid4().hex}
    ):
      operation = self.client.objects.BulkRestore(
          self.messages.StorageObjectsBulkRestoreRequest(
              bucket=bucket_url.bucket_name,
              bulkRestoreObjectsRequest=self.messages.BulkRestoreObjectsRequest(
                  allowOverwrite=allow_overwrite,
                  copySourceAcl=preserve_acl,
                  matchGlobs=object_globs,
                  softDeletedAfterTime=deleted_after_time,
                  softDeletedBeforeTime=deleted_before_time,
              ),
          )
      )
    return operation

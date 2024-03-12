# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""API interface for interacting with cloud storage providers."""

# TODO(b/275749579): Rename this module.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum

from googlecloudsdk.command_lib.storage import storage_url


class Capability(enum.Enum):
  """Used to track API capabilities relevant to logic in tasks."""
  COMPOSE_OBJECTS = 'COMPOSE_OBJECTS'
  CLIENT_SIDE_HASH_VALIDATION = 'CLIENT_SIDE_HASH_VALIDATION'
  ENCRYPTION = 'ENCRYPTION'
  MANAGED_FOLDERS = 'MANAGED_FOLDERS'
  RESUMABLE_UPLOAD = 'RESUMABLE_UPLOAD'
  SLICED_DOWNLOAD = 'SLICED_DOWNLOAD'
  # For daisy chain operations, the upload stream is not purely seekable.
  # For certain seek calls, we raise errors to avoid re-downloading the object.
  # We do not want the "seekable" method for the upload stream to always return
  # False because in case of GCS, Apitools checks for this value to determine
  # if a resumable upload can be performed. However, for S3,
  # boto3's upload_fileobj calls "seek" with
  # unsupported offset and whence combinations, and to avoid that,
  # we need to mark the upload stream as non-seekable for S3.
  # This value is used by daisy chain operation to determine if the upload
  # stream can be treated as seekable.
  DAISY_CHAIN_SEEKABLE_UPLOAD_STREAM = 'DAISY_CHAIN_SEEKABLE_UPLOAD_STREAM'


class DownloadStrategy(enum.Enum):
  """Enum class for specifying download strategy."""
  ONE_SHOT = 'oneshot'  # No in-flight retries performed.
  # Operations are retried on network errors.
  RETRIABLE_IN_FLIGHT = 'retriable_in_flight'
  # In addition to retrying on errors, operations can be resumed if halted.
  # This option will write tracker files to track the downloads in progress.
  RESUMABLE = 'resumable'


class UploadStrategy(enum.Enum):
  """Enum class for specifying upload strategy."""
  SIMPLE = 'simple'
  RESUMABLE = 'resumable'
  STREAMING = 'streaming'


class FieldsScope(enum.Enum):
  """Values used to determine fields and projection values for API calls."""

  FULL = 1
  NO_ACL = 2
  RSYNC = 3  # Only for objects.
  SHORT = 4


class HmacKeyState(enum.Enum):
  ACTIVE = 'ACTIVE'
  INACTIVE = 'INACTIVE'


class NotificationEventType(enum.Enum):
  """Used to filter what events a notification configuration notifies on."""
  OBJECT_ARCHIVE = 'OBJECT_ARCHIVE'
  OBJECT_DELETE = 'OBJECT_DELETE'
  OBJECT_FINALIZE = 'OBJECT_FINALIZE'
  OBJECT_METADATA_UPDATE = 'OBJECT_METADATA_UPDATE'


class NotificationPayloadFormat(enum.Enum):
  """Used to format the body of notifications."""
  JSON = 'json'
  NONE = 'none'


class ObjectState(enum.Enum):
  """For whether to operate on live, noncurrent, or soft-deleted objects."""

  LIVE = 'live'  # Default.
  LIVE_AND_NONCURRENT = 'live-and-noncurrent'
  SOFT_DELETED = 'soft-deleted'


DEFAULT_PROVIDER = storage_url.ProviderPrefix.GCS
NUM_ITEMS_PER_LIST_PAGE = 1000


class CloudApi(object):
  """Abstract base class for interacting with cloud storage providers.

  Implementations of the Cloud API are not guaranteed to be thread-safe.
  Behavior when calling a Cloud API instance simultaneously across
  threads is undefined and doing so will likely cause errors. Therefore,
  a separate instance of the Cloud API should be instantiated per-thread.

  Attributes:
    capabilities (set[Capability]): If a Capability is present in this set, this
      API can be used to execute related logic in tasks.
  """
  capabilities = set()

  # Some APIs limit the number of objects that can be composed in a single call.
  # This field should be overidden by those APIs, and default to 1 for APIs
  # that do not support compose_objects.
  MAX_OBJECTS_PER_COMPOSE_CALL = 1

  # All supported APIs currently limit object names to 1024 UTF-8 encoded bytes.
  # S3: https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-keys.html
  # GCS: https://cloud.google.com/storage/docs/objects#naming
  MAX_OBJECT_NAME_LENGTH = 1024

  def create_anywhere_cache(
      self, bucket_name, zone, admission_policy=None, ttl=None
  ):
    """Creates Anywhere Cache for given bucket.

    Args:
      bucket_name (str): The name of the bucket where the Anywhere Cache should
        be created.
      zone (str): Name of the zonal locations where the Anywhere Cache should be
        created.
      admission_policy (str|None): The cache admission policy decides for each
        cache miss, that is whether to insert the missed block or not.
      ttl (str|None): Cache entry time-to-live in seconds

    Returns:
      GoogleLongrunningOperation Apitools object for creating caches.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('create_anywhere_cache must be overridden.')

  def get_anywhere_cache(self, bucket_name, anywhere_cache_id):
    """Gets Anywhere Cache Instance for a zone in bucket.

    Args:
      bucket_name (str): The name of the bucket.
      anywhere_cache_id (str): Unique identifier for a cache instance in bucket.

    Returns:
      AnywhereCache: the Anywhere Cache Instance

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('get_anywhere_cache must be overridden.')

  def pause_anywhere_cache(
      self, bucket_name, anywhere_cache_id
  ):
    """Pauses Anywhere Cache Instance for a zone in bucket.

    Args:
      bucket_name (str): The name of the bucket.
      anywhere_cache_id (str): Unique identifier for a cache instance in bucket.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('pause_anywhere_cache must be overridden.')

  def resume_anywhere_cache(self, bucket_name, anywhere_cache_id):
    """Resumes Anywhere Cache in particular zone of a bucket.

    Args:
      bucket_name (str): The name of the bucket where the Anywhere Cache should
        be resumed.
      anywhere_cache_id (str): Unique identifier for a cache instance in bucket.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('resume_anywhere_cache must be overridden.')

  def disable_anywhere_cache(self, bucket_name, anywhere_cache_id):
    """Disables Anywhere Cache in particular zone of a bucket.

    Args:
      bucket_name (str): The name of the bucket where the Anywhere Cache should
        be disabled.
      anywhere_cache_id (str): Unique identifier for a cache instance in bucket.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('disable_anywhere_cache must be overridden.')

  def list_anywhere_caches(self, bucket_name):
    """Lists all Anywhere Cache instances of the bucket.

    Args:
      bucket_name (str): The name of the bucket.

    Yields:
      Iterator over gcs_resource_reference.GcsAnywhereCacheResource objects.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('list_anywhere_cache must be overridden.')

  def patch_anywhere_cache(
      self, bucket_name, anywhere_cache_id, admission_policy=None, ttl=None
  ):
    """Updates Anywhere Cache instance of a bucket.

    Args:
      bucket_name (str): The name of the bucket where the Anywhere Cache should
        be updated.
      anywhere_cache_id (str): Unique identifier for a cache instance in bucket.
      admission_policy (str|None): The cache admission policy decides for each
        cache miss, that is whether to insert the missed block or not.
      ttl (str|None): Cache entry time-to-live in seconds

    Returns:
      GoogleLongrunningOperation Apitools object for creating caches.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('patch_anywhere_cache must be overridden.')

  def create_bucket(self, bucket_resource, request_config, fields_scope=None):
    """Creates a new bucket with the specified metadata.

    Args:
      bucket_resource (resource_reference.UnknownResource): The bucket to
        create.
      request_config (RequestConfig): Contains metadata for new bucket.
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.

    Raises:
      CloudApiError: API returned an error.
      Error: Invalid fields_scope.
      NotImplementedError: This function was not implemented by a class using
        this interface.

    Returns:
      resource_reference.BucketResource representing new bucket.
    """
    raise NotImplementedError('create_bucket must be overridden.')

  def delete_bucket(self, bucket_name, request_config):
    """Deletes a bucket.

    Args:
      bucket_name (str): Name of the bucket to delete.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('delete_bucket must be overridden.')

  def get_bucket(self, bucket_name, fields_scope=None):
    """Gets bucket metadata.

    Args:
      bucket_name (str): Name of the bucket.
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.

    Returns:
      resource_reference.BucketResource containing the bucket metadata.

    Raises:
      CloudApiError: API returned an error.
      Error: Invalid fields_scope.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('get_bucket must be overridden.')

  def get_bucket_iam_policy(self, bucket_name):
    """Gets bucket IAM policy.

    Args:
      bucket_name (str): Name of the bucket.

    Returns:
      Provider-specific data type. Currently, only available for GCS so returns
        Apitools messages.Policy object. If supported for
        more providers in the future, use a generic container.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('get_bucket_iam_policy must be overridden.')

  def list_buckets(self, fields_scope=None):
    """Lists bucket metadata for the given project.

    Args:
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.

    Yields:
      Iterator over resource_reference.BucketResource objects

    Raises:
      Error: Invalid fields_scope.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('list_buckets must be overridden.')

  def lock_bucket_retention_policy(self, bucket_resource, request_config):
    """Locks a bucket's retention policy.

    Args:
      bucket_resource (UnknownResource): The bucket with the policy to lock.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.

    Returns:
      resource_reference.BucketResource containing the bucket metadata.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
          this interface.
    """
    raise NotImplementedError(
        'lock_bucket_retention_policy must be overridden.')

  def patch_bucket(self, bucket_resource, request_config, fields_scope=None):
    """Patches bucket metadata.

    Args:
      bucket_resource (BucketResource|UnknownResource): The bucket to patch.
      request_config (RequestConfig): Contains new metadata for the bucket.
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.

    Returns:
      resource_reference.BucketResource containing the bucket metadata.

    Raises:
      CloudApiError: API returned an error.
      Error: Invalid fields_scope.
      NotImplementedError: This function was not implemented by a class using
          this interface.
    """
    raise NotImplementedError('patch_bucket must be overridden.')

  def set_bucket_iam_policy(self, bucket_name, policy):
    """Sets bucket IAM policy.

    Args:
      bucket_name (str): Name of the bucket.
      policy (object): Provider-specific data type. Currently, only
        available for GCS so Apitools messages.Policy object. If supported for
        more providers in the future, use a generic container.

    Returns:
      Provider-specific data type. Currently, only available for GCS so returns
        Apitools messages.Policy object. If supported for
        more providers in the future, use a generic container.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('get_bucket_iam_policy must be overridden.')

  def create_hmac_key(self, service_account_email):
    """Creates an HMAC key.

    Args:
      service_account_email (str): The email of the service account to use.

    Returns:
      gcs_resource_reference.GcsHmacKeyResource. Provider-specific data type
      is used for now because we currently support this feature only for the
      JSON API.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('create_hmac_key must be overridden.')

  def delete_hmac_key(self, access_id):
    """Deletes an HMAC key.

    Args:
      access_id (str): The access ID corresponding to the HMAC key.

    Returns:
      None

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('delete_hmac_key must be overridden.')

  def get_hmac_key(self, access_id):
    """Gets an HMAC key.

    Args:
      access_id (str): The access ID corresponding to the HMAC key.

    Returns:
      gcs_resource_reference.GcsHmacKeyResource. Provider-specific data type
      is used for now because we currently support this feature only for the
      JSON API.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('get_hmac_key must be overridden.')

  def list_hmac_keys(self, service_account_email=None, show_deleted_keys=False,
                     fields_scope=None):
    """Lists HMAC keys.

    Args:
      service_account_email (str): Return HMAC keys for the given service
        account email.
      show_deleted_keys (bool): If True, include keys in the DELETED state.
      fields_scope (FieldsScope): Determines which metadata keys
        the API should return for each key.

    Yields:
      Iterator over gcs_resource_reference.GcsHmacKeyResource objects.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    pass

  def patch_hmac_key(self, access_id, etag, state):
    """Updates an HMAC key.

    Args:
      access_id (str): The access ID corresponding to the HMAC key.
      etag (str): Only perform the patch request if the etag matches this value.
      state (HmacKeyState): The desired state of the HMAC key.

    Returns:
      gcs_resource_reference.GcsHmacKeyResource. Provider-specific data type
        is used for now because we currently support this feature only for the
        JSON API.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('patch_hmac_key must be overridden.')

  def compose_objects(
      self,
      source_resources,
      destination_resource,
      request_config,
      original_source_resource=None,
      posix_to_set=None,
  ):
    """Concatenates a list of objects into a new object.

    Args:
      source_resources (list[ObjectResource|UnknownResource]): The objects to
        compose.
      destination_resource (resource_reference.UnknownResource): Metadata for
        the resulting composite object.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.
      original_source_resource (Resource|None): Useful for finding metadata to
        apply to final object. For instance, if doing a composite upload, this
        would represent the pre-split local file.
      posix_to_set (PosixAttributes|None): Set as custom metadata on target.

    Returns:
      resource_reference.ObjectResource with composite object's metadata.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('compose_object must be overridden.')

  def copy_object(
      self,
      source_resource,
      destination_resource,
      request_config,
      posix_to_set=None,
      progress_callback=None,
      should_deep_copy_metadata=False,
  ):
    """Copies an object within the cloud of one provider.

    Args:
      source_resource (resource_reference.ObjectResource): Resource for source
        object. Must have been confirmed to exist in the cloud.
      destination_resource (resource_reference.ObjectResource|UnknownResource):
        Resource for destination object. Existence doesn't have to be confirmed.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.
      posix_to_set (PosixAttributes|None): Set as custom metadata on target.
      progress_callback (function): Optional callback function for progress
        notifications. Receives calls with arguments (bytes_transferred,
        total_size).
      should_deep_copy_metadata (bool): Rather than copying select fields of the
        source metadata, if True, copy everything. The request_config data
        (containing user args) overrides the deep-copied data.

    Returns:
      resource_reference.ObjectResource with new object's metadata.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('copy_object must be overridden')

  def delete_object(self, object_url, request_config):
    """Deletes an object.

    Args:
      object_url (storage_url.CloudUrl): Url of object to delete.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
          this interface.
    """
    raise NotImplementedError('delete_object must be overridden.')

  def download_object(self,
                      cloud_resource,
                      download_stream,
                      request_config,
                      digesters=None,
                      do_not_decompress=False,
                      download_strategy=DownloadStrategy.ONE_SHOT,
                      progress_callback=None,
                      start_byte=0,
                      end_byte=None):
    """Gets object data.

    Args:
      cloud_resource (resource_reference.ObjectResource): Contains metadata and
        information about object being downloaded.
      download_stream (stream): Stream to send the object data to.
      request_config (RequestConfig): Contains arguments for API calls.
      digesters (dict): Dict of {string : digester}, where string is the name of
        a hash algorithm, and digester is a validation digester object that
        update(bytes) and digest() using that algorithm. Implementation can set
        the digester value to None to indicate supports bytes were not
        successfully digested on-the-fly.
      do_not_decompress (bool): If true, gzipped objects will not be
        decompressed on-the-fly if supported by the API.
      download_strategy (DownloadStrategy): Cloud API download strategy to use
        for download.
      progress_callback (function): Optional callback function for progress
        notifications. Receives calls with arguments (bytes_transferred,
        total_size).
      start_byte (int): Starting point for download (for resumable downloads and
        range requests). Can be set to negative to request a range of bytes
        (python equivalent of [:-3]).
      end_byte (int): Ending byte number, inclusive, for download (for range
        requests). If None, download the rest of the object.

    Returns:
      server_encoding (str): Useful for determining what the server actually
        sent versus what object metadata claims.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('download_object must be overridden.')

  def get_object_iam_policy(self, bucket_name, object_name, generation=None):
    """Gets object IAM policy.

    Args:
      bucket_name (str): Name of the bucket.
      object_name (str): Name of the object.
      generation (str|None): Generation of object.

    Returns:
      Provider-specific data type. Currently, only available for GCS so returns
        Apitools messages.Policy object. If supported for
        more providers in the future, use a generic container.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('get_object_iam_policy must be overridden.')

  def get_object_metadata(
      self,
      bucket_name,
      object_name,
      request_config=None,
      generation=None,
      fields_scope=None,
      soft_deleted=False,
  ):
    """Gets object metadata.

    If decryption is supported by the implementing class, this function will
    read decryption keys from configuration and appropriately retry requests to
    encrypted objects with the correct key.

    Args:
      bucket_name (str): Bucket containing the object.
      object_name (str): Object name.
      request_config (RequestConfig): Contains API call arguments.
      generation (string): Generation of the object to retrieve.
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.
      soft_deleted (bool): Returns the soft-deleted version of an object (not
        the live version or a past version in a bucket with versioning enabled).

    Returns:
      resource_reference.ObjectResource with object metadata.

    Raises:
      CloudApiError: API returned an error.
      Error: Invalid fields_scope.
      NotImplementedError: This function was not implemented by a class using
        this interface.
      NotFoundError: Raised if object does not exist.
    """
    raise NotImplementedError('get_object_metadata must be overridden.')

  def list_objects(
      self,
      bucket_name,
      prefix=None,
      delimiter=None,
      fields_scope=None,
      halt_on_empty_response=True,
      include_folders_as_prefixes=None,
      next_page_token=None,
      object_state=ObjectState.LIVE,
  ):
    """Lists objects (with metadata) and prefixes in a bucket.

    Args:
      bucket_name (str): Bucket containing the objects.
      prefix (str|None): Prefix for directory-like behavior.
      delimiter (str|None): Delimiter for directory-like behavior.
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.
      halt_on_empty_response (bool): For features like soft delete, the API may
        return an empty list and a next page token. If true, print a warning
        instead of using the next page token. See the warning text details.
      include_folders_as_prefixes (bool): If True, includes managed folders as
        prefixes in list responses. This means that managed folders that don't
        contain objects will be listed.
      next_page_token (str|None): Used to resume LIST calls. For example, if
        halt_on_empty_response was true and a halt warning is printed, it will
        contain a next_page_token the user can use to resume querying.
      object_state (ObjectState): What versions of an object to query.

    Yields:
      Iterator over resource_reference.ObjectResource objects.

    Raises:
      Error: Invalid fields_scope.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('list_objects must be overridden.')

  def patch_object_metadata(
      self,
      bucket_name,
      object_name,
      object_resource,
      request_config,
      fields_scope=None,
      generation=None,
      posix_to_set=None,
  ):
    """Updates object metadata with patch semantics.

    Args:
      bucket_name (str): Bucket containing the object.
      object_name (str): Object name.
      object_resource (resource_reference.ObjectResource): Contains metadata
        that will be used to update cloud object. May have different name than
        object_name argument.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.
      fields_scope (FieldsScope): Determines the fields and projection
        parameters of API call.
      generation (string): Generation (or version) of the object to update.
      posix_to_set (PosixAttributes|None): Set as custom metadata on target.

    Returns:
      resource_reference.ObjectResource with patched object metadata.

    Raises:
      CloudApiError: API returned an error.
      Error: Invalid fields_scope.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('patch_object_metadata must be overridden.')

  def set_object_iam_policy(self,
                            bucket_name,
                            object_name,
                            policy,
                            generation=None):
    """Sets object IAM policy.

    Args:
      bucket_name (str): Name of the bucket.
      object_name (str): Name of the object.
      policy (object): Provider-specific data type. Currently, only available
        for GCS so Apitools messages.Policy object. If supported for more
        providers in the future, use a generic container.
      generation (str|None): Generation of object.

    Returns:
      Provider-specific data type. Currently, only available for GCS so returns
        Apitools messages.Policy object. If supported for
        more providers in the future, use a generic container.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('set_bucket_iam_policy must be overridden.')

  def upload_object(
      self,
      source_stream,
      destination_resource,
      request_config,
      posix_to_set=None,
      serialization_data=None,
      source_resource=None,
      tracker_callback=None,
      upload_strategy=UploadStrategy.SIMPLE,
  ):
    """Uploads object data and metadata.

    Args:
      source_stream (stream): Seekable stream of object data.
      destination_resource (resource_reference.ObjectResource|UnknownResource):
        Contains the correct metadata to upload.
      request_config (RequestConfig): Object containing general API function
        arguments. Subclasses for specific cloud providers are available.
      posix_to_set (PosixAttributes|None): Set as custom metadata on target.
      serialization_data (dict): API-specific data needed to resume an upload.
        Only used with UploadStrategy.RESUMABLE.
      source_resource (resource_reference.FileObjectResource|None): Contains the
        source StorageUrl. Can be None if source is pure stream.
      tracker_callback (Callable[[dict]|None]): Function that writes a tracker
        file with serialization data. Only used with UploadStrategy.RESUMABLE.
      upload_strategy (UploadStrategy): Strategy to use for this upload.

    Returns:
      resource_reference.ObjectResource with uploaded object's metadata.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('upload_object must be overridden.')

  def create_managed_folder(self, bucket_name, managed_folder_name):
    """Creates a managed folder.

    Args:
      bucket_name (str): The bucket to create the managed folder in.
      managed_folder_name (str): The name of the managed folder to create.

    Returns:
      A resource_reference.ManagedFolderResource for the new managed folder.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('create_managed_folder must be overridden.')

  def delete_managed_folder(self, bucket_name, managed_folder_name):
    """Deletes a managed folder.

    Args:
      bucket_name (str): The bucket containing the managed folder to delete.
      managed_folder_name (str): The name of the managed folder to delete.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('delete_managed_folder must be overridden.')

  def get_managed_folder(self, bucket_name, managed_folder_name):
    """Gets metadata for a managed folder.

    Args:
      bucket_name (str): The bucket containing the managed folder to get.
      managed_folder_name (str): The name of the managed folder to get.

    Returns:
      A resource_reference.ManagedFolderResource.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('get_managed_folder must be overridden.')

  def get_managed_folder_iam_policy(self, bucket_name, managed_folder_name):
    """Gets the IAM policy for a managed folder.

    Args:
      bucket_name (str): The bucket containing the managed folder to get the IAM
        policy for.
      managed_folder_name (str): The name of the managed folder to get the IAM
        policy for.

    Returns:
      An Apitools message.Policy object.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError(
        'get_managed_folder_iam_policy must be overridden.'
    )

  def list_managed_folders(self, bucket_name, prefix=None):
    """Lists managed folders in a bucket.

    Args:
      bucket_name (str): The bucket to list managed folders in.
      prefix (str|None): Only managed folders beginning with `prefix` are listed
        if specified.

    Yields:
      resource_reference.ManagedFolderResources

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError('list_managed_folders must be overridden.')

  def set_managed_folder_iam_policy(
      self, bucket_name, managed_folder_name, policy
  ):
    """Sets the IAM policy for a managed folder.

    Args:
      bucket_name (str): The bucket containing the managed folder to get the IAM
        policy for.
      managed_folder_name (str): The name of the managed folder to get the IAM
        policy for.
      policy (object): Provider-specific data type. Currently, only available
        for GCS so Apitools messages.Policy object. If supported for more
        providers in the future, use a generic container.

    Returns:
      Provider-specific data type. Currently, only available for GCS so returns
        Apitools messages.Policy object. If supported for
        more providers in the future, use a generic container.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError(
        'set_managed_folder_iam_policy must be overridden.'
    )

  def get_service_agent(self, project_id=None, project_number=None):
    """Returns the email address (str) used to identify the service agent.

    For some providers, the service agent is responsible for encrypting and
    decrypting objects using CMEKs. project_number is useful because it may be
    in bucket metadata when project ID is not.

    If neither project_id or project_number are available, uses the
      default project configured in gcloud.


    Args:
      project_id (str|None): Project to get service account for. Takes
        precedence over project_number.
      project_number (int|None): Project to get service account for.

    Returns:
      Email of service account (str).
    """
    raise NotImplementedError('get_service_agent must be overridden.')

  def create_notification_configuration(
      self,
      url,
      pubsub_topic,
      custom_attributes=None,
      event_types=None,
      object_name_prefix=None,
      payload_format=NotificationPayloadFormat.JSON):
    """Creates a new notification on a bucket with the specified parameters.

    Args:
      url (storage_url.CloudUrl): Bucket URL.
      pubsub_topic (str): Cloud Pub/Sub topic to publish to.
      custom_attributes (dict[str, str]|None): Dictionary of custom attributes
        to apply to all notifications sent by the new configuration.
      event_types (list[NotificationEventType]|None): Event type filters, e.g.
        'OBJECT_FINALIZE'.
      object_name_prefix (str|None): Filter on object name.
      payload_format (NotificationPayloadFormat): Format of body of
        notifications sent by the new configuration.

    Raises:
      CloudApiError: API returned an error.
      InvalidUrlError: Received a non-bucket URL.
      NotImplementedError: This function was not implemented by a class using
        this interface.

    Returns:
      Apitools Notification object for the new notification configuration.
    """
    raise NotImplementedError(
        'create_notification_configuration must be overridden.')

  def delete_notification_configuration(self, url, notification_id):
    """Deletes a notification configuration on a bucket.

    Args:
      url (storage_url.CloudUrl): Bucket URL.
      notification_id (str): Name of the notification configuration.

    Raises:
      CloudApiError: API returned an error.
      InvalidUrlError: Received a non-bucket URL.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError(
        'delete_notification_configuration must be overridden.')

  def get_notification_configuration(self, url, notification_id):
    """Gets a notification configuration on a bucket.

    Args:
      url (storage_url.CloudUrl): Bucket URL.
      notification_id (str): Name of the notification configuration.

    Raises:
      CloudApiError: API returned an error.
      InvalidUrlError: Received a non-bucket URL.
      NotImplementedError: This function was not implemented by a class using
        this interface.
    """
    raise NotImplementedError(
        'get_notification_configuration must be overridden.')

  def list_notification_configurations(self, url):
    """Lists notification configurations on a bucket.

    Args:
      url (storage_url.CloudUrl): Bucket URL.

    Raises:
      CloudApiError: API returned an error.
      InvalidUrlError: Received a non-bucket URL.
      NotImplementedError: This function was not implemented by a class using
        this interface.

    Yields:
      List of  apitools Notification objects.
    """
    raise NotImplementedError(
        'list_notification_configurations must be overridden.')

  def cancel_operation(self, bucket_name, operation_id):
    """Cancels a long-running operation if it's still running.

    Args:
      bucket_name (str): Bucket associated with operation.
      operation_id (str): Operation to cancel.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: Function not implemented by child class.
    """
    raise NotImplementedError('cancel_operation must be overridden.')

  def get_operation(self, bucket_name, operation_id):
    """Returns metadata of a long-running operation.

    Args:
      bucket_name (str): Bucket associated with operation.
      operation_id (str): Operation to fetch.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: Function not implemented by child class.

    Returns:
      Apitools Operation object (currently Google-only).
    """
    raise NotImplementedError('get_operation must be overridden.')

  def list_operations(self, bucket_name, server_side_filter=None):
    """Lists long-running operations.

    Args:
      bucket_name (str): Bucket associated with target operations.
      server_side_filter: (str|None): Filter operations on backend.

    Raises:
      CloudApiError: API returned an error.
      NotImplementedError: Function not implemented by child class.

    Yields:
      Apitools Operation objects (currently Google-only).
    """
    raise NotImplementedError('list_operations must be overridden.')

  def restore_object(self, url, request_config):
    """Restores soft-deleted object.

    Args:
      url (storage_url.CloudUrl): Object URL.
      request_config (RequestConfig): Contains preconditions for API requests.

    Raises:
      CloudApiError: API returned an error.
      InvalidUrlError: Received invalid object URL.
      NotImplementedError: This function was not implemented by a class using
        this interface.

    Returns:
      ObjectResource of restored resource.
    """
    raise NotImplementedError('restore_object must be overridden.')

  def bulk_restore_objects(
      self,
      bucket_url,
      object_globs,
      request_config,
      allow_overwrite=False,
      deleted_after_time=None,
      deleted_before_time=None,
  ):
    """Initiates long-running operation to restore soft-deleted objects.

    Args:
      bucket_url (StorageUrl): Launch a bulk restore operation for this bucket.
      object_globs (list[str]): Objects in the target bucket matching these glob
        patterns will be restored.
      request_config (RequestConfig): Contains preconditions for API requests.
      allow_overwrite (bool): Allow overwriting live objects with soft-deleted
        versions.
      deleted_after_time (datetime|None): Restore only objects soft-deleted
        after this time.
      deleted_before_time (datetime|None): Restore only objects soft-deleted
        before this time.

    Raises:
      CloudApiError: API returned an error.
      InvalidUrlError: Received invalid object URL.
      NotImplementedError: This function was not implemented by a class using
        this interface.

    Returns:
      GoogleLongrunningOperation Apitools object for restoring objects.
    """
    raise NotImplementedError('bulk_restore_object must be overridden.')

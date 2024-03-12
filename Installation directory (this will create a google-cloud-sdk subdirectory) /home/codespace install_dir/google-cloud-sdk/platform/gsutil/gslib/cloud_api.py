# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""Gsutil API for interacting with cloud storage providers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class CloudApi(object):
  """Abstract base class for interacting with cloud storage providers.

  Implementations of the gsutil Cloud API are not guaranteed to be thread-safe.
  Behavior when calling a gsutil Cloud API instance simultaneously across
  threads is undefined and doing so will likely cause errors. Therefore,
  a separate instance of the gsutil Cloud API should be instantiated per-thread.
  """

  def __init__(self,
               bucket_storage_uri_class,
               logger,
               status_queue,
               provider=None,
               debug=0,
               http_headers=None,
               trace_token=None,
               perf_trace_token=None,
               user_project=None):
    """Performs necessary setup for interacting with the cloud storage provider.

    Args:
      bucket_storage_uri_class: boto storage_uri class, used by APIs that
                                provide boto translation or mocking.
      logger: logging.logger for outputting log messages.
      status_queue: Queue for relaying status to UI.
      provider: Default provider prefix describing cloud storage provider to
                connect to.
      debug: Debug level for the API implementation (0..3).
      http_headers (dict|None): Arbitrary headers to be included in every request.
      trace_token: Google internal trace token to pass to the API
                   implementation (string).
      perf_trace_token: Performance trace token to use when making API calls.
      user_project: Project to be billed for this request.
    """
    self.bucket_storage_uri_class = bucket_storage_uri_class
    self.logger = logger
    self.status_queue = status_queue
    self.provider = provider
    self.debug = debug
    self.http_headers = http_headers
    self.trace_token = trace_token
    self.perf_trace_token = perf_trace_token
    self.user_project = user_project

  def GetServiceAccountId(self):
    """Returns the service account email id."""
    raise NotImplementedError('GetServiceAccountId must be overridden.')

  def GetBucket(self, bucket_name, provider=None, fields=None):
    """Gets Bucket metadata.

    Args:
      bucket_name: Name of the bucket.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only these Bucket metadata fields, for
              example, ['logging', 'defaultObjectAcl']

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Bucket object.
    """
    raise NotImplementedError('GetBucket must be overloaded')

  def GetBucketIamPolicy(self, bucket_name, provider=None, fields=None):
    """Returns an IAM policy for the specified Bucket.

    Args:
      bucket_name: Name of the bucket.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only the IAM policy fields specified.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with the cloud storage providers.

    Returns:
      Policy object of the bucket.
    """
    raise NotImplementedError('GetBucketIamPolicy must be overloaded')

  def SetBucketIamPolicy(self, bucket_name, policy, provider=None):
    """Sets an IAM policy for the specified Bucket.

    Args:
      bucket_name: Name of the bucket.
      policy: A Policy object describing the IAM policy.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with the cloud storage providers.

    Returns:
      Policy object of the bucket. May differ from input Policy.
    """
    raise NotImplementedError('SetBucketIamPolicy must be overloaded')

  def SignUrl(self, method, duration, path, generation, logger, region,
              signed_headers, string_to_sign_debug):
    """Sign a url using service account's system managed private key.

    Args:
      method: The HTTP method to be used with the signed URL.
      duration: timedelta for which the constructed signed URL should be valid.
      path: String path to the bucket or object for signing, in the form
          'bucket' or 'bucket/object'.
      generation: If not None, specifies a version of an object for signing.
      logger: logging.Logger for warning and debug output.
      region: Geographic region in which the requested resource resides.
      signed_headers: Dict containing the header  info like host
          content-type etc.
      string_to_sign_debug: If true AND logger is enabled for debug level,
          print string to sign to debug. Used to differentiate user's
          signed URL from the probing permissions-check signed URL.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.
      CommandException for errors because of invalid account used for signing.

    Returns:
      The signed url.
    """
    raise NotImplementedError('SignUrl must be overloaded')

  def ListBuckets(self, project_id=None, provider=None, fields=None):
    """Lists bucket metadata for the given project.

    Args:
      project_id: Project owning the buckets, default from config if None.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only these metadata fields for the listing,
              for example:
              ['items/logging', 'items/defaultObjectAcl'].
              Note that the WildcardIterator class should be used to list
              buckets instead of calling this function directly.  It amends
              the fields definition from get-like syntax such as
              ['logging', 'defaultObjectAcl'] so that the caller does not
              need to prepend 'items/' or specify fields necessary for listing
              (like nextPageToken).

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Iterator over Bucket objects.
    """
    raise NotImplementedError('ListBuckets must be overloaded')

  def PatchBucket(self,
                  bucket_name,
                  metadata,
                  canned_acl=None,
                  canned_def_acl=None,
                  preconditions=None,
                  provider=None,
                  fields=None):
    """Updates bucket metadata for the bucket with patch semantics.

    Args:
      bucket_name: Name of bucket to update.
      metadata: Bucket object defining metadata to be updated.
      canned_acl: Canned ACL to apply to the bucket.
      canned_def_acl: Canned default object ACL to apply to the bucket.
      preconditions: Preconditions for the request.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only these Bucket metadata fields.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Bucket object describing new bucket metadata.
    """
    raise NotImplementedError('PatchBucket must be overloaded')

  def LockRetentionPolicy(self, bucket_name, metageneration, provider=None):
    """Locks the Retention Policy on the bucket.

    Args:
      bucket_name: Name of bucket to update.
      metageneration: Bucket metageneration to use as a precondition.
      provider: Cloud storage provider to connect to. If not present,
                class-wide default is used.

    Raises:
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      None
    """
    raise NotImplementedError('LockRetentionPolicy must be overloaded')

  def CreateBucket(self,
                   bucket_name,
                   project_id=None,
                   metadata=None,
                   provider=None,
                   fields=None):
    """Creates a new bucket with the specified metadata.

    Args:
      bucket_name: Name of the new bucket.
      project_id: Project owner of the new bucket, default from config if None.
      metadata: Bucket object defining new bucket metadata.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only these Bucket metadata fields.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Bucket object describing new bucket metadata.
    """
    raise NotImplementedError('CreateBucket must be overloaded')

  def DeleteBucket(self, bucket_name, preconditions=None, provider=None):
    """Deletes a bucket.

    Args:
      bucket_name: Name of the bucket to delete.
      preconditions: Preconditions for the request.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      None.
    """
    raise NotImplementedError('DeleteBucket must be overloaded')

  class CsObjectOrPrefixType(object):
    """Enum class for describing CsObjectOrPrefix types."""
    OBJECT = 'object'  # Cloud object
    PREFIX = 'prefix'  # Cloud bucket subdirectory

  class CsObjectOrPrefix(object):
    """Container class for ListObjects results."""

    def __init__(self, data, datatype):
      """Stores a ListObjects result.

      Args:
        data: Root object, either an apitools Object or a string Prefix.
        datatype: CsObjectOrPrefixType of data.
      """
      self.data = data
      self.datatype = datatype

  def ListObjects(self,
                  bucket_name,
                  prefix=None,
                  delimiter=None,
                  all_versions=None,
                  provider=None,
                  fields=None):
    """Lists objects (with metadata) and prefixes in a bucket.

    Args:
      bucket_name: Bucket containing the objects.
      prefix: Prefix for directory-like behavior.
      delimiter: Delimiter for directory-like behavior.
      all_versions: If true, list all object versions.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only these metadata fields for the listing,
              for example:
              ['items/acl', 'items/updated', 'prefixes'].
              Note that the WildcardIterator class should be used to list
              objects instead of calling this function directly.  It amends
              the fields definition from get-like syntax such as
              ['acl', 'updated'] so that the caller does not need to
              prepend 'items/' or specify any fields necessary for listing
              (such as prefixes or nextPageToken).

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Iterator over CsObjectOrPrefix wrapper class.
    """
    raise NotImplementedError('ListObjects must be overloaded')

  def GetObjectIamPolicy(self,
                         bucket_name,
                         object_name,
                         generation=None,
                         provider=None,
                         fields=None):
    """Gets IAM policy for specified Object.

    Args:
      bucket_name: Bucket containing the object.
      object_name: Name of the object.
      generation: Generation of the object to retrieve.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only the IAM policy fields specified.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Object IAM policy.
    """
    raise NotImplementedError('GetObjectIamPolicy must be overloaded')

  def SetObjectIamPolicy(self,
                         bucket_name,
                         object_name,
                         policy,
                         generation=None,
                         provider=None):
    """Sets IAM policy for specified Object.

    Args:
      bucket_name: Bucket containing the object.
      object_name: Name of the object.
      policy: IAM Policy object.
      generation: Generation of the object to which the IAM policy will apply.
      provider: Cloud storage provider to connect to. If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Policy object of the object. May differ from input Policy.
    """
    raise NotImplementedError('SetObjectIamPolicy must be overloaded')

  def GetObjectMetadata(self,
                        bucket_name,
                        object_name,
                        generation=None,
                        provider=None,
                        fields=None):
    """Gets object metadata.

    If decryption is supported by the implementing class, this function will
    read decryption keys from configuration and appropriately retry requests to
    encrypted objects with the correct key.

    Args:
      bucket_name: Bucket containing the object.
      object_name: Object name.
      generation: Generation of the object to retrieve.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only these Object metadata fields, for
              example, ['acl', 'updated'].

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Object object.
    """
    raise NotImplementedError('GetObjectMetadata must be overloaded')

  def PatchObjectMetadata(self,
                          bucket_name,
                          object_name,
                          metadata,
                          canned_acl=None,
                          generation=None,
                          preconditions=None,
                          provider=None,
                          fields=None):
    """Updates object metadata with patch semantics.

    Args:
      bucket_name: Bucket containing the object.
      object_name: Object name for object.
      metadata: Object object defining metadata to be updated.
      canned_acl: Canned ACL to be set on the object.
      generation: Generation (or version) of the object to update.
      preconditions: Preconditions for the request.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only these Object metadata fields.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Updated object metadata.
    """
    raise NotImplementedError('PatchObjectMetadata must be overloaded')

  class DownloadStrategy(object):
    """Enum class for specifying download strategy."""
    ONE_SHOT = 'oneshot'
    RESUMABLE = 'resumable'

  # TODO: Change {de,en}cryption_tuple field names, as they don't actually
  # accept tuples.
  def GetObjectMedia(self,
                     bucket_name,
                     object_name,
                     download_stream,
                     provider=None,
                     generation=None,
                     object_size=None,
                     compressed_encoding=False,
                     download_strategy=DownloadStrategy.ONE_SHOT,
                     start_byte=0,
                     end_byte=None,
                     progress_callback=None,
                     serialization_data=None,
                     digesters=None,
                     decryption_tuple=None):
    """Gets object data.

    Args:
      bucket_name: Bucket containing the object.
      object_name: Object name.
      download_stream: Stream to send the object data to.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      generation: Generation of the object to retrieve.
      object_size: Total size of the object being downloaded.
      compressed_encoding: If true, object is stored with a compressed encoding.
      download_strategy: Cloud API download strategy to use for download.
      start_byte: Starting point for download (for resumable downloads and
                  range requests). Can be set to negative to request a range
                  of bytes (python equivalent of [:-3])
      end_byte: Ending byte number, inclusive, for download (for range
                requests). If None, download the rest of the object.
      progress_callback: Optional callback function for progress notifications.
                         Receives calls with arguments
                         (bytes_transferred, total_size).
      serialization_data: Implementation-specific JSON string of a dict
                          containing serialization information for the download.
      digesters: Dict of {string : digester}, where string is a name of a hash
                 algorithm, and digester is a validation digester that supports
                 update(bytes) and digest() using that algorithm.
                 Implementation can set the digester value to None to indicate
                 bytes were not successfully digested on-the-fly.
      decryption_tuple: Optional utils.encryption_helper.CryptoKeyWrapper for
                        decrypting an encrypted object.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Content-encoding string if it was detected that the server sent an encoded
      object during transfer, None otherwise.
    """
    raise NotImplementedError('GetObjectMedia must be overloaded')

  def UploadObject(self,
                   upload_stream,
                   object_metadata,
                   canned_acl=None,
                   size=None,
                   preconditions=None,
                   progress_callback=None,
                   encryption_tuple=None,
                   provider=None,
                   fields=None,
                   gzip_encoded=False):
    """Uploads object data and metadata.

    Args:
      upload_stream: Seekable stream of object data.
      object_metadata: Object metadata for new object.  Must include bucket
                       and object name.
      canned_acl: Optional canned ACL to apply to object. Overrides ACL set
                  in object_metadata.
      size: Optional object size.
      preconditions: Preconditions for the request.
      progress_callback: Optional callback function for progress notifications.
                         Receives calls with arguments
                         (bytes_transferred, total_size).
      encryption_tuple: Optional utils.encryption_helper.CryptoKeyWrapper for
                        encrypting the uploaded object.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only these Object metadata fields.
      gzip_encoded: Whether to use gzip transport encoding for the upload.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Object object for newly created destination object.
    """
    raise NotImplementedError('UploadObject must be overloaded')

  def UploadObjectStreaming(self,
                            upload_stream,
                            object_metadata,
                            canned_acl=None,
                            preconditions=None,
                            progress_callback=None,
                            encryption_tuple=None,
                            provider=None,
                            fields=None,
                            gzip_encoded=False):
    """Uploads object data and metadata.

    Args:
      upload_stream: Stream of object data. May not be seekable.
      object_metadata: Object metadata for new object.  Must include bucket
                       and object name.
      canned_acl: Optional canned ACL to apply to object. Overrides ACL set
                  in object_metadata.
      preconditions: Preconditions for the request.
      progress_callback: Optional callback function for progress notifications.
                         Receives calls with arguments
                         (bytes_transferred, total_size), but fills in only
                         bytes_transferred.
      encryption_tuple: Optional utils.encryption_helper.CryptoKeyWrapper for
                        encrypting the uploaded object.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only these Object metadata fields.
      gzip_encoded: Whether to use gzip transport encoding for the upload.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Object object for newly created destination object.
    """
    raise NotImplementedError('UploadObjectStreaming must be overloaded')

  def UploadObjectResumable(self,
                            upload_stream,
                            object_metadata,
                            canned_acl=None,
                            size=None,
                            preconditions=None,
                            serialization_data=None,
                            tracker_callback=None,
                            progress_callback=None,
                            encryption_tuple=None,
                            provider=None,
                            fields=None,
                            gzip_encoded=False):
    """Uploads object data and metadata using a resumable upload strategy.

    Args:
      upload_stream: Seekable stream of object data.
      object_metadata: Object metadata for new object.  Must include bucket
                       and object name.
      canned_acl: Optional canned ACL to apply to object. Overrides ACL set
                  in object_metadata.
      size: Total size of the object.
      preconditions: Preconditions for the request.
      serialization_data: Dict of {'url' : UploadURL} allowing for uploads to
                          be resumed.
      tracker_callback: Callback function taking a upload URL string.
                        Guaranteed to be called when the implementation gets an
                        upload URL, allowing the caller to resume the upload
                        across process breaks by saving the upload URL in
                        a tracker file.
      progress_callback: Optional callback function for progress notifications.
                         Receives calls with arguments
                         (bytes_transferred, total_size).
      encryption_tuple: Optional utils.encryption_helper.CryptoKeyWrapper for
                        encrypting the uploaded object.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only these Object metadata fields when the
              upload is complete.
      gzip_encoded: Whether to use gzip transport encoding for the upload.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Object object for newly created destination object.
    """
    raise NotImplementedError('UploadObjectResumable must be overloaded')

  # TODO: Change {de,en}cryption_tuple field names, as they don't actually
  # accept tuples.
  def CopyObject(self,
                 src_obj_metadata,
                 dst_obj_metadata,
                 src_generation=None,
                 canned_acl=None,
                 preconditions=None,
                 progress_callback=None,
                 max_bytes_per_call=None,
                 encryption_tuple=None,
                 decryption_tuple=None,
                 provider=None,
                 fields=None):
    """Copies an object in the cloud.

    Args:
      src_obj_metadata: Object metadata for source object.  Must include
                        bucket name, object name, and etag.
      dst_obj_metadata: Object metadata for new object.  Must include bucket
                        and object name.
      src_generation: Generation of the source object to copy.
      canned_acl: Optional canned ACL to apply to destination object. Overrides
                  ACL set in dst_obj_metadata.
      preconditions: Destination object preconditions for the request.
      progress_callback: Optional callback function for progress notifications.
                         Receives calls with arguments
                         (bytes_transferred, total_size).
      max_bytes_per_call: Integer describing maximum number of bytes
                          to rewrite per service call.
      encryption_tuple: Optional utils.encryption_helper.CryptoKeyWrapper for
                        encrypting the destination object.
      decryption_tuple: Optional utils.encryption_helper.CryptoKeyWrapper for
                        decrypting the source object. If supplied without
                        encryption_tuple, destination object will be written
                        without customer-supplied encryption.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only these Object metadata fields.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Object object for newly created destination object.
    """
    raise NotImplementedError('CopyObject must be overloaded')

  def ComposeObject(self,
                    src_objs_metadata,
                    dst_obj_metadata,
                    preconditions=None,
                    encryption_tuple=None,
                    provider=None,
                    fields=None):
    """Composes an object in the cloud.

    Args:
      src_objs_metadata: List of ComposeRequest.SourceObjectsValueListEntries
                         specifying the objects to compose.
      dst_obj_metadata: Metadata for the destination object including bucket
                        and object name.
      preconditions: Destination object preconditions for the request.
      encryption_tuple: Optional utils.encryption_helper.CryptoKeyWrapper for
                        decrypting source objects and encrypting the destination
                        object.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only these Object metadata fields.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Composed object metadata.
    """
    raise NotImplementedError('ComposeObject must be overloaded')

  def DeleteObject(self,
                   bucket_name,
                   object_name,
                   preconditions=None,
                   generation=None,
                   provider=None):
    """Deletes an object.

    Args:
      bucket_name: Name of the containing bucket.
      object_name: Name of the object to delete.
      preconditions: Preconditions for the request.
      generation: Generation (or version) of the object to delete; if None,
                  deletes the live object.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      None.
    """
    raise NotImplementedError('DeleteObject must be overloaded')

  def WatchBucket(self,
                  bucket_name,
                  address,
                  channel_id,
                  token=None,
                  provider=None,
                  fields=None):
    """Creates a notification subscription for changes to objects in a bucket.

    Args:
      bucket_name: Bucket containing the objects.
      address: Address to which to send notifications.
      channel_id: Unique ID string for the channel.
      token: If present, token string is delivered with each notification.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.
      fields: If present, return only these Channel metadata fields.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Channel object describing the notification subscription.
    """
    raise NotImplementedError('WatchBucket must be overloaded')

  def StopChannel(self, channel_id, resource_id, provider=None):
    """Stops a notification channel.

    Args:
      channel_id: Unique ID string for the channel.
      resource_id: Version-agnostic ID string for the channel.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      None.
    """
    raise NotImplementedError('StopChannel must be overloaded')

  def ListChannels(self, bucket_name, provider=None):
    """Lists object change notifications for a bucket.

    Args:
      bucket_name: Bucket containing the objects
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      None.
    """
    raise NotImplementedError('ListChannels must be overloaded')

  def GetProjectServiceAccount(self, project_number, provider=None):
    """Get the GCS-owned service account representing this project.

    Args:
      project_number: the project in question.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Service account object (with email_address string field)
    """
    raise NotImplementedError('GetProjectServiceAccount must be overloaded')

  def CreateNotificationConfig(self,
                               bucket_name,
                               pubsub_topic,
                               payload_format,
                               event_types=None,
                               custom_attributes=None,
                               object_name_prefix=None,
                               provider=None):
    """Creates a new notification with the specified parameters.

    Args:
      bucket_name: (Required) Name of the bucket.
      pubsub_topic: (Required) Cloud Pub/Sub topic to which to publish.
      payload_format: (Required) payload format, must be 'JSON' or 'NONE'.
      event_types: (Opt) List of event type filters, e.g. 'OBJECT_FINALIZE'.
      custom_attributes: (Opt) Dictionary of custom attributes.
      object_name_prefix: (Opt) Filter on object name.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Notification object describing new notificationConfig
    """
    raise NotImplementedError('CreateNotificationConfig must be overloaded')

  def DeleteNotificationConfig(self, bucket_name, notification, provider=None):
    """Deletes a notification.

    Args:
      bucket_name: (Required) Name of the bucket.
      notification: (Required) Integer name of the notification.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      None
    """
    raise NotImplementedError('DeleteNotificationConfig must be overloaded')

  def ListNotificationConfigs(self, bucket_name, provider=None):
    """Lists notification configs in a bucket.

    Args:
      bucket_name: Name of the bucket.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Yields:
      List of notification objects.
    """
    raise NotImplementedError('ListNotificationConfig must be overloaded')

  def CreateHmacKey(self, project_id, service_account_email):
    """Creates a new HMAC key for the specified service account.

    Args:
      project_id: Project ID owning the service account for which the key is to
                  be created.
      service_account_email: Email address of the service account for which to
                              create a key.

    Raises:
        NotImplementedError: not implemented TODO(tuckerkirven)

    Returns
      The key metadata and the secret key material.
    """
    raise NotImplementedError('CreateHmacKey must be overloaded')

  def DeleteHmacKey(self, project_id, access_id):
    """Deletes an HMAC key.

    Args:
      project_id: Project ID owning the requested key.
      access_id: Name of the HMAC key to be deleted.

    Raises:
        NotImplementedError: not implemented TODO(tuckerkirven)
    """
    raise NotImplementedError('DeleteHmacKey must be overloaded')

  def GetHmacKey(self, project_id, access_id):
    """Retrieves an HMAC key's metadata.

    Args:
      project_id: Project ID owning the service account of the requested key.
      access_id: Name of the HMAC key for which the metadata is being requested.

    Raises:
        NotImplementedError: not implemented TODO(tuckerkirven)

    Returns:
      Metadata for the specified key.
    """
    raise NotImplementedError('GetHmacKey must be overloaded')

  def ListHmacKeys(self,
                   project_id,
                   service_account_email,
                   show_deleted_keys=False):
    """Lists HMAC keys matching the criteria.

    Args:
        project_id: Name of the project from which to list HMAC keys.
        service_account_email: If present, only keys for the given service
                               account will be returned.
        show_deleted_keys: If set, show keys in the DELETED state.
    Raises:
        NotImplementedError: not implemented TODO(tuckerkirven)

    Yields:
      List of HMAC key metadata objects.
    """
    raise NotImplementedError('ListHmacKeys must be overloaded')

  def UpdateHmacKey(self, project_id, access_id, state, etag):
    """Updates the state of an HMAC key.

    Args:
      project_id: Project ID owning the service account of the updated key.
      access_id: Name of the HMAC key being updated.
      state: The state to which the key should be updated.
      etag: None or a string matching the key's etag to ensure the appropriate
            version of the key is updated.

    Raises:
        NotImplementedError: not implemented TODO(tuckerkirven)

    Returns:
        The updated key metadata.
    """
    raise NotImplementedError('UpdateHmacKey must be overloaded')


class Preconditions(object):
  """Preconditions class for specifying preconditions to cloud API requests."""

  def __init__(self, gen_match=None, meta_gen_match=None):
    """Instantiates a Preconditions object.

    Args:
      gen_match: Perform request only if generation of target object
                 matches the given integer. Ignored for bucket requests.
      meta_gen_match: Perform request only if metageneration of target
                      object/bucket matches the given integer.
    """
    self.gen_match = gen_match
    self.meta_gen_match = meta_gen_match


class EncryptionException(Exception):
  """Exception raised when an encrypted resource cannot be decrypted."""


class ArgumentException(Exception):
  """Exception raised when arguments to a Cloud API method are invalid.

    This exception is never raised as a result of a failed call to a cloud
    storage provider.
  """

  def __init__(self, reason):
    Exception.__init__(self)
    self.reason = reason

  def __repr__(self):
    return str(self)

  def __str__(self):
    return '%s: %s' % (self.__class__.__name__, self.reason)


class ProjectIdException(ArgumentException):
  """Exception raised when a Project ID argument is required but not present."""


class ServiceException(Exception):
  """Exception raised when a cloud storage provider request fails.

    This exception is raised only as a result of a failed remote call.
  """

  def __init__(self, reason, status=None, body=None):
    Exception.__init__(self)
    self.reason = reason
    self.status = status
    self.body = body

  def __repr__(self):
    return str(self)

  def __str__(self):
    message = '%s:' % self.__class__.__name__
    if self.status:
      message += ' %s' % self.status
    message += ' %s' % self.reason
    if self.body:
      message += '\n%s' % self.body
    return message


class RetryableServiceException(ServiceException):
  """Exception class for retryable exceptions."""


class ResumableDownloadException(RetryableServiceException):
  """Exception raised for res. downloads that can be retried later."""


class ResumableUploadException(RetryableServiceException):
  """Exception raised for res. uploads that can be retried w/ same upload ID."""


class ResumableUploadStartOverException(RetryableServiceException):
  """Exception raised for res. uploads that can be retried w/ new upload ID."""


class ResumableUploadAbortException(ServiceException):
  """Exception raised for resumable uploads that cannot be retried later."""


class AuthenticationException(ServiceException):
  """Exception raised for errors during the authentication process."""


class PreconditionException(ServiceException):
  """Exception raised for precondition failures."""


class NotFoundException(ServiceException):
  """Exception raised when a resource is not found (404)."""


class BucketNotFoundException(NotFoundException):
  """Exception raised when a bucket resource is not found (404)."""

  def __init__(self, reason, bucket_name, status=None, body=None):
    super(BucketNotFoundException, self).__init__(reason,
                                                  status=status,
                                                  body=body)
    self.bucket_name = bucket_name


class NotEmptyException(ServiceException):
  """Exception raised when trying to delete a bucket is not empty."""


class BadRequestException(ServiceException):
  """Exception raised for malformed requests.

    Where it is possible to detect invalid arguments prior to sending them
    to the server, an ArgumentException should be raised instead.
  """


class AccessDeniedException(ServiceException):
  """Exception raised  when authenticated user has insufficient access rights.

    This is raised when the authentication process succeeded but the
    authenticated user does not have access rights to the requested resource.
  """


class PublishPermissionDeniedException(ServiceException):
  """Exception raised when bucket does not have publish permission to a topic.

    This is raised when a custom attempts to set up a notification config to a
    Cloud Pub/Sub topic, but their GCS bucket does not have permission to
    publish to the specified topic.
  """

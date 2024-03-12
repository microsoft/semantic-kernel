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
"""Gsutil API delegator for interacting with cloud storage providers."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import boto
from boto import config
from gslib import context_config
from gslib.cloud_api import ArgumentException
from gslib.cloud_api import CloudApi
from gslib.cs_api_map import ApiMapConstants
from gslib.cs_api_map import ApiSelector
from gslib.exception import CommandException
from gslib.utils import boto_util


class CloudApiDelegator(CloudApi):
  """Class that handles delegating requests to gsutil Cloud API implementations.

  This class is responsible for determining at runtime which gsutil Cloud API
  implementation should service the request based on the Cloud storage provider,
  command-level API support, and configuration file override.

  During initialization it takes as an argument a gsutil_api_map which maps
  providers to their default and supported gsutil Cloud API implementations
  (see comments in cs_api_map for details).

  Instantiation of multiple delegators per-thread is required for multiprocess
  and/or multithreaded operations. Calling methods on the same delegator in
  multiple threads is unsafe.
  """

  def __init__(self,
               bucket_storage_uri_class,
               gsutil_api_map,
               logger,
               status_queue,
               provider=None,
               debug=0,
               http_headers=None,
               trace_token=None,
               perf_trace_token=None,
               user_project=None):
    """Performs necessary setup for delegating cloud storage requests.

    This function has different arguments than the gsutil Cloud API __init__
    function because of the delegation responsibilties of this class.

    Args:
      bucket_storage_uri_class: boto storage_uri class, used by APIs that
                                provide boto translation or mocking.
      gsutil_api_map: Map of providers and API selector tuples to api classes
                      which can be used to communicate with those providers.
      logger: logging.logger for outputting log messages.
      status_queue: Queue for relaying status to UI.
      provider: Default provider prefix describing cloud storage provider to
                connect to.
      debug: Debug level for the API implementation (0..3).
      http_headers (dict|None): Arbitrary headers to be included in every request.
      trace_token: Apiary trace token to pass to API.
      perf_trace_token: Performance trace token to use when making API calls.
      user_project: Project to be billed for this project.
    """
    super(CloudApiDelegator, self).__init__(bucket_storage_uri_class,
                                            logger,
                                            status_queue,
                                            provider=provider,
                                            debug=debug,
                                            http_headers=http_headers,
                                            trace_token=trace_token,
                                            perf_trace_token=perf_trace_token,
                                            user_project=user_project)
    self.api_map = gsutil_api_map
    self.prefer_api = boto.config.get('GSUtil', 'prefer_api', '').upper()
    self.loaded_apis = {}

    if not self.api_map[ApiMapConstants.API_MAP]:
      raise ArgumentException('No apiclass supplied for gsutil Cloud API map.')

  def _GetApi(self, provider):
    """Returns a valid CloudApi for use by the caller.

    This function lazy-loads connection and credentials using the API map
    and credential store provided during class initialization.

    Args:
      provider: Provider to load API for. If None, class-wide default is used.

    Raises:
      ArgumentException if there is no matching API available in the API map.

    Returns:
      Valid API instance that can be used to communicate with the Cloud
      Storage provider.
    """
    provider = provider or self.provider
    if not provider:
      raise ArgumentException('No provider selected for _GetApi')

    provider = str(provider)
    if provider not in self.loaded_apis:
      self.loaded_apis[provider] = {}

    api_selector = self.GetApiSelector(provider)
    if api_selector not in self.loaded_apis[provider]:
      # Need to load the API.
      self._LoadApi(provider, api_selector)
    return self.loaded_apis[provider][api_selector]

  def _LoadApi(self, provider, api_selector):
    """Loads a CloudApi into the loaded_apis map for this class.

    Args:
      provider: Provider to load the API for.
      api_selector: cs_api_map.ApiSelector defining the API type.
    """
    if provider not in self.api_map[ApiMapConstants.API_MAP]:
      raise ArgumentException(
          'gsutil Cloud API map contains no entry for provider %s.' % provider)
    if api_selector not in self.api_map[ApiMapConstants.API_MAP][provider]:
      raise ArgumentException(
          'gsutil Cloud API map does not support API %s for provider %s.' %
          (api_selector, provider))
    self.loaded_apis[provider][api_selector] = (
        self.api_map[ApiMapConstants.API_MAP][provider][api_selector](
            self.bucket_storage_uri_class,
            self.logger,
            self.status_queue,
            provider=provider,
            debug=self.debug,
            http_headers=self.http_headers,
            trace_token=self.trace_token,
            perf_trace_token=self.perf_trace_token,
            user_project=self.user_project))

  def GetApiSelector(self, provider=None):
    """Returns a cs_api_map.ApiSelector based on input and configuration.

    Args:
      provider: Provider to return the ApiSelector for.  If None, class-wide
                default is used.

    Returns:
      cs_api_map.ApiSelector that will be used for calls to the delegator
      for this provider.
    """
    selected_provider = provider or self.provider
    if not selected_provider:
      raise ArgumentException('No provider selected for CloudApi')

    if (selected_provider not in self.api_map[ApiMapConstants.DEFAULT_MAP] or
        self.api_map[ApiMapConstants.DEFAULT_MAP][selected_provider]
        not in self.api_map[ApiMapConstants.API_MAP][selected_provider]):
      raise ArgumentException('No default api available for provider %s' %
                              selected_provider)

    if selected_provider not in self.api_map[ApiMapConstants.SUPPORT_MAP]:
      raise ArgumentException('No supported apis available for provider %s' %
                              selected_provider)

    api = self.api_map[ApiMapConstants.DEFAULT_MAP][selected_provider]

    using_gs_hmac = provider == 'gs' and boto_util.UsingGsHmac()

    configured_encryption = (provider == 'gs' and
                             (config.has_option('GSUtil', 'encryption_key') or
                              config.has_option('GSUtil', 'decryption_key1')))

    if using_gs_hmac and configured_encryption:
      raise CommandException(
          'gsutil does not support HMAC credentials with customer-supplied '
          'encryption keys (CSEK) or customer-managed KMS encryption keys '
          '(CMEK). Please generate and include non-HMAC credentials '
          'in your .boto configuration file, or to access public encrypted '
          'objects, remove your HMAC credentials.')
    # If we have only HMAC credentials for Google Cloud Storage, we must use
    # the XML API as the JSON API does not support HMAC.
    #
    # Technically if we have only HMAC credentials, we should still be able to
    # access public read resources via the JSON API, but the XML API can do
    # that just as well. It is better to use it than inspect the credentials on
    # every HTTP call.
    elif using_gs_hmac:
      api = ApiSelector.XML
    # CSEK and CMEK encryption keys are currently only supported in the
    # JSON API implementation (GcsJsonApi). We can't stop XML API users from
    # interacting with encrypted objects, since we don't know the object is
    # encrypted until after the API call is made, but if they specify
    # configuration values we will use JSON.
    elif configured_encryption:
      api = ApiSelector.JSON
    # Try to force the user's preference to a supported API.
    elif self.prefer_api in (
        self.api_map[ApiMapConstants.SUPPORT_MAP][selected_provider]):
      api = self.prefer_api

    if (api == ApiSelector.XML and context_config.get_context_config() and
        context_config.get_context_config().use_client_certificate):
      raise ArgumentException(
          'User enabled mTLS by setting "use_client_certificate", but mTLS'
          ' is not supported for the selected XML API. Try configuring for '
          ' the GCS JSON API or setting "use_client_certificate" to "False" in'
          ' the Boto config.')

    return api

  def GetServiceAccountId(self, provider=None):
    return self._GetApi(provider).GetServiceAccountId()

  # For function docstrings, see CloudApi class.
  def GetBucket(self, bucket_name, provider=None, fields=None):
    return self._GetApi(provider).GetBucket(bucket_name, fields=fields)

  def GetBucketIamPolicy(self, bucket_name, provider=None, fields=None):
    return self._GetApi(provider).GetBucketIamPolicy(bucket_name, fields=fields)

  def SetBucketIamPolicy(self, bucket_name, policy, provider=None):
    return self._GetApi(provider).SetBucketIamPolicy(bucket_name, policy)

  def ListBuckets(self, project_id=None, provider=None, fields=None):
    return self._GetApi(provider).ListBuckets(project_id=project_id,
                                              fields=fields)

  def PatchBucket(self,
                  bucket_name,
                  metadata,
                  canned_acl=None,
                  canned_def_acl=None,
                  preconditions=None,
                  provider=None,
                  fields=None):
    return self._GetApi(provider).PatchBucket(bucket_name,
                                              metadata,
                                              canned_acl=canned_acl,
                                              canned_def_acl=canned_def_acl,
                                              preconditions=preconditions,
                                              fields=fields)

  def LockRetentionPolicy(self, bucket_name, metageneration, provider=None):
    return self._GetApi(provider).LockRetentionPolicy(bucket_name,
                                                      metageneration,
                                                      provider=provider)

  def CreateBucket(self,
                   bucket_name,
                   project_id=None,
                   metadata=None,
                   provider=None,
                   fields=None):
    return self._GetApi(provider).CreateBucket(bucket_name,
                                               project_id=project_id,
                                               metadata=metadata,
                                               fields=fields)

  def DeleteBucket(self, bucket_name, preconditions=None, provider=None):
    return self._GetApi(provider).DeleteBucket(bucket_name,
                                               preconditions=preconditions)

  def GetObjectIamPolicy(self,
                         bucket_name,
                         object_name,
                         generation=None,
                         provider=None,
                         fields=None):
    return self._GetApi(provider).GetObjectIamPolicy(bucket_name,
                                                     object_name,
                                                     generation,
                                                     fields=fields)

  def SetObjectIamPolicy(self,
                         bucket_name,
                         object_name,
                         policy,
                         generation=None,
                         provider=None):
    return self._GetApi(provider).SetObjectIamPolicy(bucket_name, object_name,
                                                     policy, generation)

  def ListObjects(self,
                  bucket_name,
                  prefix=None,
                  delimiter=None,
                  all_versions=None,
                  provider=None,
                  fields=None):
    return self._GetApi(provider).ListObjects(bucket_name,
                                              prefix=prefix,
                                              delimiter=delimiter,
                                              all_versions=all_versions,
                                              fields=fields)

  def GetObjectMetadata(self,
                        bucket_name,
                        object_name,
                        generation=None,
                        provider=None,
                        fields=None):
    return self._GetApi(provider).GetObjectMetadata(bucket_name,
                                                    object_name,
                                                    generation=generation,
                                                    fields=fields)

  def PatchObjectMetadata(self,
                          bucket_name,
                          object_name,
                          metadata,
                          canned_acl=None,
                          generation=None,
                          preconditions=None,
                          provider=None,
                          fields=None):
    return self._GetApi(provider).PatchObjectMetadata(
        bucket_name,
        object_name,
        metadata,
        canned_acl=canned_acl,
        generation=generation,
        preconditions=preconditions,
        fields=fields)

  def GetObjectMedia(self,
                     bucket_name,
                     object_name,
                     download_stream,
                     provider=None,
                     generation=None,
                     object_size=None,
                     compressed_encoding=False,
                     download_strategy=CloudApi.DownloadStrategy.ONE_SHOT,
                     start_byte=0,
                     end_byte=None,
                     progress_callback=None,
                     serialization_data=None,
                     digesters=None,
                     decryption_tuple=None):
    return self._GetApi(provider).GetObjectMedia(
        bucket_name,
        object_name,
        download_stream,
        compressed_encoding=compressed_encoding,
        download_strategy=download_strategy,
        start_byte=start_byte,
        end_byte=end_byte,
        generation=generation,
        object_size=object_size,
        progress_callback=progress_callback,
        serialization_data=serialization_data,
        digesters=digesters,
        decryption_tuple=decryption_tuple)

  def UploadObject(self,
                   upload_stream,
                   object_metadata,
                   size=None,
                   canned_acl=None,
                   preconditions=None,
                   progress_callback=None,
                   encryption_tuple=None,
                   provider=None,
                   fields=None,
                   gzip_encoded=False):
    return self._GetApi(provider).UploadObject(
        upload_stream,
        object_metadata,
        size=size,
        canned_acl=canned_acl,
        preconditions=preconditions,
        progress_callback=progress_callback,
        encryption_tuple=encryption_tuple,
        fields=fields,
        gzip_encoded=gzip_encoded)

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
    return self._GetApi(provider).UploadObjectStreaming(
        upload_stream,
        object_metadata,
        canned_acl=canned_acl,
        preconditions=preconditions,
        progress_callback=progress_callback,
        encryption_tuple=encryption_tuple,
        fields=fields,
        gzip_encoded=gzip_encoded)

  def UploadObjectResumable(self,
                            upload_stream,
                            object_metadata,
                            canned_acl=None,
                            preconditions=None,
                            size=None,
                            serialization_data=None,
                            tracker_callback=None,
                            progress_callback=None,
                            encryption_tuple=None,
                            provider=None,
                            fields=None,
                            gzip_encoded=False):
    return self._GetApi(provider).UploadObjectResumable(
        upload_stream,
        object_metadata,
        canned_acl=canned_acl,
        preconditions=preconditions,
        size=size,
        serialization_data=serialization_data,
        tracker_callback=tracker_callback,
        progress_callback=progress_callback,
        encryption_tuple=encryption_tuple,
        fields=fields,
        gzip_encoded=gzip_encoded)

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
    return self._GetApi(provider).CopyObject(
        src_obj_metadata,
        dst_obj_metadata,
        src_generation=src_generation,
        canned_acl=canned_acl,
        preconditions=preconditions,
        progress_callback=progress_callback,
        max_bytes_per_call=max_bytes_per_call,
        encryption_tuple=encryption_tuple,
        decryption_tuple=decryption_tuple,
        fields=fields)

  def ComposeObject(self,
                    src_objs_metadata,
                    dst_obj_metadata,
                    preconditions=None,
                    encryption_tuple=None,
                    provider=None,
                    fields=None):
    return self._GetApi(provider).ComposeObject(
        src_objs_metadata,
        dst_obj_metadata,
        preconditions=preconditions,
        encryption_tuple=encryption_tuple,
        fields=fields)

  def DeleteObject(self,
                   bucket_name,
                   object_name,
                   preconditions=None,
                   generation=None,
                   provider=None):
    return self._GetApi(provider).DeleteObject(bucket_name,
                                               object_name,
                                               preconditions=preconditions,
                                               generation=generation)

  def WatchBucket(self,
                  bucket_name,
                  address,
                  channel_id,
                  token=None,
                  provider=None,
                  fields=None):
    return self._GetApi(provider).WatchBucket(bucket_name,
                                              address,
                                              channel_id,
                                              token=token,
                                              fields=fields)

  def StopChannel(self, channel_id, resource_id, provider=None):
    return self._GetApi(provider).StopChannel(channel_id, resource_id)

  def ListChannels(self, bucket_name, provider=None):
    return self._GetApi(provider).ListChannels(bucket_name)

  def GetProjectServiceAccount(self, project_number, provider=None):
    return self._GetApi(provider).GetProjectServiceAccount(project_number)

  def CreateNotificationConfig(self,
                               bucket_name,
                               pubsub_topic,
                               payload_format,
                               event_types=None,
                               custom_attributes=None,
                               object_name_prefix=None,
                               provider=None):
    return self._GetApi(provider).CreateNotificationConfig(
        bucket_name, pubsub_topic, payload_format, event_types,
        custom_attributes, object_name_prefix)

  def DeleteNotificationConfig(self, bucket_name, notification, provider=None):
    return self._GetApi(provider).DeleteNotificationConfig(
        bucket_name, notification)

  def ListNotificationConfigs(self, bucket_name, provider=None):
    return self._GetApi(provider).ListNotificationConfigs(bucket_name)

  def ListBucketAccessControls(self, bucket_name, provider=None):
    return self._GetApi(provider).ListBucketAccessControls(bucket_name)

  def ListObjectAccessControls(self, bucket_name, object_name, provider=None):
    return self._GetApi(provider).ListObjectAccessControls(
        bucket_name, object_name)

  def CreateHmacKey(self, project_id, service_account_email, provider=None):
    return self._GetApi(provider).CreateHmacKey(project_id,
                                                service_account_email)

  def DeleteHmacKey(self, project_id, access_id, provider=None):
    return self._GetApi(provider).DeleteHmacKey(project_id, access_id)

  def GetHmacKey(self, project_id, access_id, provider=None):
    return self._GetApi(provider).GetHmacKey(project_id, access_id)

  def ListHmacKeys(self,
                   project_id,
                   service_account_email,
                   show_deleted_keys=False,
                   provider=None):
    return self._GetApi(provider).ListHmacKeys(project_id,
                                               service_account_email,
                                               show_deleted_keys)

  def SignUrl(self, provider, method, duration, path, generation, logger,
              region, signed_headers, string_to_sign_debug):
    return self._GetApi(provider).SignUrl(
        method=method,
        duration=duration,
        path=path,
        generation=generation,
        logger=logger,
        region=region,
        signed_headers=signed_headers,
        string_to_sign_debug=string_to_sign_debug)

  def UpdateHmacKey(self, project_id, access_id, state, etag, provider=None):
    return self._GetApi(provider).UpdateHmacKey(project_id, access_id, state,
                                                etag)

  def XmlPassThroughGetAcl(self, storage_url, def_obj_acl=False, provider=None):
    """XML compatibility function for getting ACLs.

    Args:
      storage_url: StorageUrl object.
      def_obj_acl: If true, get the default object ACL on a bucket.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      ACL XML for the resource specified by storage_url.
    """
    return self._GetApi(provider).XmlPassThroughGetAcl(storage_url,
                                                       def_obj_acl=def_obj_acl)

  def XmlPassThroughSetAcl(self,
                           acl_text,
                           storage_url,
                           canned=True,
                           def_obj_acl=False,
                           provider=None):
    """XML compatibility function for setting ACLs.

    Args:
      acl_text: XML ACL or canned ACL string.
      storage_url: StorageUrl object.
      canned: If true, acl_text is treated as a canned ACL string.
      def_obj_acl: If true, set the default object ACL on a bucket.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      None.
    """
    self._GetApi(provider).XmlPassThroughSetAcl(acl_text,
                                                storage_url,
                                                canned=canned,
                                                def_obj_acl=def_obj_acl)

  def XmlPassThroughGetCors(self, storage_url, provider=None):
    """XML compatibility function for getting CORS configuration on a bucket.

    Args:
      storage_url: StorageUrl object.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      CORS configuration XML for the bucket specified by storage_url.
    """
    return self._GetApi(provider).XmlPassThroughGetCors(storage_url)

  def XmlPassThroughSetCors(self, cors_text, storage_url, provider=None):
    """XML compatibility function for setting CORS configuration on a bucket.

    Args:
      cors_text: Raw CORS XML string.
      storage_url: StorageUrl object.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      None.
    """
    self._GetApi(provider).XmlPassThroughSetCors(cors_text, storage_url)

  def XmlPassThroughGetLifecycle(self, storage_url, provider=None):
    """XML compatibility function for getting lifecycle config on a bucket.

    Args:
      storage_url: StorageUrl object.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Lifecycle configuration XML for the bucket specified by storage_url.
    """
    return self._GetApi(provider).XmlPassThroughGetLifecycle(storage_url)

  def XmlPassThroughSetLifecycle(self,
                                 lifecycle_text,
                                 storage_url,
                                 provider=None):
    """XML compatibility function for setting lifecycle config on a bucket.

    Args:
      lifecycle_text: Raw lifecycle configuration XML string.
      storage_url: StorageUrl object.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      None.
    """
    self._GetApi(provider).XmlPassThroughSetLifecycle(lifecycle_text,
                                                      storage_url)

  def XmlPassThroughGetLogging(self, storage_url, provider=None):
    """XML compatibility function for getting logging configuration on a bucket.

    Args:
      storage_url: StorageUrl object.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Logging configuration XML for the bucket specified by storage_url.
    """
    return self._GetApi(provider).XmlPassThroughGetLogging(storage_url)

  def XmlPassThroughSetTagging(self, tags_text, storage_url, provider=None):
    """XML compatibility function for setting tagging configuration on a bucket.

    This passthrough provides support for setting a tagging configuration
    (equivalent to a label configuration) on a cloud bucket.

    Args:
      tags_text: Raw tagging configuration XML string.
      storage_url: StorageUrl object.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      None.
    """
    return self._GetApi(provider).XmlPassThroughSetTagging(
        tags_text, storage_url)

  def XmlPassThroughGetTagging(self, storage_url, provider=None):
    """XML compatibility function for getting tagging configuration on a bucket.

    Args:
      storage_url: StorageUrl object.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Tagging configuration XML for the bucket specified by storage_url.
    """
    return self._GetApi(provider).XmlPassThroughGetTagging(storage_url)

  def XmlPassThroughGetWebsite(self, storage_url, provider=None):
    """XML compatibility function for getting website configuration on a bucket.

    Args:
      storage_url: StorageUrl object.
      provider: Cloud storage provider to connect to.  If not present,
                class-wide default is used.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      Website configuration XML for the bucket specified by storage_url.
    """
    return self._GetApi(provider).XmlPassThroughGetWebsite(storage_url)

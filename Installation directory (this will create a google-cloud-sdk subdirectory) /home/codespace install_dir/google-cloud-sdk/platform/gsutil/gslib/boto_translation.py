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
"""XML/boto gsutil Cloud API implementation for GCS and Amazon S3."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import base64
import binascii
import datetime
import errno
import json
import os
import pickle
import random
import re
import socket
import tempfile
import textwrap
import threading
import time
import xml
from xml.dom.minidom import parseString as XmlParseString
from xml.sax import _exceptions as SaxExceptions

import six
from six.moves import http_client
import boto
from boto import config
from boto import handler
from boto.gs.cors import Cors
from boto.gs.lifecycle import LifecycleConfig
from boto.s3.cors import CORSConfiguration as S3Cors
from boto.s3.deletemarker import DeleteMarker
from boto.s3.lifecycle import Lifecycle as S3Lifecycle
from boto.s3.prefix import Prefix
from boto.s3.tagging import Tags
import boto.exception
import boto.utils
from gslib.boto_resumable_upload import BotoResumableUpload
from gslib.cloud_api import AccessDeniedException
from gslib.cloud_api import ArgumentException
from gslib.cloud_api import BadRequestException
from gslib.cloud_api import CloudApi
from gslib.cloud_api import NotEmptyException
from gslib.cloud_api import NotFoundException
from gslib.cloud_api import PreconditionException
from gslib.cloud_api import ResumableDownloadException
from gslib.cloud_api import ResumableUploadAbortException
from gslib.cloud_api import ResumableUploadException
from gslib.cloud_api import ResumableUploadStartOverException
from gslib.cloud_api import ServiceException
# Imported for boto AuthHandler purposes.
import gslib.devshell_auth_plugin  # pylint: disable=unused-import
from gslib.exception import CommandException
from gslib.exception import InvalidUrlError
from gslib.project_id import GOOG_PROJ_ID_HDR
from gslib.project_id import PopulateProjectId
from gslib.storage_url import GenerationFromUrlAndString
from gslib.storage_url import StorageUrlFromString
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.utils import parallelism_framework_util
from gslib.utils.boto_util import ConfigureNoOpAuthIfNeeded
from gslib.utils.boto_util import GetMaxRetryDelay
from gslib.utils.boto_util import GetNumRetries
from gslib.utils.cloud_api_helper import ListToGetFields
from gslib.utils.cloud_api_helper import ValidateDstObjectMetadata
from gslib.utils.constants import DEFAULT_FILE_BUFFER_SIZE
from gslib.utils.constants import REQUEST_REASON_ENV_VAR
from gslib.utils.constants import REQUEST_REASON_HEADER_KEY
from gslib.utils.constants import S3_DELETE_MARKER_GUID
from gslib.utils.constants import UTF8
from gslib.utils.constants import XML_PROGRESS_CALLBACKS
from gslib.utils.hashing_helper import Base64EncodeHash
from gslib.utils.hashing_helper import Base64ToHexHash
from gslib.utils.metadata_util import AddAcceptEncodingGzipIfNeeded
from gslib.utils.parallelism_framework_util import multiprocessing_context
from gslib.utils.text_util import EncodeStringAsLong
from gslib.utils.translation_helper import AclTranslation
from gslib.utils.translation_helper import AddS3MarkerAclToObjectMetadata
from gslib.utils.translation_helper import CorsTranslation
from gslib.utils.translation_helper import CreateBucketNotFoundException
from gslib.utils.translation_helper import CreateNotFoundExceptionForObjectWrite
from gslib.utils.translation_helper import CreateObjectNotFoundException
from gslib.utils.translation_helper import DEFAULT_CONTENT_TYPE
from gslib.utils.translation_helper import HeadersFromObjectMetadata
from gslib.utils.translation_helper import LabelTranslation
from gslib.utils.translation_helper import LifecycleTranslation
from gslib.utils.translation_helper import REMOVE_CORS_CONFIG
from gslib.utils.translation_helper import S3MarkerAclFromObjectMetadata
from gslib.utils.translation_helper import UnaryDictToXml
from gslib.utils.unit_util import TWO_MIB

if six.PY3:
  long = int

TRANSLATABLE_BOTO_EXCEPTIONS = (boto.exception.BotoServerError,
                                boto.exception.InvalidUriError,
                                boto.exception.ResumableDownloadException,
                                boto.exception.ResumableUploadException,
                                boto.exception.StorageCreateError,
                                boto.exception.StorageResponseError)

# pylint: disable=global-at-module-level
global boto_auth_initialized, boto_auth_initialized_lock
# If multiprocessing is available, these will be overridden to process-safe
# variables in InitializeMultiprocessingVariables.
boto_auth_initialized_lock = threading.Lock()
boto_auth_initialized = False

NON_EXISTENT_OBJECT_REGEX = re.compile(r'.*non-\s*existent\s*object',
                                       flags=re.DOTALL)
# Determines whether an etag is a valid MD5.
MD5_REGEX = re.compile(r'^"*[a-fA-F0-9]{32}"*$')


def _AddCustomEndpointToKey(key):
  """Update Boto Key object with user config's custom endpoint."""
  user_setting_to_key_attribute = {
      'gs_host': 'host',
      'gs_port': 'port',
      'gs_host_header': 'host_header',
  }
  for user_setting, key_attribute in user_setting_to_key_attribute.items():
    user_setting_value = config.get('Credentials', user_setting, None)
    if user_setting_value is not None:
      setattr(key.bucket.connection, key_attribute, user_setting_value)


def InitializeMultiprocessingVariables():  # pylint: disable=invalid-name
  """Perform necessary initialization for multiprocessing.

    See gslib.command.InitializeMultiprocessingVariables for an explanation
    of why this is necessary.
  """
  # pylint: disable=global-variable-undefined
  global boto_auth_initialized, boto_auth_initialized_lock
  boto_auth_initialized_lock = parallelism_framework_util.CreateLock()
  boto_auth_initialized = multiprocessing_context.Value('i', 0)


class DownloadProxyCallbackHandler(object):
  """Intermediary callback to keep track of the number of bytes downloaded."""

  def __init__(self, start_byte, callback):
    self._start_byte = start_byte
    self._callback = callback

  def call(self, bytes_downloaded, total_size):
    """Saves necessary data and then calls the given Cloud API callback.

    Args:
      bytes_downloaded: Number of bytes processed so far.
      total_size: Total size of the ongoing operation.
    """
    if self._callback:
      self._callback(self._start_byte + bytes_downloaded, total_size)


class BotoTranslation(CloudApi):
  """Boto-based XML translation implementation of gsutil Cloud API.

  This class takes gsutil Cloud API objects, translates them to XML service
  calls, and translates the results back into gsutil Cloud API objects for
  use by the caller.

  This class does not support encryption and ignores encryption and decryption
  parameters. Behavior when encountering encrypted objects is undefined.
  TODO: Implement support.

  This class does not support handling a Requester Pays user project for
  billing, and any given user project will be ignored.
  TODO: Support user_project.
  """

  def __init__(self,
               bucket_storage_uri_class,
               logger,
               status_queue,
               provider=None,
               credentials=None,
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
      provider: Provider prefix describing cloud storage provider to connect to.
                'gs' and 's3' are supported. Function implementations ignore
                the provider argument and use this one instead.
      credentials: Unused.
      debug: Debug level for the API implementation (0..3).
      http_headers (dict|None): Arbitrary headers to be included in every request. 
      trace_token: Unused in this subclass.
      perf_trace_token: Performance trace token to use when making API calls
          ('gs' provider only).
      user_project: Unused in this subclass
    """
    super(BotoTranslation, self).__init__(bucket_storage_uri_class,
                                          logger,
                                          status_queue,
                                          provider=provider,
                                          debug=debug,
                                          http_headers=http_headers,
                                          trace_token=trace_token,
                                          perf_trace_token=perf_trace_token)
    _ = credentials
    # pylint: disable=global-variable-undefined, global-variable-not-assigned
    global boto_auth_initialized, boto_auth_initialized_lock
    with boto_auth_initialized_lock:
      ConfigureNoOpAuthIfNeeded()
      if isinstance(boto_auth_initialized, bool):
        boto_auth_initialized = True
      else:
        boto_auth_initialized.value = 1
    self.api_version = boto.config.get_value('GSUtil', 'default_api_version',
                                             '1')

  def GetServiceAccountId(self):
    """Service account credentials unused for S3."""
    return None

  def GetBucket(self, bucket_name, provider=None, fields=None):
    """See CloudApi class for function doc strings."""
    _ = provider
    bucket_uri = self._StorageUriForBucket(bucket_name)
    headers = self._CreateBaseHeaders()
    try:
      return self._BotoBucketToBucket(bucket_uri.get_bucket(validate=True,
                                                            headers=headers),
                                      fields=fields)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

  def ListBuckets(self, project_id=None, provider=None, fields=None):
    """See CloudApi class for function doc strings."""
    _ = provider
    get_fields = ListToGetFields(list_fields=fields)
    headers = self._CreateBaseHeaders()
    if self.provider == 'gs':
      headers[GOOG_PROJ_ID_HDR] = PopulateProjectId(project_id)
    try:
      provider_uri = boto.storage_uri(
          '%s://' % self.provider,
          suppress_consec_slashes=False,
          bucket_storage_uri_class=self.bucket_storage_uri_class,
          debug=self.debug)

      buckets_iter = provider_uri.get_all_buckets(headers=headers)
      for bucket in buckets_iter:
        if self.provider == 's3' and bucket.name.lower() != bucket.name:
          # S3 listings can return buckets with upper-case names, but boto
          # can't successfully call them.
          continue
        yield self._BotoBucketToBucket(bucket, fields=get_fields)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def PatchBucket(self,
                  bucket_name,
                  metadata,
                  canned_acl=None,
                  canned_def_acl=None,
                  preconditions=None,
                  provider=None,
                  fields=None):
    """See CloudApi class for function doc strings."""
    _ = provider
    bucket_uri = self._StorageUriForBucket(bucket_name)
    headers = self._CreateBaseHeaders()
    self._AddPreconditionsToHeaders(preconditions, headers)
    try:
      if metadata.acl:
        boto_acl = AclTranslation.BotoAclFromMessage(metadata.acl)
        bucket_uri.set_xml_acl(boto_acl.to_xml(), headers=headers)
      if canned_acl:
        canned_acls = bucket_uri.canned_acls()
        if canned_acl not in canned_acls:
          raise CommandException('Invalid canned ACL "%s".' % canned_acl)
        bucket_uri.set_acl(canned_acl, bucket_uri.object_name, headers=headers)
      if canned_def_acl:
        canned_acls = bucket_uri.canned_acls()
        if canned_def_acl not in canned_acls:
          raise CommandException('Invalid canned ACL "%s".' % canned_def_acl)
        bucket_uri.set_def_acl(canned_def_acl,
                               bucket_uri.object_name,
                               headers=headers)
      if metadata.cors:
        if metadata.cors == REMOVE_CORS_CONFIG:
          metadata.cors = []
        boto_cors = CorsTranslation.BotoCorsFromMessage(metadata.cors)
        bucket_uri.set_cors(boto_cors, False, headers=headers)
      if metadata.defaultObjectAcl:
        boto_acl = AclTranslation.BotoAclFromMessage(metadata.defaultObjectAcl)
        bucket_uri.set_def_xml_acl(boto_acl.to_xml(), headers=headers)
      if metadata.labels:
        boto_tags = LabelTranslation.BotoTagsFromMessage(metadata.labels)
        # TODO: Define tags-related methods on storage_uri objects. The set_tags
        # method raises an exception if the response differs from the style of
        # S3, which uses a 204 response code upon success. That method
        # should be okay with a 200 instead of a 204 for GS responses. In the
        # meantime, we invoke the underlying bucket's methods directly and
        # bypass manually raised exceptions from 200 responses.
        try:
          bucket_uri.get_bucket().set_tags(boto_tags, headers=headers)
        except boto.exception.GSResponseError as e:
          if e.status != 200:
            raise
      if metadata.lifecycle:
        boto_lifecycle = LifecycleTranslation.BotoLifecycleFromMessage(
            metadata.lifecycle)
        bucket_uri.configure_lifecycle(boto_lifecycle, False, headers=headers)
      if metadata.logging:
        if metadata.logging.logBucket and metadata.logging.logObjectPrefix:
          bucket_uri.enable_logging(metadata.logging.logBucket,
                                    metadata.logging.logObjectPrefix,
                                    False,
                                    headers=headers)
        else:  # Logging field is present and empty.  Disable logging.
          bucket_uri.disable_logging(False, headers=headers)
      if metadata.storageClass:
        bucket_uri.set_storage_class(metadata.storageClass, headers=headers)
      if metadata.versioning:
        bucket_uri.configure_versioning(metadata.versioning.enabled,
                                        headers=headers)
      if metadata.website:
        main_page_suffix = metadata.website.mainPageSuffix
        error_page = metadata.website.notFoundPage
        bucket_uri.set_website_config(main_page_suffix,
                                      error_page,
                                      headers=headers)
      return self.GetBucket(bucket_name, fields=fields)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

  def CreateBucket(self,
                   bucket_name,
                   project_id=None,
                   metadata=None,
                   provider=None,
                   fields=None):
    """See CloudApi class for function doc strings."""
    _ = provider
    bucket_uri = self._StorageUriForBucket(bucket_name)
    location = ''
    if metadata and metadata.location:
      location = metadata.location.lower()
    # Pass storage_class param only if this is a GCS bucket. (In S3 the
    # storage class is specified on the key object.)
    headers = self._CreateBaseHeaders()
    if bucket_uri.scheme == 'gs':
      headers[GOOG_PROJ_ID_HDR] = PopulateProjectId(project_id)
      storage_class = ''
      if metadata and metadata.storageClass:
        storage_class = metadata.storageClass
      if (metadata and metadata.retentionPolicy and
          metadata.retentionPolicy.retentionPeriod):
        headers['x-goog-bucket-retention-period'] = str(
            metadata.retentionPolicy.retentionPeriod)
      try:
        bucket_uri.create_bucket(headers=headers,
                                 location=location,
                                 storage_class=storage_class)
      except TRANSLATABLE_BOTO_EXCEPTIONS as e:
        self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)
    else:
      try:
        bucket_uri.create_bucket(headers=headers, location=location)
      except TRANSLATABLE_BOTO_EXCEPTIONS as e:
        self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)
    return self.GetBucket(bucket_name, fields=fields)

  def DeleteBucket(self, bucket_name, preconditions=None, provider=None):
    """See CloudApi class for function doc strings."""
    _ = provider, preconditions
    bucket_uri = self._StorageUriForBucket(bucket_name)
    headers = self._CreateBaseHeaders()
    try:
      bucket_uri.delete_bucket(headers=headers)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      translated_exception = self._TranslateBotoException(
          e, bucket_name=bucket_name)
      if (translated_exception and
          'BucketNotEmpty' in translated_exception.reason):
        try:
          if bucket_uri.get_versioning_config():
            if self.provider == 's3':
              raise NotEmptyException(
                  'VersionedBucketNotEmpty (%s). Currently, gsutil does not '
                  'support listing or removing S3 DeleteMarkers, so you may '
                  'need to delete these using another tool to successfully '
                  'delete this bucket.' % bucket_name,
                  status=e.status,
              )
            raise NotEmptyException(
                'VersionedBucketNotEmpty (%s)' % bucket_name,
                status=e.status,
            )
          else:
            raise NotEmptyException(
                'BucketNotEmpty (%s)' % bucket_name,
                status=e.status,
            )
        except TRANSLATABLE_BOTO_EXCEPTIONS as e2:
          self._TranslateExceptionAndRaise(e2, bucket_name=bucket_name)
      elif translated_exception and translated_exception.status == 404:
        raise NotFoundException('Bucket %s does not exist.' % bucket_name)
      else:
        self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

  def ListObjects(self,
                  bucket_name,
                  prefix=None,
                  delimiter=None,
                  all_versions=None,
                  provider=None,
                  fields=None):
    """See CloudApi class for function doc strings."""
    _ = provider
    get_fields = ListToGetFields(list_fields=fields)
    bucket_uri = self._StorageUriForBucket(bucket_name)
    headers = self._CreateBaseHeaders()
    yield_prefixes = fields is None or 'prefixes' in fields
    yield_objects = fields is None or any(
        field.startswith('items/') for field in fields)
    try:
      objects_iter = bucket_uri.list_bucket(prefix=prefix or '',
                                            delimiter=delimiter or '',
                                            all_versions=all_versions,
                                            headers=headers)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

    try:
      for key in objects_iter:
        if yield_prefixes and isinstance(key, Prefix):
          yield CloudApi.CsObjectOrPrefix(key.name,
                                          CloudApi.CsObjectOrPrefixType.PREFIX)
        elif yield_objects:
          key_to_convert = key

          # Listed keys are populated with these fields during bucket listing.
          key_http_fields = set([
              'bucket',
              'etag',
              'name',
              'updated',
              'generation',
              'metageneration',
              'size',
          ])

          # When fields == None, the caller is requesting all possible fields.
          # If the caller requested any fields that are not populated by bucket
          # listing, we'll need to make a separate HTTP call for each object to
          # get its metadata and populate the remaining fields with the result.
          if not get_fields or (get_fields and
                                not get_fields.issubset(key_http_fields)):

            generation = None
            if getattr(key, 'generation', None):
              generation = key.generation
            if getattr(key, 'version_id', None):
              generation = key.version_id
            key_to_convert = self._GetBotoKey(bucket_name,
                                              key.name,
                                              generation=generation)
          return_object = self._BotoKeyToObject(key_to_convert,
                                                fields=get_fields)

          yield CloudApi.CsObjectOrPrefix(return_object,
                                          CloudApi.CsObjectOrPrefixType.OBJECT)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

  def GetObjectMetadata(self,
                        bucket_name,
                        object_name,
                        generation=None,
                        provider=None,
                        fields=None):
    """See CloudApi class for function doc strings."""
    _ = provider
    try:
      return self._BotoKeyToObject(self._GetBotoKey(bucket_name,
                                                    object_name,
                                                    generation=generation),
                                   fields=fields)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=bucket_name,
                                       object_name=object_name,
                                       generation=generation)

  def _CurryDigester(self, digester_object):
    """Curries a digester object into a form consumable by boto.

    Key instantiates its own digesters by calling hash_algs[alg]() [note there
    are no arguments to this function].  So in order to pass in our caught-up
    digesters during a resumable download, we need to pass the digester
    object but don't get to look it up based on the algorithm name.  Here we
    use a lambda to make lookup implicit.

    Args:
      digester_object: Input object to be returned by the created function.

    Returns:
      A function which when called will return the input object.
    """
    return lambda: digester_object

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
    """See CloudApi class for function doc strings."""
    # This implementation will get the object metadata first if we don't pass it
    # in via serialization_data.
    headers = self._CreateBaseHeaders()
    AddAcceptEncodingGzipIfNeeded(headers,
                                  compressed_encoding=compressed_encoding)
    if end_byte is not None:
      headers['range'] = 'bytes=%s-%s' % (start_byte, end_byte)
    elif start_byte > 0:
      headers['range'] = 'bytes=%s-' % (start_byte)
    elif start_byte < 0:
      headers['range'] = 'bytes=%s' % (start_byte)

    # Since in most cases we already made a call to get the object metadata,
    # here we avoid an extra HTTP call by unpickling the key.  This is coupled
    # with the implementation in _BotoKeyToObject.
    if serialization_data:
      serialization_dict = json.loads(serialization_data)
      key = pickle.loads(binascii.a2b_base64(serialization_dict['url']))
      if self.provider == 'gs':
        _AddCustomEndpointToKey(key)
    else:
      key = self._GetBotoKey(bucket_name, object_name, generation=generation)

    if digesters and self.provider == 'gs':
      hash_algs = {}
      for alg in digesters:
        hash_algs[alg] = self._CurryDigester(digesters[alg])
    else:
      hash_algs = {}

    total_size = object_size or 0
    if serialization_data:
      total_size = json.loads(serialization_data)['total_size']

    if total_size:
      num_progress_callbacks = max(
          int(total_size) / TWO_MIB, XML_PROGRESS_CALLBACKS)
    else:
      num_progress_callbacks = XML_PROGRESS_CALLBACKS

    try:
      if download_strategy is CloudApi.DownloadStrategy.RESUMABLE:
        self._PerformResumableDownload(download_stream,
                                       start_byte,
                                       end_byte,
                                       key,
                                       headers=headers,
                                       callback=progress_callback,
                                       num_callbacks=num_progress_callbacks,
                                       hash_algs=hash_algs)
      elif download_strategy is CloudApi.DownloadStrategy.ONE_SHOT:
        self._PerformSimpleDownload(
            download_stream,
            key,
            progress_callback=progress_callback,
            num_progress_callbacks=num_progress_callbacks,
            headers=headers,
            hash_algs=hash_algs)
      else:
        raise ArgumentException('Unsupported DownloadStrategy: %s' %
                                download_strategy)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=bucket_name,
                                       object_name=object_name,
                                       generation=generation)

    if self.provider == 's3':
      if digesters:

        class HashToDigester(object):
          """Wrapper class to expose hash digests.

          boto creates its own digesters in s3's get_file, returning on-the-fly
          hashes only by way of key.local_hashes.  To propagate the digest back
          to the caller, this stub class implements the digest() function.
          """

          def __init__(self, hash_val):
            self.hash_val = hash_val

          def digest(self):  # pylint: disable=invalid-name
            return self.hash_val

        for alg_name in digesters:
          if ((download_strategy == CloudApi.DownloadStrategy.RESUMABLE and
               start_byte != 0) or not ((getattr(key, 'local_hashes', None) and
                                         alg_name in key.local_hashes))):
            # For resumable downloads, boto does not provide a mechanism to
            # catch up the hash in the case of a partially complete download.
            # In this case or in the case where no digest was successfully
            # calculated, set the digester to None, which indicates that we'll
            # need to manually calculate the hash from the local file once it
            # is complete.
            digesters[alg_name] = None
          else:
            # Use the on-the-fly hash.
            digesters[alg_name] = HashToDigester(key.local_hashes[alg_name])

  def _PerformSimpleDownload(self,
                             download_stream,
                             key,
                             progress_callback=None,
                             num_progress_callbacks=XML_PROGRESS_CALLBACKS,
                             headers=None,
                             hash_algs=None):
    try:
      key.get_contents_to_file(download_stream,
                               cb=progress_callback,
                               num_cb=num_progress_callbacks,
                               headers=headers,
                               hash_algs=hash_algs)
    except TypeError:  # s3 and mocks do not support hash_algs
      key.get_contents_to_file(download_stream,
                               cb=progress_callback,
                               num_cb=num_progress_callbacks,
                               headers=headers)

  def _PerformResumableDownload(self,
                                fp,
                                start_byte,
                                end_byte,
                                key,
                                headers=None,
                                callback=None,
                                num_callbacks=XML_PROGRESS_CALLBACKS,
                                hash_algs=None):
    """Downloads bytes from key to fp, resuming as needed.

    Args:
      fp: File pointer into which data should be downloaded.
      start_byte: Start byte of the download.
      end_byte: End byte of the download.
      key: Key object from which data is to be downloaded
      headers: Headers to send when retrieving the file
      callback: (optional) a callback function that will be called to report
           progress on the download.  The callback should accept two integer
           parameters.  The first integer represents the number of
           bytes that have been successfully transmitted from the service.  The
           second represents the total number of bytes that need to be
           transmitted.
      num_callbacks: (optional) If a callback is specified with the callback
           parameter, this determines the granularity of the callback
           by defining the maximum number of times the callback will be
           called during the file transfer.
      hash_algs: Dict of hash algorithms to apply to downloaded bytes.

    Raises:
      ResumableDownloadException on error.
    """
    retryable_exceptions = (http_client.HTTPException, IOError, socket.error,
                            socket.gaierror)

    debug = key.bucket.connection.debug

    num_retries = GetNumRetries()
    progress_less_iterations = 0
    last_progress_byte = start_byte

    while True:  # Retry as long as we're making progress.
      try:
        cb_handler = DownloadProxyCallbackHandler(start_byte, callback)
        headers = headers.copy()
        if 'range' in headers:
          headers.pop('range')
        headers['Range'] = 'bytes=%d-%d' % (start_byte, end_byte)

        # Disable AWSAuthConnection-level retry behavior, since that would
        # cause downloads to restart from scratch.
        try:
          key.get_file(fp,
                       headers,
                       cb_handler.call,
                       num_callbacks,
                       override_num_retries=0,
                       hash_algs=hash_algs)
        except TypeError:
          key.get_file(fp,
                       headers,
                       cb_handler.call,
                       num_callbacks,
                       override_num_retries=0)
        fp.flush()
        # Download succeeded.
        return
      except retryable_exceptions as e:  # pylint: disable=catching-non-exception
        if debug >= 1:
          self.logger.info('Caught exception (%s)', repr(e))
        if isinstance(e, IOError) and e.errno == errno.EPIPE:
          # Broken pipe error causes httplib to immediately
          # close the socket (http://bugs.python.org/issue5542),
          # so we need to close and reopen the key before resuming
          # the download.
          if self.provider == 's3':
            key.get_file(fp,
                         headers,
                         cb_handler.call,
                         num_callbacks,
                         override_num_retries=0)
          else:  # self.provider == 'gs'
            key.get_file(fp,
                         headers,
                         cb_handler.call,
                         num_callbacks,
                         override_num_retries=0,
                         hash_algs=hash_algs)
      except boto.exception.ResumableDownloadException as e:
        if (e.disposition ==
            boto.exception.ResumableTransferDisposition.ABORT_CUR_PROCESS):
          raise ResumableDownloadException(e.message)
        else:
          if debug >= 1:
            self.logger.info(
                'Caught boto.exception.ResumableDownloadException (%s) - will '
                'retry', e.message)

      # At this point we had a re-tryable failure; see if made progress.
      start_byte = fp.tell()
      if start_byte > last_progress_byte:
        last_progress_byte = start_byte
        progress_less_iterations = 0
      else:
        progress_less_iterations += 1

      if progress_less_iterations > num_retries:
        # Don't retry any longer in the current process.
        raise ResumableDownloadException(
            'Too many resumable download attempts failed without '
            'progress. You might try this download again later')

      # Close the key, in case a previous download died partway
      # through and left data in the underlying key HTTP buffer.
      # Do this within a try/except block in case the connection is
      # closed (since key.close() attempts to do a final read, in which
      # case this read attempt would get an IncompleteRead exception,
      # which we can safely ignore).
      try:
        key.close()
      except http_client.IncompleteRead:
        pass

      sleep_time_secs = min(random.random() * (2**progress_less_iterations),
                            GetMaxRetryDelay())
      if debug >= 1:
        self.logger.info(
            'Got retryable failure (%d progress-less in a row).\nSleeping %d '
            'seconds before re-trying', progress_less_iterations,
            sleep_time_secs)
      time.sleep(sleep_time_secs)

  def PatchObjectMetadata(self,
                          bucket_name,
                          object_name,
                          metadata,
                          canned_acl=None,
                          generation=None,
                          preconditions=None,
                          provider=None,
                          fields=None):
    """See CloudApi class for function doc strings."""
    _ = provider
    object_uri = self._StorageUriForObject(bucket_name,
                                           object_name,
                                           generation=generation)

    headers = self._CreateBaseHeaders()
    meta_headers = HeadersFromObjectMetadata(metadata, self.provider)

    metadata_plus = {}
    metadata_minus = set()
    metadata_changed = False
    for k, v in six.iteritems(meta_headers):
      metadata_changed = True
      if v is None:
        metadata_minus.add(k)
      else:
        metadata_plus[k] = v

    self._AddPreconditionsToHeaders(preconditions, headers)

    if metadata_changed:
      try:
        object_uri.set_metadata(metadata_plus,
                                metadata_minus,
                                False,
                                headers=headers)
      except TRANSLATABLE_BOTO_EXCEPTIONS as e:
        self._TranslateExceptionAndRaise(e,
                                         bucket_name=bucket_name,
                                         object_name=object_name,
                                         generation=generation)

    if metadata.acl:
      boto_acl = AclTranslation.BotoAclFromMessage(metadata.acl)
      try:
        object_uri.set_xml_acl(boto_acl.to_xml(),
                               key_name=object_name,
                               headers=headers)
      except TRANSLATABLE_BOTO_EXCEPTIONS as e:
        self._TranslateExceptionAndRaise(e,
                                         bucket_name=bucket_name,
                                         object_name=object_name,
                                         generation=generation)
    if canned_acl:
      canned_acls = object_uri.canned_acls()
      if canned_acl not in canned_acls:
        raise CommandException('Invalid canned ACL "%s".' % canned_acl)
      object_uri.set_acl(canned_acl, object_uri.object_name, headers=headers)

    return self.GetObjectMetadata(bucket_name,
                                  object_name,
                                  generation=generation,
                                  fields=fields)

  def _PerformSimpleUpload(self,
                           dst_uri,
                           upload_stream,
                           md5=None,
                           canned_acl=None,
                           progress_callback=None,
                           headers=None):
    dst_uri.set_contents_from_file(upload_stream,
                                   md5=md5,
                                   policy=canned_acl,
                                   cb=progress_callback,
                                   headers=headers,
                                   rewind=True)

  def _PerformStreamingUpload(self,
                              dst_uri,
                              upload_stream,
                              canned_acl=None,
                              progress_callback=None,
                              headers=None):
    if dst_uri.get_provider().supports_chunked_transfer():
      dst_uri.set_contents_from_stream(upload_stream,
                                       policy=canned_acl,
                                       cb=progress_callback,
                                       headers=headers)
    else:
      # Provider doesn't support chunked transfer, so copy to a temporary
      # file.
      (temp_fh, temp_path) = tempfile.mkstemp()
      try:
        with open(temp_path, 'wb') as out_fp:
          stream_bytes = upload_stream.read(DEFAULT_FILE_BUFFER_SIZE)
          while stream_bytes:
            out_fp.write(stream_bytes)
            stream_bytes = upload_stream.read(DEFAULT_FILE_BUFFER_SIZE)
        with open(temp_path, 'rb') as in_fp:
          dst_uri.set_contents_from_file(in_fp,
                                         policy=canned_acl,
                                         headers=headers)
      finally:
        os.close(temp_fh)
        os.unlink(temp_path)

  def _PerformResumableUpload(self,
                              key,
                              upload_stream,
                              upload_size,
                              tracker_callback,
                              canned_acl=None,
                              serialization_data=None,
                              progress_callback=None,
                              headers=None):
    resumable_upload = BotoResumableUpload(tracker_callback,
                                           self.logger,
                                           resume_url=serialization_data)
    resumable_upload.SendFile(key,
                              upload_stream,
                              upload_size,
                              canned_acl=canned_acl,
                              cb=progress_callback,
                              headers=headers)

  def _UploadSetup(self, object_metadata, preconditions=None):
    """Shared upload implementation.

    Args:
      object_metadata: Object metadata describing destination object.
      preconditions: Optional gsutil Cloud API preconditions.

    Returns:
      Headers dictionary, StorageUri for upload (based on inputs)
    """
    ValidateDstObjectMetadata(object_metadata)

    headers = self._CreateBaseHeaders()
    headers.update(HeadersFromObjectMetadata(object_metadata, self.provider))

    if object_metadata.crc32c:
      if 'x-goog-hash' in headers:
        headers['x-goog-hash'] += (',crc32c=%s' %
                                   object_metadata.crc32c.rstrip('\n'))
      else:
        headers['x-goog-hash'] = ('crc32c=%s' %
                                  object_metadata.crc32c.rstrip('\n'))
    if object_metadata.md5Hash:
      if 'x-goog-hash' in headers:
        headers['x-goog-hash'] += (',md5=%s' %
                                   object_metadata.md5Hash.rstrip('\n'))
      else:
        headers['x-goog-hash'] = ('md5=%s' %
                                  object_metadata.md5Hash.rstrip('\n'))

    if 'content-type' in headers and not headers['content-type']:
      headers['content-type'] = 'application/octet-stream'

    self._AddPreconditionsToHeaders(preconditions, headers)

    dst_uri = self._StorageUriForObject(object_metadata.bucket,
                                        object_metadata.name)
    return headers, dst_uri

  def _HandleSuccessfulUpload(self, dst_uri, object_metadata, fields=None):
    """Set ACLs on an uploaded object and return its metadata.

    Args:
      dst_uri: Generation-specific StorageUri describing the object.
      object_metadata: Metadata for the object, including an ACL if applicable.
      fields: If present, return only these Object metadata fields.

    Returns:
      gsutil Cloud API Object metadata.

    Raises:
      CommandException if the object was overwritten / deleted concurrently.
    """
    try:
      # The XML API does not support if-generation-match for GET requests.
      # Therefore, if the object gets overwritten before the ACL and get_key
      # operations, the best we can do is warn that it happened.
      self._SetObjectAcl(object_metadata, dst_uri)
      headers = self._CreateBaseHeaders()
      return self._BotoKeyToObject(dst_uri.get_key(headers=headers),
                                   fields=fields)
    except boto.exception.InvalidUriError as e:
      if e.message and NON_EXISTENT_OBJECT_REGEX.match(e.message.encode(UTF8)):
        raise CommandException('\n'.join(
            textwrap.wrap(
                'Uploaded object (%s) was deleted or overwritten immediately '
                'after it was uploaded. This can happen if you attempt to upload '
                'to the same object multiple times concurrently.' %
                dst_uri.uri)))
      else:
        raise

  def _SetObjectAcl(self, object_metadata, dst_uri):
    """Sets the ACL (if present in object_metadata) on an uploaded object."""
    headers = self._CreateBaseHeaders()
    if object_metadata.acl:
      boto_acl = AclTranslation.BotoAclFromMessage(object_metadata.acl)
      dst_uri.set_xml_acl(boto_acl.to_xml(), headers=headers)
    elif self.provider == 's3':
      s3_acl = S3MarkerAclFromObjectMetadata(object_metadata)
      if s3_acl:
        dst_uri.set_xml_acl(s3_acl, headers=headers)

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
    """See CloudApi class for function doc strings."""
    if gzip_encoded:
      raise NotImplementedError(
          'XML API does not support gzip-encoded uploads.')
    if self.provider == 's3':
      # Resumable uploads are not supported for s3.
      return self.UploadObject(upload_stream,
                               object_metadata,
                               canned_acl=canned_acl,
                               preconditions=preconditions,
                               fields=fields,
                               size=size)
    headers, dst_uri = self._UploadSetup(object_metadata,
                                         preconditions=preconditions)
    if not tracker_callback:
      raise ArgumentException('No tracker callback function set for '
                              'resumable upload of %s' % dst_uri)
    try:
      self._PerformResumableUpload(dst_uri.new_key(headers=headers),
                                   upload_stream,
                                   size,
                                   tracker_callback,
                                   canned_acl=canned_acl,
                                   serialization_data=serialization_data,
                                   progress_callback=progress_callback,
                                   headers=headers)
      return self._HandleSuccessfulUpload(dst_uri,
                                          object_metadata,
                                          fields=fields)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      not_found_exception = CreateNotFoundExceptionForObjectWrite(
          self.provider, object_metadata.bucket)
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=object_metadata.bucket,
                                       object_name=object_metadata.name,
                                       not_found_exception=not_found_exception)

  def UploadObjectStreaming(self,
                            upload_stream,
                            object_metadata,
                            canned_acl=None,
                            progress_callback=None,
                            preconditions=None,
                            encryption_tuple=None,
                            provider=None,
                            fields=None,
                            gzip_encoded=False):
    """See CloudApi class for function doc strings."""
    if gzip_encoded:
      raise NotImplementedError('XML API does not suport gzip-encoded uploads.')
    headers, dst_uri = self._UploadSetup(object_metadata,
                                         preconditions=preconditions)

    try:
      self._PerformStreamingUpload(dst_uri,
                                   upload_stream,
                                   canned_acl=canned_acl,
                                   progress_callback=progress_callback,
                                   headers=headers)
      return self._HandleSuccessfulUpload(dst_uri,
                                          object_metadata,
                                          fields=fields)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      not_found_exception = CreateNotFoundExceptionForObjectWrite(
          self.provider, object_metadata.bucket)
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=object_metadata.bucket,
                                       object_name=object_metadata.name,
                                       not_found_exception=not_found_exception)

  def UploadObject(self,
                   upload_stream,
                   object_metadata,
                   canned_acl=None,
                   preconditions=None,
                   size=None,
                   progress_callback=None,
                   encryption_tuple=None,
                   provider=None,
                   fields=None,
                   gzip_encoded=False):
    """See CloudApi class for function doc strings."""
    if gzip_encoded:
      raise NotImplementedError('XML API does not suport gzip-encoded uploads.')

    headers, dst_uri = self._UploadSetup(object_metadata,
                                         preconditions=preconditions)

    try:
      md5 = None
      if object_metadata.md5Hash:
        # boto expects hex at index 0, base64 at index 1
        md5 = [
            Base64ToHexHash(object_metadata.md5Hash),
            object_metadata.md5Hash.strip('\n"\'')
        ]
      self._PerformSimpleUpload(dst_uri,
                                upload_stream,
                                md5=md5,
                                canned_acl=canned_acl,
                                progress_callback=progress_callback,
                                headers=headers)
      return self._HandleSuccessfulUpload(dst_uri,
                                          object_metadata,
                                          fields=fields)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      not_found_exception = CreateNotFoundExceptionForObjectWrite(
          self.provider, object_metadata.bucket)
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=object_metadata.bucket,
                                       object_name=object_metadata.name,
                                       not_found_exception=not_found_exception)

  def DeleteObject(self,
                   bucket_name,
                   object_name,
                   preconditions=None,
                   generation=None,
                   provider=None):
    """See CloudApi class for function doc strings."""
    _ = provider
    headers = self._CreateBaseHeaders()
    self._AddPreconditionsToHeaders(preconditions, headers)

    uri = self._StorageUriForObject(bucket_name,
                                    object_name,
                                    generation=generation)
    try:
      uri.delete_key(validate=False, headers=headers)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=bucket_name,
                                       object_name=object_name,
                                       generation=generation)

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
    """See CloudApi class for function doc strings."""
    _ = provider

    if max_bytes_per_call is not None:
      raise NotImplementedError('XML API does not suport max_bytes_per_call')
    dst_uri = self._StorageUriForObject(dst_obj_metadata.bucket,
                                        dst_obj_metadata.name)

    # Usually it's okay to treat version_id and generation as
    # the same, but in this case the underlying boto call determines the
    # provider based on the presence of one or the other.
    src_version_id = None
    if self.provider == 's3':
      src_version_id = src_generation
      src_generation = None

    headers = self._CreateBaseHeaders()
    headers.update(HeadersFromObjectMetadata(dst_obj_metadata, self.provider))
    self._AddPreconditionsToHeaders(preconditions, headers)

    if canned_acl:
      headers[dst_uri.get_provider().acl_header] = canned_acl

    preserve_acl = True if dst_obj_metadata.acl else False
    if self.provider == 's3':
      s3_acl = S3MarkerAclFromObjectMetadata(dst_obj_metadata)
      if s3_acl:
        preserve_acl = True

    # If no destination storage class was specified, we want to not specify a
    # storage class in our copy request, resulting in the bucket's default
    # storage class being used. Boto uses a default storage class of STANDARD
    # for copy_key() calls, so we explicitly use None if no storage class was
    # specified, which will omit the storage class header in our request.
    dst_storage_class = dst_obj_metadata.storageClass or None
    try:
      new_key = dst_uri.copy_key(src_obj_metadata.bucket,
                                 src_obj_metadata.name,
                                 preserve_acl=preserve_acl,
                                 headers=headers,
                                 storage_class=dst_storage_class,
                                 src_version_id=src_version_id,
                                 src_generation=src_generation)

      return self._BotoKeyToObject(new_key, fields=fields)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      not_found_exception = CreateNotFoundExceptionForObjectWrite(
          self.provider,
          dst_obj_metadata.bucket,
          src_provider=self.provider,
          src_bucket_name=src_obj_metadata.bucket,
          src_object_name=src_obj_metadata.name,
          src_generation=src_generation)
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=dst_obj_metadata.bucket,
                                       object_name=dst_obj_metadata.name,
                                       not_found_exception=not_found_exception)

  def ComposeObject(self,
                    src_objs_metadata,
                    dst_obj_metadata,
                    preconditions=None,
                    encryption_tuple=None,
                    provider=None,
                    fields=None):
    """See CloudApi class for function doc strings."""
    _ = provider
    ValidateDstObjectMetadata(dst_obj_metadata)

    dst_obj_name = dst_obj_metadata.name
    dst_obj_metadata.name = None
    dst_bucket_name = dst_obj_metadata.bucket
    dst_obj_metadata.bucket = None

    headers = self._CreateBaseHeaders()
    headers.update(HeadersFromObjectMetadata(dst_obj_metadata, self.provider))
    self._AddPreconditionsToHeaders(preconditions, headers)

    if not dst_obj_metadata.contentType:
      dst_obj_metadata.contentType = DEFAULT_CONTENT_TYPE
      headers['content-type'] = dst_obj_metadata.contentType

    dst_uri = self._StorageUriForObject(dst_bucket_name, dst_obj_name)

    src_components = []
    for src_obj in src_objs_metadata:
      src_uri = self._StorageUriForObject(dst_bucket_name,
                                          src_obj.name,
                                          generation=src_obj.generation)
      src_components.append(src_uri)

    try:
      dst_uri.compose(src_components, headers=headers)

      return self.GetObjectMetadata(dst_bucket_name,
                                    dst_obj_name,
                                    fields=fields)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, dst_obj_metadata.bucket,
                                       dst_obj_metadata.name)

  def _AddPreconditionsToHeaders(self, preconditions, headers):
    """Adds preconditions (if any) to headers."""
    if preconditions and self.provider == 'gs':
      if preconditions.gen_match is not None:
        headers['x-goog-if-generation-match'] = str(preconditions.gen_match)
      if preconditions.meta_gen_match is not None:
        headers['x-goog-if-metageneration-match'] = str(
            preconditions.meta_gen_match)

  def _CreateBaseHeaders(self):
    """Creates base headers used for all API calls in this class."""
    base_headers = {}
    if self.http_headers:
      base_headers.update(self.http_headers)

    if self.provider == 'gs':
      base_headers['x-goog-api-version'] = self.api_version
    if self.provider == 'gs' and self.perf_trace_token:
      base_headers['cookie'] = self.perf_trace_token
    request_reason = os.environ.get(REQUEST_REASON_ENV_VAR)
    if request_reason:
      base_headers[REQUEST_REASON_HEADER_KEY] = request_reason

    return base_headers

  def _GetMD5FromETag(self, src_etag):
    """Returns an MD5 from the etag iff the etag is a valid MD5 hash.

    Args:
      src_etag: Object etag for which to return the MD5.

    Returns:
      MD5 in hex string format, or None.
    """
    if src_etag and MD5_REGEX.search(src_etag):
      return src_etag.strip('"\'').lower()

  def _StorageUriForBucket(self, bucket):
    """Returns a boto storage_uri for the given bucket name.

    Args:
      bucket: Bucket name (string).

    Returns:
      Boto storage_uri for the bucket.
    """
    return boto.storage_uri(
        '%s://%s' % (self.provider, bucket),
        suppress_consec_slashes=False,
        bucket_storage_uri_class=self.bucket_storage_uri_class,
        debug=self.debug,
        validate=False)

  def _StorageUriForObject(self, bucket, object_name, generation=None):
    """Returns a boto storage_uri for the given object.

    Args:
      bucket: Bucket name (string).
      object_name: Object name (string).
      generation: Generation or version_id of object.  If None, live version
                  of the object is used.

    Returns:
      Boto storage_uri for the object.
    """
    uri_string = '%s://%s/%s' % (self.provider, bucket, object_name)
    if generation:
      uri_string += '#%s' % generation
    return boto.storage_uri(
        uri_string,
        suppress_consec_slashes=False,
        bucket_storage_uri_class=self.bucket_storage_uri_class,
        debug=self.debug)

  def _GetBotoKey(self, bucket_name, object_name, generation=None):
    """Gets the boto key for an object.

    Args:
      bucket_name: Bucket containing the object.
      object_name: Object name.
      generation: Generation or version of the object to retrieve.

    Returns:
      Boto key for the object.
    """
    object_uri = self._StorageUriForObject(bucket_name,
                                           object_name,
                                           generation=generation)
    try:
      headers = self._CreateBaseHeaders()
      key = object_uri.get_key(headers=headers)
      if not key:
        raise CreateObjectNotFoundException('404',
                                            self.provider,
                                            bucket_name,
                                            object_name,
                                            generation=generation)
      return key
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=bucket_name,
                                       object_name=object_name,
                                       generation=generation)

  # pylint: disable=too-many-statements
  def _BotoBucketToBucket(self, bucket, fields=None):
    """Constructs an apitools Bucket from a boto bucket.

    Args:
      bucket: Boto bucket.
      fields: If present, construct the apitools Bucket with only this set of
              metadata fields.

    Returns:
      apitools Bucket.
    """
    bucket_uri = self._StorageUriForBucket(bucket.name)

    cloud_api_bucket = apitools_messages.Bucket(name=bucket.name,
                                                id=bucket.name)
    headers = self._CreateBaseHeaders()
    if self.provider == 'gs':
      if not fields or 'storageClass' in fields:
        if hasattr(bucket, 'get_storage_class'):
          cloud_api_bucket.storageClass = bucket.get_storage_class()
      if not fields or 'acl' in fields:
        try:
          for acl in AclTranslation.BotoBucketAclToMessage(
              bucket.get_acl(headers=headers)):
            cloud_api_bucket.acl.append(acl)
        except TRANSLATABLE_BOTO_EXCEPTIONS as e:
          translated_exception = self._TranslateBotoException(
              e, bucket_name=bucket.name)
          if (translated_exception and
              isinstance(translated_exception, AccessDeniedException)):
            # JSON API doesn't differentiate between a blank ACL list
            # and an access denied, so this is intentionally left blank.
            pass
          else:
            self._TranslateExceptionAndRaise(e, bucket_name=bucket.name)
      if not fields or 'cors' in fields:
        try:
          boto_cors = bucket_uri.get_cors(headers=headers)
          cloud_api_bucket.cors = CorsTranslation.BotoCorsToMessage(boto_cors)
        except TRANSLATABLE_BOTO_EXCEPTIONS as e:
          self._TranslateExceptionAndRaise(e, bucket_name=bucket.name)
      if not fields or 'defaultObjectAcl' in fields:
        try:
          for acl in AclTranslation.BotoObjectAclToMessage(
              bucket.get_def_acl(headers=headers)):
            cloud_api_bucket.defaultObjectAcl.append(acl)
        except TRANSLATABLE_BOTO_EXCEPTIONS as e:
          translated_exception = self._TranslateBotoException(
              e, bucket_name=bucket.name)
          if (translated_exception and
              isinstance(translated_exception, AccessDeniedException)):
            # JSON API doesn't differentiate between a blank ACL list
            # and an access denied, so this is intentionally left blank.
            pass
          else:
            self._TranslateExceptionAndRaise(e, bucket_name=bucket.name)
      if not fields or 'encryption' in fields:
        try:
          keyname = (bucket_uri.get_encryption_config(
              headers=headers).default_kms_key_name)
          if keyname:
            cloud_api_bucket.encryption = (
                apitools_messages.Bucket.EncryptionValue())
            cloud_api_bucket.encryption.defaultKmsKeyName = keyname
        except TRANSLATABLE_BOTO_EXCEPTIONS as e:
          self._TranslateExceptionAndRaise(e, bucket_name=bucket.name)
      if not fields or 'lifecycle' in fields:
        try:
          boto_lifecycle = bucket_uri.get_lifecycle_config(headers=headers)
          cloud_api_bucket.lifecycle = (
              LifecycleTranslation.BotoLifecycleToMessage(boto_lifecycle))
        except TRANSLATABLE_BOTO_EXCEPTIONS as e:
          self._TranslateExceptionAndRaise(e, bucket_name=bucket.name)
      if not fields or 'logging' in fields:
        try:
          boto_logging = bucket_uri.get_logging_config(headers=headers)
          if boto_logging and 'Logging' in boto_logging:
            logging_config = boto_logging['Logging']
            log_object_prefix_present = 'LogObjectPrefix' in logging_config
            log_bucket_present = 'LogBucket' in logging_config
            if log_object_prefix_present or log_bucket_present:
              cloud_api_bucket.logging = apitools_messages.Bucket.LoggingValue()
              if log_object_prefix_present:
                cloud_api_bucket.logging.logObjectPrefix = (
                    logging_config['LogObjectPrefix'])
              if log_bucket_present:
                cloud_api_bucket.logging.logBucket = logging_config['LogBucket']
        except TRANSLATABLE_BOTO_EXCEPTIONS as e:
          self._TranslateExceptionAndRaise(e, bucket_name=bucket.name)
      if not fields or 'website' in fields:
        try:
          boto_website = bucket_uri.get_website_config(headers=headers)
          if boto_website and 'WebsiteConfiguration' in boto_website:
            website_config = boto_website['WebsiteConfiguration']
            main_page_suffix_present = 'MainPageSuffix' in website_config
            not_found_page_present = 'NotFoundPage' in website_config
            if main_page_suffix_present or not_found_page_present:
              cloud_api_bucket.website = apitools_messages.Bucket.WebsiteValue()
              if main_page_suffix_present:
                cloud_api_bucket.website.mainPageSuffix = (
                    website_config['MainPageSuffix'])
              if not_found_page_present:
                cloud_api_bucket.website.notFoundPage = (
                    website_config['NotFoundPage'])
        except TRANSLATABLE_BOTO_EXCEPTIONS as e:
          self._TranslateExceptionAndRaise(e, bucket_name=bucket.name)
      if not fields or 'location' in fields:
        cloud_api_bucket.location = bucket_uri.get_location(headers=headers)
      # End gs-specific field checks.
    if not fields or 'labels' in fields:
      try:
        # TODO: Define tags-related methods on storage_uri objects. In the
        # meantime, we invoke the underlying bucket's methods directly.
        try:
          boto_tags = bucket_uri.get_bucket().get_tags()
          cloud_api_bucket.labels = (
              LabelTranslation.BotoTagsToMessage(boto_tags))
        except boto.exception.StorageResponseError as e:
          # If no tagging config exists, the S3 API returns a 404 (the GS API
          # returns a 200 with an empty TagSet). If the bucket didn't exist,
          # we would have failed much earlier in this method, so we know that
          # it's the tagging config that doesn't exist.
          if not (self.provider == 's3' and e.status == 404):
            raise
      except TRANSLATABLE_BOTO_EXCEPTIONS as e:
        self._TranslateExceptionAndRaise(e, bucket_name=bucket.name)
    if not fields or 'versioning' in fields:
      versioning = bucket_uri.get_versioning_config(headers=headers)
      if versioning:
        if (self.provider == 's3' and 'Versioning' in versioning and
            versioning['Versioning'] == 'Enabled'):
          cloud_api_bucket.versioning = (
              apitools_messages.Bucket.VersioningValue(enabled=True))
        elif self.provider == 'gs':
          cloud_api_bucket.versioning = (
              apitools_messages.Bucket.VersioningValue(enabled=True))

    # For S3 long bucket listing we do not support CORS, lifecycle, website, and
    # logging translation. The individual commands can be used to get
    # the XML equivalents for S3.
    return cloud_api_bucket

  def _BotoKeyToObject(self, key, fields=None):
    """Constructs an apitools Object from a boto key.

    Args:
      key: Boto key to construct Object from.
      fields: If present, construct the apitools Object with only this set of
              metadata fields.

    Returns:
      apitools Object corresponding to key.
    """
    custom_metadata = None
    if not fields or 'metadata' in fields or len(
        [field for field in fields if field.startswith('metadata/')]) >= 1:
      custom_metadata = self._TranslateBotoKeyCustomMetadata(key)
    cache_control = None
    if not fields or 'cacheControl' in fields:
      cache_control = getattr(key, 'cache_control', None)
    component_count = None
    if not fields or 'componentCount' in fields:
      component_count = getattr(key, 'component_count', None)
    content_disposition = None
    if not fields or 'contentDisposition' in fields:
      content_disposition = getattr(key, 'content_disposition', None)
    # Other fields like updated and ACL depend on the generation
    # of the object, so populate that regardless of whether it was requested.
    generation = self._TranslateBotoKeyGeneration(key)
    metageneration = None
    if not fields or 'metageneration' in fields:
      metageneration = self._TranslateBotoKeyMetageneration(key)
    time_created = None
    if not fields or 'timeCreated' in fields:
      # Translation code to avoid a dependency on dateutil.
      time_created = self._TranslateBotoKeyTimestamp(key)
    etag = None
    if not fields or 'etag' in fields:
      etag = getattr(key, 'etag', None)
      if etag:
        etag = etag.strip('"\'')
    crc32c = None
    if not fields or 'crc32c' in fields:
      if hasattr(key, 'cloud_hashes') and 'crc32c' in key.cloud_hashes:
        crc32c = base64.b64encode(key.cloud_hashes['crc32c']).rstrip(b'\n')
    md5_hash = None
    if not fields or 'md5Hash' in fields:
      if hasattr(key, 'cloud_hashes') and 'md5' in key.cloud_hashes:
        md5_hash = base64.b64encode(key.cloud_hashes['md5']).rstrip(b'\n')
      elif self._GetMD5FromETag(getattr(key, 'etag', None)):
        md5_hash = Base64EncodeHash(self._GetMD5FromETag(key.etag))
      elif self.provider == 's3':
        # S3 etags are MD5s for non-multi-part objects, but multi-part objects
        # (which include all objects >= 5 GB) have a custom checksum
        # implementation that is not currently supported by gsutil.
        self.logger.warn(
            'Non-MD5 etag (%s) present for key %s, data integrity checks are '
            'not possible.', key.etag, key)

    # Serialize the boto key in the media link if it is requested.  This
    # way we can later access the key without adding an HTTP call.
    media_link = None
    if not fields or 'mediaLink' in fields:
      media_link = binascii.b2a_base64(
          pickle.dumps(key, pickle.HIGHEST_PROTOCOL))
    size = None
    if not fields or 'size' in fields:
      size = key.size or 0
    storage_class = None
    if not fields or 'storageClass' in fields:
      # TODO: Scrub all callers requesting the storageClass field and then
      # revert this to storage_class; the base storage_class
      # attribute calls GET on the bucket if the storage class is not already
      # populated in the key, which can fail if the user does not have
      # permission on the bucket.
      storage_class = getattr(key, '_storage_class', None)

    if six.PY3:
      if crc32c and isinstance(crc32c, bytes):
        crc32c = crc32c.decode('ascii')
      if md5_hash and isinstance(md5_hash, bytes):
        md5_hash = md5_hash.decode('ascii')

    cloud_api_object = apitools_messages.Object(
        bucket=key.bucket.name,
        name=key.name,
        size=size,
        contentEncoding=key.content_encoding,
        contentLanguage=key.content_language,
        contentType=key.content_type,
        cacheControl=cache_control,
        contentDisposition=content_disposition,
        etag=etag,
        crc32c=crc32c,
        md5Hash=md5_hash,
        generation=generation,
        metageneration=metageneration,
        componentCount=component_count,
        timeCreated=time_created,
        metadata=custom_metadata,
        mediaLink=media_link,
        storageClass=storage_class)

    # Remaining functions amend cloud_api_object.
    self._TranslateDeleteMarker(key, cloud_api_object)
    if not fields or 'acl' in fields:
      generation_str = GenerationFromUrlAndString(
          StorageUrlFromString(self.provider), generation)
      self._TranslateBotoKeyAcl(key,
                                cloud_api_object,
                                generation=generation_str)

    return cloud_api_object

  def _TranslateBotoKeyCustomMetadata(self, key):
    """Populates an apitools message from custom metadata in the boto key."""
    custom_metadata = None
    if getattr(key, 'metadata', None):
      custom_metadata = apitools_messages.Object.MetadataValue(
          additionalProperties=[])
      for k, v in six.iteritems(key.metadata):
        if k.lower() == 'content-language':
          # Work around content-language being inserted into custom metadata.
          continue
        custom_metadata.additionalProperties.append(
            apitools_messages.Object.MetadataValue.AdditionalProperty(key=k,
                                                                      value=v))
    return custom_metadata

  def _TranslateBotoKeyGeneration(self, key):
    """Returns the generation/version_id number from the boto key if present."""
    generation = None
    if self.provider == 'gs':
      if getattr(key, 'generation', None):
        generation = long(key.generation)
    elif self.provider == 's3':
      if getattr(key, 'version_id', None):
        generation = EncodeStringAsLong(key.version_id)
    return generation

  def _TranslateBotoKeyMetageneration(self, key):
    """Returns the metageneration number from the boto key if present."""
    metageneration = None
    if self.provider == 'gs':
      if getattr(key, 'metageneration', None):
        metageneration = long(key.metageneration)
    return metageneration

  def _TranslateBotoKeyTimestamp(self, key):
    """Parses the timestamp from the boto key into an datetime object.

    This avoids a dependency on dateutil.

    Args:
      key: Boto key to get timestamp from.

    Returns:
      datetime object if string is parsed successfully, None otherwise.
    """
    if key.last_modified:
      if '.' in key.last_modified:
        key_us_timestamp = key.last_modified.rstrip('Z') + '000Z'
      else:
        key_us_timestamp = key.last_modified.rstrip('Z') + '.000000Z'
      fmt = '%Y-%m-%dT%H:%M:%S.%fZ'
      try:
        return datetime.datetime.strptime(key_us_timestamp, fmt)
      except ValueError:
        try:
          # Try alternate format
          fmt = '%a, %d %b %Y %H:%M:%S %Z'
          return datetime.datetime.strptime(key.last_modified, fmt)
        except ValueError:
          # Could not parse the time; leave updated as None.
          return None

  def _TranslateDeleteMarker(self, key, cloud_api_object):
    """Marks deleted objects with a metadata value (for S3 compatibility)."""
    if isinstance(key, DeleteMarker):
      if not cloud_api_object.metadata:
        cloud_api_object.metadata = apitools_messages.Object.MetadataValue()
        cloud_api_object.metadata.additionalProperties = []
      cloud_api_object.metadata.additionalProperties.append(
          apitools_messages.Object.MetadataValue.AdditionalProperty(
              key=S3_DELETE_MARKER_GUID, value=True))

  def _TranslateBotoKeyAcl(self, key, cloud_api_object, generation=None):
    """Updates cloud_api_object with the ACL from the boto key."""
    storage_uri_for_key = self._StorageUriForObject(key.bucket.name,
                                                    key.name,
                                                    generation=generation)
    headers = self._CreateBaseHeaders()
    try:
      if self.provider == 'gs':
        key_acl = storage_uri_for_key.get_acl(headers=headers)
        # key.get_acl() does not support versioning so we need to use
        # storage_uri to ensure we're getting the versioned ACL.
        for acl in AclTranslation.BotoObjectAclToMessage(key_acl):
          cloud_api_object.acl.append(acl)
      if self.provider == 's3':
        key_acl = key.get_xml_acl(headers=headers)
        # ACLs for s3 are different and we use special markers to represent
        # them in the gsutil Cloud API.
        AddS3MarkerAclToObjectMetadata(cloud_api_object, key_acl)
    except boto.exception.GSResponseError as e:
      if e.status == 403:
        # Consume access denied exceptions to mimic JSON behavior of simply
        # returning None if sufficient permission is not present.  The caller
        # needs to handle the case where the ACL is not populated.
        pass
      else:
        raise

  def _TranslateExceptionAndRaise(self,
                                  e,
                                  bucket_name=None,
                                  object_name=None,
                                  generation=None,
                                  not_found_exception=None):
    """Translates a Boto exception and raises the translated or original value.

    Args:
      e: Any Exception.
      bucket_name: Optional bucket name in request that caused the exception.
      object_name: Optional object name in request that caused the exception.
      generation: Optional generation in request that caused the exception.
      not_found_exception: Optional exception to raise in the not-found case.

    Raises:
      Translated CloudApi exception, or the original exception if it was not
      translatable.
    """
    translated_exception = self._TranslateBotoException(
        e,
        bucket_name=bucket_name,
        object_name=object_name,
        generation=generation,
        not_found_exception=not_found_exception)
    if translated_exception:
      raise translated_exception  # pylint: disable=raising-bad-type
    else:
      raise

  def _TranslateBotoException(self,
                              e,
                              bucket_name=None,
                              object_name=None,
                              generation=None,
                              not_found_exception=None):
    """Translates boto exceptions into their gsutil Cloud API equivalents.

    Args:
      e: Any exception in TRANSLATABLE_BOTO_EXCEPTIONS.
      bucket_name: Optional bucket name in request that caused the exception.
      object_name: Optional object name in request that caused the exception.
      generation: Optional generation in request that caused the exception.
      not_found_exception: Optional exception to raise in the not-found case.

    Returns:
      ServiceException for translatable exceptions, None
      otherwise.

    Because we're using isinstance, check for subtypes first.
    """
    if isinstance(e, boto.exception.StorageResponseError):
      if e.status == 400:
        return BadRequestException(e.code, status=e.status, body=e.body)
      elif e.status == 401 or e.status == 403:
        return AccessDeniedException(e.code, status=e.status, body=e.body)
      elif e.status == 404:
        if not_found_exception:
          # The exception is pre-constructed prior to translation; the HTTP
          # status code isn't available at that time.
          setattr(not_found_exception, 'status', e.status)
          return not_found_exception
        elif bucket_name:
          if object_name:
            return CreateObjectNotFoundException(e.status,
                                                 self.provider,
                                                 bucket_name,
                                                 object_name,
                                                 generation=generation)
          return CreateBucketNotFoundException(e.status, self.provider,
                                               bucket_name)
        return NotFoundException(e.message, status=e.status, body=e.body)

      elif e.status == 409 and e.code and 'BucketNotEmpty' in e.code:
        return NotEmptyException('BucketNotEmpty (%s)' % bucket_name,
                                 status=e.status,
                                 body=e.body)
      elif e.status == 410:
        # 410 errors should always cause us to start over - either the UploadID
        # has expired or there was a server-side problem that requires starting
        # the upload over from scratch.
        return ResumableUploadStartOverException(e.message)
      elif e.status == 412:
        return PreconditionException(e.code, status=e.status, body=e.body)
    if isinstance(e, boto.exception.StorageCreateError):
      return ServiceException('Bucket already exists.',
                              status=e.status,
                              body=e.body)

    if isinstance(e, boto.exception.BotoServerError):
      return ServiceException(e.message, status=e.status, body=e.body)

    if isinstance(e, boto.exception.InvalidUriError):
      # Work around textwrap when searching for this string.
      if e.message and NON_EXISTENT_OBJECT_REGEX.match(e.message):
        return NotFoundException(e.message, status=404)
      return InvalidUrlError(e.message)

    if isinstance(e, boto.exception.ResumableUploadException):
      if e.disposition == boto.exception.ResumableTransferDisposition.ABORT:
        return ResumableUploadAbortException(e.message)
      elif (e.disposition ==
            boto.exception.ResumableTransferDisposition.START_OVER):
        return ResumableUploadStartOverException(e.message)
      else:
        return ResumableUploadException(e.message)

    if isinstance(e, boto.exception.ResumableDownloadException):
      return ResumableDownloadException(e.message)

    return None

  # For function docstrings, see CloudApiDelegator class.
  def XmlPassThroughGetAcl(self, storage_url, def_obj_acl=False):
    """See CloudApiDelegator class for function doc strings."""
    try:
      uri = boto.storage_uri(
          storage_url.url_string,
          suppress_consec_slashes=False,
          bucket_storage_uri_class=self.bucket_storage_uri_class,
          debug=self.debug)
      if def_obj_acl:
        return uri.get_def_acl()
      else:
        return uri.get_acl()
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def XmlPassThroughSetAcl(self,
                           acl_text,
                           storage_url,
                           canned=True,
                           def_obj_acl=False):
    """See CloudApiDelegator class for function doc strings."""
    headers = self._CreateBaseHeaders()
    try:
      uri = boto.storage_uri(
          storage_url.url_string,
          suppress_consec_slashes=False,
          bucket_storage_uri_class=self.bucket_storage_uri_class,
          debug=self.debug)
      if canned:
        if def_obj_acl:
          canned_acls = uri.canned_acls()
          if acl_text not in canned_acls:
            raise CommandException('Invalid canned ACL "%s".' % acl_text)
          uri.set_def_acl(acl_text, uri.object_name, headers=headers)
        else:
          canned_acls = uri.canned_acls()
          if acl_text not in canned_acls:
            raise CommandException('Invalid canned ACL "%s".' % acl_text)
          uri.set_acl(acl_text, uri.object_name, headers=headers)
      else:
        if def_obj_acl:
          uri.set_def_xml_acl(acl_text, uri.object_name, headers=headers)
        else:
          uri.set_xml_acl(acl_text, uri.object_name, headers=headers)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  # pylint: disable=catching-non-exception
  def XmlPassThroughSetCors(self, cors_text, storage_url):
    """See CloudApiDelegator class for function doc strings."""
    headers = self._CreateBaseHeaders()
    # Parse XML document and convert into Cors object.
    if storage_url.scheme == 's3':
      cors_obj = S3Cors()
    else:
      cors_obj = Cors()
    h = handler.XmlHandler(cors_obj, None)
    try:
      xml.sax.parseString(cors_text, h)
    except SaxExceptions.SAXParseException as e:
      raise CommandException(
          'Requested CORS is invalid: %s at line %s, '
          'column %s' %
          (e.getMessage(), e.getLineNumber(), e.getColumnNumber()))

    try:
      uri = boto.storage_uri(
          storage_url.url_string,
          suppress_consec_slashes=False,
          bucket_storage_uri_class=self.bucket_storage_uri_class,
          debug=self.debug)
      uri.set_cors(cors_obj, False, headers=headers)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def XmlPassThroughGetCors(self, storage_url):
    """See CloudApiDelegator class for function doc strings."""
    headers = self._CreateBaseHeaders()
    uri = boto.storage_uri(
        storage_url.url_string,
        suppress_consec_slashes=False,
        bucket_storage_uri_class=self.bucket_storage_uri_class,
        debug=self.debug)
    try:
      cors = uri.get_cors(False, headers=headers)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

    parsed_xml = xml.dom.minidom.parseString(cors.to_xml().encode(UTF8))
    # Pretty-print the XML to make it more easily human editable.
    return parsed_xml.toprettyxml(indent='    ')

  def XmlPassThroughGetLifecycle(self, storage_url):
    """See CloudApiDelegator class for function doc strings."""
    headers = self._CreateBaseHeaders()
    try:
      uri = boto.storage_uri(
          storage_url.url_string,
          suppress_consec_slashes=False,
          bucket_storage_uri_class=self.bucket_storage_uri_class,
          debug=self.debug)
      lifecycle = uri.get_lifecycle_config(False, headers=headers)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

    parsed_xml = xml.dom.minidom.parseString(lifecycle.to_xml().encode(UTF8))
    # Pretty-print the XML to make it more easily human editable.
    return parsed_xml.toprettyxml(indent='    ')

  def XmlPassThroughSetLifecycle(self, lifecycle_text, storage_url):
    """See CloudApiDelegator class for function doc strings."""
    headers = self._CreateBaseHeaders()
    # Parse XML document and convert into lifecycle object.
    if storage_url.scheme == 's3':
      lifecycle_obj = S3Lifecycle()
    else:
      lifecycle_obj = LifecycleConfig()
    h = handler.XmlHandler(lifecycle_obj, None)
    try:
      xml.sax.parseString(lifecycle_text, h)
    except SaxExceptions.SAXParseException as e:
      raise CommandException(
          'Requested lifecycle config is invalid: %s at line %s, column %s' %
          (e.getMessage(), e.getLineNumber(), e.getColumnNumber()))

    try:
      uri = boto.storage_uri(
          storage_url.url_string,
          suppress_consec_slashes=False,
          bucket_storage_uri_class=self.bucket_storage_uri_class,
          debug=self.debug)
      uri.configure_lifecycle(lifecycle_obj, False, headers=headers)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def XmlPassThroughGetLogging(self, storage_url):
    """See CloudApiDelegator class for function doc strings."""
    headers = self._CreateBaseHeaders()
    try:
      uri = boto.storage_uri(
          storage_url.url_string,
          suppress_consec_slashes=False,
          bucket_storage_uri_class=self.bucket_storage_uri_class,
          debug=self.debug)
      logging_config_xml = UnaryDictToXml(
          uri.get_logging_config(headers=headers))
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

    return XmlParseString(logging_config_xml).toprettyxml()

  def XmlPassThroughGetTagging(self, storage_url):
    """See CloudApiDelegator class for function doc strings."""
    headers = self._CreateBaseHeaders()
    try:
      uri = boto.storage_uri(
          storage_url.url_string,
          suppress_consec_slashes=False,
          bucket_storage_uri_class=self.bucket_storage_uri_class,
          debug=self.debug)
      # TODO: Define tags-related methods on storage_uri objects. In the
      # meantime, we invoke the underlying bucket's methods directly.
      tagging_config_xml = uri.get_bucket().get_xml_tags()
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

    return XmlParseString(tagging_config_xml).toprettyxml()

  def XmlPassThroughSetTagging(self, tagging_text, storage_url):
    """See CloudApiDelegator class for function doc strings."""
    headers = self._CreateBaseHeaders()
    tags_obj = Tags()
    h = handler.XmlHandler(tags_obj, None)
    try:
      xml.sax.parseString(tagging_text, h)
    except SaxExceptions.SAXParseException as e:
      raise CommandException(
          'Requested labels/tagging config is invalid: %s at line %s, column '
          '%s' % (e.getMessage(), e.getLineNumber(), e.getColumnNumber()))

    try:
      uri = boto.storage_uri(
          storage_url.url_string,
          suppress_consec_slashes=False,
          bucket_storage_uri_class=self.bucket_storage_uri_class,
          debug=self.debug)
      # TODO: Define tags-related methods on storage_uri objects. In the
      # meantime, we invoke the underlying bucket's methods directly.
      uri.get_bucket().set_tags(tags_obj, headers=headers)
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def XmlPassThroughGetWebsite(self, storage_url):
    """See CloudApiDelegator class for function doc strings."""
    headers = self._CreateBaseHeaders()
    try:
      uri = boto.storage_uri(
          storage_url.url_string,
          suppress_consec_slashes=False,
          bucket_storage_uri_class=self.bucket_storage_uri_class,
          debug=self.debug)
      web_config_xml = UnaryDictToXml(uri.get_website_config(headers=headers))
    except TRANSLATABLE_BOTO_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

    return XmlParseString(web_config_xml).toprettyxml()

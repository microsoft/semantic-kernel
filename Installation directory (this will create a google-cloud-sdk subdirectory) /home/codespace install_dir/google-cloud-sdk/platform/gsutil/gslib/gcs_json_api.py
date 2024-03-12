# -*- coding: utf-8 -*-
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
"""JSON gsutil Cloud API implementation for Google Cloud Storage."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from contextlib import contextmanager
import functools
from six.moves import http_client
import json
import logging
import os
import socket
import ssl
import time
import traceback

import six

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import http_wrapper as apitools_http_wrapper
from apitools.base.py import transfer as apitools_transfer
from apitools.base.py.util import CalculateWaitForRetry
from boto import config
import httplib2
import oauth2client

from gslib import context_config
from gslib.cloud_api import AccessDeniedException
from gslib.cloud_api import ArgumentException
from gslib.cloud_api import BadRequestException
from gslib.cloud_api import CloudApi
from gslib.cloud_api import EncryptionException
from gslib.cloud_api import NotEmptyException
from gslib.cloud_api import NotFoundException
from gslib.cloud_api import PreconditionException
from gslib.cloud_api import Preconditions
from gslib.cloud_api import PublishPermissionDeniedException
from gslib.cloud_api import ResumableDownloadException
from gslib.cloud_api import ResumableUploadAbortException
from gslib.cloud_api import ResumableUploadException
from gslib.cloud_api import ResumableUploadStartOverException
from gslib.cloud_api import ServiceException
from gslib.exception import CommandException
from gslib.gcs_json_credentials import SetUpJsonCredentialsAndCache
from gslib.gcs_json_media import BytesTransferredContainer
from gslib.gcs_json_media import DownloadCallbackConnectionClassFactory
from gslib.gcs_json_media import HttpWithDownloadStream
from gslib.gcs_json_media import HttpWithNoRetries
from gslib.gcs_json_media import UploadCallbackConnectionClassFactory
from gslib.gcs_json_media import WrapDownloadHttpRequest
from gslib.gcs_json_media import WrapUploadHttpRequest
from gslib.impersonation_credentials import ImpersonationCredentials
from gslib.no_op_credentials import NoOpCredentials
from gslib.progress_callback import ProgressCallbackWithTimeout
from gslib.project_id import PopulateProjectId
from gslib.third_party.storage_apitools import storage_v1_client as apitools_client
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.tracker_file import DeleteTrackerFile
from gslib.tracker_file import GetRewriteTrackerFilePath
from gslib.tracker_file import HashRewriteParameters
from gslib.tracker_file import ReadRewriteTrackerFile
from gslib.tracker_file import WriteRewriteTrackerFile
from gslib.utils.boto_util import GetCertsFile
from gslib.utils.boto_util import GetGcsJsonApiVersion
from gslib.utils.boto_util import GetJsonResumableChunkSize
from gslib.utils.boto_util import GetMaxRetryDelay
from gslib.utils.boto_util import GetNewHttp
from gslib.utils.boto_util import GetNumRetries
from gslib.utils.boto_util import JsonResumableChunkSizeDefined
from gslib.utils.cloud_api_helper import ListToGetFields
from gslib.utils.cloud_api_helper import ValidateDstObjectMetadata
from gslib.utils.constants import IAM_POLICY_VERSION
from gslib.utils.constants import NUM_OBJECTS_PER_LIST_PAGE
from gslib.utils.constants import REQUEST_REASON_ENV_VAR
from gslib.utils.constants import REQUEST_REASON_HEADER_KEY
from gslib.utils.constants import UTF8
from gslib.utils.encryption_helper import Base64Sha256FromBase64EncryptionKey
from gslib.utils.encryption_helper import CryptoKeyType
from gslib.utils.encryption_helper import CryptoKeyWrapperFromKey
from gslib.utils.encryption_helper import FindMatchingCSEKInBotoConfig
from gslib.utils.metadata_util import AddAcceptEncodingGzipIfNeeded
from gslib.utils.retry_util import LogAndHandleRetries
from gslib.utils.signurl_helper import CreatePayload, GetFinalUrl
from gslib.utils.text_util import GetPrintableExceptionString
from gslib.utils.translation_helper import CreateBucketNotFoundException
from gslib.utils.translation_helper import CreateNotFoundExceptionForObjectWrite
from gslib.utils.translation_helper import CreateObjectNotFoundException
from gslib.utils.translation_helper import DEFAULT_CONTENT_TYPE
from gslib.utils.translation_helper import PRIVATE_DEFAULT_OBJ_ACL
from gslib.utils.translation_helper import REMOVE_CORS_CONFIG
from oauth2client.service_account import ServiceAccountCredentials

if six.PY3:
  long = int

# pylint: disable=invalid-name
Notification = apitools_messages.Notification
NotificationCustomAttributesValue = Notification.CustomAttributesValue
NotificationAdditionalProperty = (
    NotificationCustomAttributesValue.AdditionalProperty)

# Implementation supports only 'gs' URLs, so provider is unused.
# pylint: disable=unused-argument

NUM_BUCKETS_PER_LIST_PAGE = 1000

TRANSLATABLE_APITOOLS_EXCEPTIONS = (apitools_exceptions.HttpError,
                                    apitools_exceptions.StreamExhausted,
                                    apitools_exceptions.TransferError,
                                    apitools_exceptions.TransferInvalidError)

# TODO: Distribute these exceptions better through apitools and here.
# Right now, apitools is configured not to handle any exceptions on
# uploads/downloads.
# oauth2_client tries to JSON-decode the response, which can result
# in a ValueError if the response was invalid. Until that is fixed in
# oauth2_client, need to handle it here.
HTTP_TRANSFER_EXCEPTIONS = (
    apitools_exceptions.TransferRetryError,
    apitools_exceptions.BadStatusCodeError,
    # TODO: Honor retry-after headers.
    apitools_exceptions.RetryAfterError,
    apitools_exceptions.RequestError,
    http_client.BadStatusLine,
    http_client.IncompleteRead,
    http_client.ResponseNotReady,
    httplib2.ServerNotFoundError,
    oauth2client.client.HttpAccessTokenRefreshError,
    socket.error,
    socket.gaierror,
    socket.timeout,
    ssl.SSLError,
    ValueError,
)

# Fields requiring projection=full across all API calls.
_ACL_FIELDS_SET = set([
    'acl',
    'defaultObjectAcl',
    'items/acl',
    'items/defaultObjectAcl',
    'items/owner',
    'owner',
])
_BUCKET_PREDEFINED_ACL_XML_TO_JSON_TRANSLATION = {
    None: None,
    'authenticated-read': 'authenticatedRead',
    'private': 'private',
    'project-private': 'projectPrivate',
    'public-read': 'publicRead',
    'public-read-write': 'publicReadWrite'
}
_OBJECT_PREDEFINED_ACL_XML_TO_JSON_TRANSLATION = {
    None: None,
    'authenticated-read': 'authenticatedRead',
    'bucket-owner-read': 'bucketOwnerRead',
    'bucket-owner-full-control': 'bucketOwnerFullControl',
    'private': 'private',
    'project-private': 'projectPrivate',
    'public-read': 'publicRead'
}
FULL_PREDEFINED_ACL_XML_TO_JSON_TRANSLATION = _BUCKET_PREDEFINED_ACL_XML_TO_JSON_TRANSLATION.copy(
)
FULL_PREDEFINED_ACL_XML_TO_JSON_TRANSLATION.update(
    _OBJECT_PREDEFINED_ACL_XML_TO_JSON_TRANSLATION)

# Fields that may be encrypted.
_ENCRYPTED_HASHES_SET = set(['crc32c', 'md5Hash'])

# During listing, if we attempt to decrypt an object but it has been removed,
# we skip including the object in the listing.
_SKIP_LISTING_OBJECT = 'skip'

_INSUFFICIENT_OAUTH2_SCOPE_MESSAGE = (
    'Insufficient OAuth2 scope to perform this operation.')

DEFAULT_HOST = 'storage.googleapis.com'
MTLS_HOST = 'storage.mtls.googleapis.com'


class GcsJsonApi(CloudApi):
  """Google Cloud Storage JSON implementation of gsutil Cloud API."""

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
    """Performs necessary setup for interacting with Google Cloud Storage.

    Args:
      bucket_storage_uri_class: Unused.
      logger: logging.logger for outputting log messages.
      status_queue: Queue for relaying status to UI.
      provider: Unused.  This implementation supports only Google Cloud Storage.
      credentials: Credentials to be used for interacting with Google Cloud
                   Storage.
      debug: Debug level for the API implementation (0..3).
      http_headers (dict|None): Arbitrary headers to be included in every request.
      trace_token: Trace token to pass to the API implementation.
      perf_trace_token: Performance trace token to use when making API calls.
      user_project: Project to be billed for this request.
    """
    # TODO: Plumb host_header for perfdiag / test_perfdiag.
    # TODO: Add jitter to apitools' http_wrapper retry mechanism.
    super(GcsJsonApi, self).__init__(bucket_storage_uri_class,
                                     logger,
                                     status_queue,
                                     provider='gs',
                                     debug=debug,
                                     http_headers=http_headers,
                                     trace_token=trace_token,
                                     perf_trace_token=perf_trace_token,
                                     user_project=user_project)

    self.certs_file = GetCertsFile()
    self.http = GetNewHttp()
    SetUpJsonCredentialsAndCache(self, logger, credentials=credentials)

    # Re-use download and upload connections. This class is only called
    # sequentially, but we can share TCP warmed-up connections across calls.
    self.download_http = self._GetNewDownloadHttp()
    self.upload_http = self._GetNewUploadHttp()
    if self.credentials:
      self.authorized_download_http = self.credentials.authorize(
          self.download_http)
      self.authorized_upload_http = self.credentials.authorize(self.upload_http)
    else:
      self.authorized_download_http = self.download_http
      self.authorized_upload_http = self.upload_http
    WrapDownloadHttpRequest(self.authorized_download_http)
    WrapUploadHttpRequest(self.authorized_upload_http)

    self.http_base = 'https://'
    gs_json_host = config.get('Credentials', 'gs_json_host', None)
    if (context_config.get_context_config() and
        context_config.get_context_config().use_client_certificate):
      if gs_json_host:
        raise ArgumentException(
            '"use_client_certificate" is enabled, which sets gsutil to use the'
            ' host {}. However, a custom host was set using'
            ' "gs_json_host": {}. Please set "use_client_certificate" to'
            ' "False" or comment out the "gs_json_host" line in the Boto'
            ' config.'.format(MTLS_HOST, gs_json_host))
      self.host_base = MTLS_HOST
    else:
      self.host_base = gs_json_host or DEFAULT_HOST

    if not gs_json_host:
      gs_host = config.get('Credentials', 'gs_host', None)
      if gs_host:
        raise ArgumentException(
            'JSON API is selected but gs_json_host is not configured, '
            'while gs_host is configured to %s. Please also configure '
            'gs_json_host and gs_json_port to match your desired endpoint.' %
            gs_host)

    gs_json_port = config.get('Credentials', 'gs_json_port', None)

    if not gs_json_port:
      gs_port = config.get('Credentials', 'gs_port', None)
      if gs_port:
        raise ArgumentException(
            'JSON API is selected but gs_json_port is not configured, '
            'while gs_port is configured to %s. Please also configure '
            'gs_json_host and gs_json_port to match your desired endpoint.' %
            gs_port)
      self.host_port = ''
    else:
      self.host_port = ':' + config.get('Credentials', 'gs_json_port')

    self.api_version = GetGcsJsonApiVersion()
    self.url_base = (self.http_base + self.host_base + self.host_port + '/' +
                     'storage/' + self.api_version + '/')

    self.global_params = apitools_messages.StandardQueryParameters(
        trace='token:%s' % trace_token) if trace_token else None

    additional_http_headers = {}

    gs_json_host_header = config.get('Credentials', 'gs_json_host_header', None)
    if gs_json_host_header and gs_json_host:
      additional_http_headers['Host'] = gs_json_host_header

    self._UpdateHeaders(additional_http_headers)

    log_request = (debug >= 3)
    log_response = (debug >= 3)

    self.api_client = apitools_client.StorageV1(
        url=self.url_base,
        http=self.http,
        log_request=log_request,
        log_response=log_response,
        credentials=self.credentials,
        version=self.api_version,
        default_global_params=self.global_params,
        additional_http_headers=additional_http_headers)

    self.max_retry_wait = GetMaxRetryDelay()
    self.api_client.max_retry_wait = self.max_retry_wait

    self.num_retries = GetNumRetries()
    self.api_client.num_retries = self.num_retries

    self.api_client.retry_func = LogAndHandleRetries(
        status_queue=self.status_queue)
    self.api_client.overwrite_transfer_urls_with_client_base = True

    if isinstance(self.credentials, NoOpCredentials):
      # This API key is not secret and is used to identify gsutil during
      # anonymous requests.
      self.api_client.AddGlobalParam('key',
                                     'AIzaSyDnacJHrKma0048b13sh8cgxNUwulubmJM')

  def GetServiceAccountId(self):
    """Returns the service account email id."""
    if isinstance(self.credentials, ImpersonationCredentials):
      return self.credentials.service_account_id
    elif isinstance(self.credentials, ServiceAccountCredentials):
      return self.credentials.service_account_email
    else:
      raise CommandException(
          'Cannot get service account email id for the given '
          'credential type.')

  def _UpdateHeaders(self, headers):
    if self.http_headers:
      headers.update(self.http_headers)

    # The following functional headers potentially overwrite
    # arbitrary ones provided by -h.
    if self.perf_trace_token:
      headers['cookie'] = self.perf_trace_token

    request_reason = os.environ.get(REQUEST_REASON_ENV_VAR)
    if request_reason:
      headers[REQUEST_REASON_HEADER_KEY] = request_reason

  def _GetNewDownloadHttp(self):
    return GetNewHttp(http_class=HttpWithDownloadStream)

  def _GetNewUploadHttp(self):
    """Returns an upload-safe Http object (by disabling httplib2 retries)."""
    return GetNewHttp(http_class=HttpWithNoRetries)

  def _GetSignedContent(self, string_to_sign):
    """Returns the Signed Content."""
    if isinstance(self.credentials, ImpersonationCredentials):
      iam_cred_api = self.credentials.api
      service_account_id = self.credentials.service_account_id
      response = iam_cred_api.SignBlob(service_account_id, string_to_sign)
      return response.keyId, response.signedBlob
    elif isinstance(self.credentials, ServiceAccountCredentials):
      return self.credentials.sign_blob(string_to_sign)
    else:
      raise CommandException(
          'Authentication using a service account is required for signing '
          'the content.')

  def _FieldsContainsAclField(self, fields=None):
    """Checks Returns true if ACL related values are in fields set.

    Args:
      fields: list or set of fields. May be in GET ['acl'] or List
          ['items/acl'] call format.

    Returns:
      True if an ACL value is requested in the input fields, False otherwise.
    """
    return fields is None or _ACL_FIELDS_SET.intersection(set(fields))

  def _ValidateEncryptionFieldsForMetadataGetRequest(self, fields=None):
    """Ensures customerEncryption field is included if hashes are requested."""
    # In the context of fetching object metadata, we only need to check for
    # customerEncryption, the field present if an object is CSEK-encrypted. Note
    # that if the object is KMS-encrypted, no field checks are necessary; a
    # metadata get request will be able to access the object's stored kmsKeyName
    # field to access the key needed to decrypt hash fields).
    if (fields and _ENCRYPTED_HASHES_SET.intersection(set(fields)) and
        'customerEncryption' not in fields):
      raise ArgumentException(
          'gsutil client error: customerEncryption must be included when '
          'requesting potentially encrypted fields %s' % _ENCRYPTED_HASHES_SET)

  def GetBucketIamPolicy(self, bucket_name, provider=None, fields=None):
    apitools_request = apitools_messages.StorageBucketsGetIamPolicyRequest(
        bucket=bucket_name,
        userProject=self.user_project,
        optionsRequestedPolicyVersion=IAM_POLICY_VERSION)
    global_params = apitools_messages.StandardQueryParameters()
    if fields:
      global_params.fields = ','.join(set(fields))
    try:
      return self.api_client.buckets.GetIamPolicy(apitools_request,
                                                  global_params=global_params)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

  def GetObjectIamPolicy(self,
                         bucket_name,
                         object_name,
                         generation=None,
                         provider=None,
                         fields=None):
    if generation is not None:
      generation = long(generation)
    apitools_request = apitools_messages.StorageObjectsGetIamPolicyRequest(
        bucket=bucket_name,
        object=object_name,
        generation=generation,
        userProject=self.user_project)
    global_params = apitools_messages.StandardQueryParameters()
    if fields:
      global_params.fields = ','.join(set(fields))
    try:
      return self.api_client.objects.GetIamPolicy(apitools_request,
                                                  global_params=global_params)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=bucket_name,
                                       object_name=object_name,
                                       generation=generation)

  def SetObjectIamPolicy(self,
                         bucket_name,
                         object_name,
                         policy,
                         generation=None,
                         provider=None):
    if generation is not None:
      generation = long(generation)
    api_request = apitools_messages.StorageObjectsSetIamPolicyRequest(
        bucket=bucket_name,
        object=object_name,
        generation=generation,
        policy=policy,
        userProject=self.user_project)
    global_params = apitools_messages.StandardQueryParameters()
    try:
      return self.api_client.objects.SetIamPolicy(api_request,
                                                  global_params=global_params)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=bucket_name,
                                       object_name=object_name)

  def SetBucketIamPolicy(self, bucket_name, policy, provider=None):
    apitools_request = apitools_messages.StorageBucketsSetIamPolicyRequest(
        bucket=bucket_name, policy=policy, userProject=self.user_project)
    global_params = apitools_messages.StandardQueryParameters()
    try:
      return self.api_client.buckets.SetIamPolicy(apitools_request,
                                                  global_params=global_params)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

  def SignUrl(self, method, duration, path, generation, logger, region,
              signed_headers, string_to_sign_debug):
    """See CloudApi class for function doc strings."""
    service_account_id = self.GetServiceAccountId()
    string_to_sign, canonical_query_string = CreatePayload(
        client_id=service_account_id,
        method=method,
        duration=duration,
        path=path,
        generation=generation,
        logger=logger,
        region=region,
        signed_headers=signed_headers,
        string_to_sign_debug=string_to_sign_debug)

    if six.PY3:
      string_to_sign = string_to_sign.encode(UTF8)

    key_id, raw_signature = self._GetSignedContent(string_to_sign)
    logger.debug('Key ID used to sign blob for service account "%s": "%s"' %
                 (service_account_id, key_id))
    return GetFinalUrl(raw_signature, signed_headers['host'], path,
                       canonical_query_string)

  def GetBucket(self, bucket_name, provider=None, fields=None):
    """See CloudApi class for function doc strings."""
    projection = (apitools_messages.StorageBucketsGetRequest.
                  ProjectionValueValuesEnum.noAcl)
    if self._FieldsContainsAclField(fields):
      projection = (apitools_messages.StorageBucketsGetRequest.
                    ProjectionValueValuesEnum.full)
    apitools_request = apitools_messages.StorageBucketsGetRequest(
        bucket=bucket_name,
        projection=projection,
        userProject=self.user_project)
    global_params = apitools_messages.StandardQueryParameters()
    if fields:
      global_params.fields = ','.join(set(fields))

    # Here and in list buckets, we have no way of knowing
    # whether we requested a field and didn't get it because it didn't exist
    # or because we didn't have permission to access it.
    try:
      return self.api_client.buckets.Get(apitools_request,
                                         global_params=global_params)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

  def ListBucketAccessControls(self, bucket_name):
    """See CloudApi class for function doc strings."""
    try:
      request = apitools_messages.StorageBucketAccessControlsListRequest(
          bucket=bucket_name)
      return self.api_client.bucketAccessControls.List(request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

  def ListObjectAccessControls(self, bucket_name, object_name):
    """See CloudApi class for function doc strings."""
    try:
      request = apitools_messages.StorageObjectAccessControlsListRequest(
          bucket=bucket_name, object=object_name)
      return self.api_client.objectAccessControls.List(request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=bucket_name,
                                       object_name=object_name)

  def PatchBucket(self,
                  bucket_name,
                  metadata,
                  canned_acl=None,
                  canned_def_acl=None,
                  preconditions=None,
                  provider=None,
                  fields=None):
    """See CloudApi class for function doc strings."""
    projection = (apitools_messages.StorageBucketsPatchRequest.
                  ProjectionValueValuesEnum.noAcl)
    if self._FieldsContainsAclField(fields):
      projection = (apitools_messages.StorageBucketsPatchRequest.
                    ProjectionValueValuesEnum.full)
    bucket_metadata = metadata

    if not preconditions:
      preconditions = Preconditions()

    # For blank metadata objects, we need to explicitly call
    # them out to apitools so it will send/erase them.
    apitools_include_fields = []
    for metadata_field in (
        'billing',
        'encryption',
        'lifecycle',
        'logging',
        'metadata',
        'retentionPolicy',
        'versioning',
        'website',
    ):
      attr = getattr(bucket_metadata, metadata_field, None)
      if attr and not encoding.MessageToDict(attr):
        setattr(bucket_metadata, metadata_field, None)
        apitools_include_fields.append(metadata_field)

    if bucket_metadata.cors and bucket_metadata.cors == REMOVE_CORS_CONFIG:
      bucket_metadata.cors = []
      apitools_include_fields.append('cors')

    if (bucket_metadata.defaultObjectAcl and
        bucket_metadata.defaultObjectAcl[0] == PRIVATE_DEFAULT_OBJ_ACL):
      bucket_metadata.defaultObjectAcl = []
      apitools_include_fields.append('defaultObjectAcl')

    predefined_acl = None
    if canned_acl:
      # Must null out existing ACLs to apply a canned ACL.
      apitools_include_fields.append('acl')
      predefined_acl = (apitools_messages.StorageBucketsPatchRequest.
                        PredefinedAclValueValuesEnum(
                            self._BucketCannedAclToPredefinedAcl(canned_acl)))

    predefined_def_acl = None
    if canned_def_acl:
      # Must null out existing default object ACLs to apply a canned ACL.
      apitools_include_fields.append('defaultObjectAcl')
      predefined_def_acl = (
          apitools_messages.StorageBucketsPatchRequest.
          PredefinedDefaultObjectAclValueValuesEnum(
              self._ObjectCannedAclToPredefinedAcl(canned_def_acl)))

    apitools_request = apitools_messages.StorageBucketsPatchRequest(
        bucket=bucket_name,
        bucketResource=bucket_metadata,
        projection=projection,
        ifMetagenerationMatch=preconditions.meta_gen_match,
        predefinedAcl=predefined_acl,
        predefinedDefaultObjectAcl=predefined_def_acl,
        userProject=self.user_project)
    global_params = apitools_messages.StandardQueryParameters()
    if fields:
      global_params.fields = ','.join(set(fields))
    with self.api_client.IncludeFields(apitools_include_fields):
      try:
        return self.api_client.buckets.Patch(apitools_request,
                                             global_params=global_params)
      except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
        self._TranslateExceptionAndRaise(e)

  def LockRetentionPolicy(self, bucket_name, metageneration, provider=None):
    try:
      metageneration = long(metageneration)
    except ValueError:
      raise ArgumentException(
          'LockRetentionPolicy Metageneration must be an integer.')

    apitools_request = (
        apitools_messages.StorageBucketsLockRetentionPolicyRequest(
            bucket=bucket_name,
            ifMetagenerationMatch=metageneration,
            userProject=self.user_project))
    global_params = apitools_messages.StandardQueryParameters()
    try:
      return self.api_client.buckets.LockRetentionPolicy(
          apitools_request, global_params=global_params)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

  def CreateBucket(self,
                   bucket_name,
                   project_id=None,
                   metadata=None,
                   provider=None,
                   fields=None):
    """See CloudApi class for function doc strings."""
    projection = (apitools_messages.StorageBucketsInsertRequest.
                  ProjectionValueValuesEnum.noAcl)
    if self._FieldsContainsAclField(fields):
      projection = (apitools_messages.StorageBucketsInsertRequest.
                    ProjectionValueValuesEnum.full)
    if not metadata:
      metadata = apitools_messages.Bucket()
    metadata.name = bucket_name

    if metadata.location:
      metadata.location = metadata.location.lower()
    if metadata.storageClass:
      metadata.storageClass = metadata.storageClass.lower()

    project_id = PopulateProjectId(project_id)

    apitools_request = apitools_messages.StorageBucketsInsertRequest(
        bucket=metadata,
        project=project_id,
        projection=projection,
        userProject=self.user_project)
    global_params = apitools_messages.StandardQueryParameters()
    if fields:
      global_params.fields = ','.join(set(fields))
    try:
      return self.api_client.buckets.Insert(apitools_request,
                                            global_params=global_params)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

  def DeleteBucket(self, bucket_name, preconditions=None, provider=None):
    """See CloudApi class for function doc strings."""
    if not preconditions:
      preconditions = Preconditions()

    apitools_request = apitools_messages.StorageBucketsDeleteRequest(
        bucket=bucket_name,
        ifMetagenerationMatch=preconditions.meta_gen_match,
        userProject=self.user_project)

    try:
      self.api_client.buckets.Delete(apitools_request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      if isinstance(
          self._TranslateApitoolsException(e, bucket_name=bucket_name),
          NotEmptyException):
        # If bucket is not empty, check to see if versioning is enabled and
        # signal that in the exception if it is.
        bucket_metadata = self.GetBucket(bucket_name, fields=['versioning'])
        if bucket_metadata.versioning and bucket_metadata.versioning.enabled:
          raise NotEmptyException('VersionedBucketNotEmpty',
                                  status=e.status_code)
      self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

  def ListBuckets(self, project_id=None, provider=None, fields=None):
    """See CloudApi class for function doc strings."""
    projection = (apitools_messages.StorageBucketsListRequest.
                  ProjectionValueValuesEnum.noAcl)
    if self._FieldsContainsAclField(fields):
      projection = (apitools_messages.StorageBucketsListRequest.
                    ProjectionValueValuesEnum.full)
    project_id = PopulateProjectId(project_id)

    apitools_request = apitools_messages.StorageBucketsListRequest(
        project=project_id,
        maxResults=NUM_BUCKETS_PER_LIST_PAGE,
        projection=projection,
        userProject=self.user_project)
    global_params = apitools_messages.StandardQueryParameters()
    if fields:
      if 'nextPageToken' not in fields:
        fields.add('nextPageToken')
      global_params.fields = ','.join(set(fields))
    try:
      bucket_list = self.api_client.buckets.List(apitools_request,
                                                 global_params=global_params)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

    for bucket in self._YieldBuckets(bucket_list):
      yield bucket

    while bucket_list.nextPageToken:
      apitools_request = apitools_messages.StorageBucketsListRequest(
          project=project_id,
          pageToken=bucket_list.nextPageToken,
          maxResults=NUM_BUCKETS_PER_LIST_PAGE,
          projection=projection,
          userProject=self.user_project)
      try:
        bucket_list = self.api_client.buckets.List(apitools_request,
                                                   global_params=global_params)
      except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
        self._TranslateExceptionAndRaise(e)

      for bucket in self._YieldBuckets(bucket_list):
        yield bucket

  def _YieldBuckets(self, bucket_list):
    """Yields buckets from a list returned by apitools."""
    if bucket_list.items:
      for bucket in bucket_list.items:
        yield bucket

  def ListObjects(self,
                  bucket_name,
                  prefix=None,
                  delimiter=None,
                  all_versions=None,
                  provider=None,
                  fields=None):
    """See CloudApi class for function doc strings."""
    projection = (apitools_messages.StorageObjectsListRequest.
                  ProjectionValueValuesEnum.noAcl)
    if self._FieldsContainsAclField(fields):
      projection = (apitools_messages.StorageObjectsListRequest.
                    ProjectionValueValuesEnum.full)
    apitools_request = apitools_messages.StorageObjectsListRequest(
        bucket=bucket_name,
        prefix=prefix,
        delimiter=delimiter,
        versions=all_versions,
        projection=projection,
        maxResults=NUM_OBJECTS_PER_LIST_PAGE,
        userProject=self.user_project)
    global_params = apitools_messages.StandardQueryParameters()

    if fields:
      fields = set(fields)
      if 'nextPageToken' not in fields:
        fields.add('nextPageToken')
      if ListToGetFields(
          list_fields=fields).intersection(_ENCRYPTED_HASHES_SET):
        # We may need to make a follow-up request to decrypt the hashes,
        # so ensure the required fields are present.
        fields.add('items/customerEncryption')
        fields.add('items/kmsKeyName')
        fields.add('items/generation')
        fields.add('items/name')
      global_params.fields = ','.join(fields)

    list_page = True
    next_page_token = None

    while list_page:
      list_page = False
      apitools_request = apitools_messages.StorageObjectsListRequest(
          bucket=bucket_name,
          prefix=prefix,
          delimiter=delimiter,
          versions=all_versions,
          projection=projection,
          pageToken=next_page_token,
          maxResults=NUM_OBJECTS_PER_LIST_PAGE,
          userProject=self.user_project)
      try:
        object_list = self.api_client.objects.List(apitools_request,
                                                   global_params=global_params)
      except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
        self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

      if object_list.nextPageToken:
        list_page = True
        next_page_token = object_list.nextPageToken

      for object_or_prefix in self._YieldObjectsAndPrefixes(object_list):
        if object_or_prefix.datatype == CloudApi.CsObjectOrPrefixType.OBJECT:
          decrypted_metadata = self._DecryptHashesIfPossible(
              bucket_name,
              object_or_prefix.data,
              fields=ListToGetFields(fields))
          if decrypted_metadata == _SKIP_LISTING_OBJECT:
            continue
          elif decrypted_metadata:
            object_or_prefix.data = decrypted_metadata
          else:
            # Object metadata was unencrypted or we did not have a matching
            # key; yield what we received in the initial listing.
            pass

        yield object_or_prefix

  def _DecryptHashesIfPossible(self, bucket_name, object_metadata, fields=None):
    """Attempts to decrypt object metadata.

    Helps fetch encrypted object metadata fields (if requested) for API method
    calls that requested them but did not receive them; this occurs for
    ListObjects(), along with GetObjectMetadata() calls for which the object is
    CSEK-encrypted but no decryption information was supplied.

    This method issues a StorageObjectsGetRequest (if object hash fields were
    requested but not retrieved), formatted appropriately depending on the
    encryption method.

    Args:
      bucket_name: String of bucket containing the object.
      object_metadata: apitools Object describing the object. Must include
          name, generation, and customerEncryption fields.
      fields: ListObjects-format fields to return.

    Returns:
      - apitools_messages.Object with decrypted hash fields if decryption was
      performed.
      - None if the object was not encrypted, or CSEK-encrypted but we could not
      find a matching decryption key.
      - gcs_json_api._SKIP_LISTING_OBJECT if the object no longer exists.
    """
    get_fields = ListToGetFields(list_fields=fields)

    if not self._ObjectIsEncrypted(object_metadata):
      self._RaiseIfNoDesiredHashesPresentForUnencryptedObject(object_metadata,
                                                              fields=get_fields)
      return None

    # If we reach this point, we know the object is encrypted.
    get_metadata_func = None
    if self._ObjectKMSEncryptedAndNeedHashes(object_metadata,
                                             fields=get_fields):
      # For CMK-encrypted objects, we can just call GetObjectMetadata.
      get_metadata_func = functools.partial(
          self._GetObjectMetadataHelper,
          bucket_name,
          object_metadata.name,
          generation=object_metadata.generation,
          fields=get_fields)
    elif self._ObjectCSEKEncryptedAndNeedHashes(object_metadata,
                                                fields=get_fields):
      # For CSEK-encrypted objects, we can do almost the same thing as above,
      # but we also need to add some info about the decryption key (if it's
      # available) into the request.
      key_sha256 = object_metadata.customerEncryption.keySha256
      if six.PY3:
        if not isinstance(key_sha256, bytes):
          key_sha256 = key_sha256.encode('ascii')
      decryption_key = FindMatchingCSEKInBotoConfig(key_sha256, config)
      if decryption_key:
        get_metadata_func = functools.partial(
            self._GetObjectMetadataHelper,
            bucket_name,
            object_metadata.name,
            generation=object_metadata.generation,
            fields=get_fields,
            decryption_tuple=CryptoKeyWrapperFromKey(decryption_key))

    if get_metadata_func is None:
      return

    try:
      return get_metadata_func()
    except NotFoundException:
      # If the object was deleted between the listing request and
      # the get request, do not include it in the list.
      return _SKIP_LISTING_OBJECT

  def _YieldObjectsAndPrefixes(self, object_list):
    # ls depends on iterating objects before prefixes for proper display.
    if object_list.items:
      for cloud_obj in object_list.items:
        yield CloudApi.CsObjectOrPrefix(cloud_obj,
                                        CloudApi.CsObjectOrPrefixType.OBJECT)
    if object_list.prefixes:
      for prefix in object_list.prefixes:
        yield CloudApi.CsObjectOrPrefix(prefix,
                                        CloudApi.CsObjectOrPrefixType.PREFIX)

  @contextmanager
  def _ApitoolsRequestHeaders(self, headers):
    """Wrapped code makes apitools requests with the specified headers."""
    if headers:
      old_headers = self.api_client.additional_http_headers.copy()
      self.api_client.additional_http_headers.update(headers)
    yield
    if headers:
      self.api_client.additional_http_headers = old_headers

  def _EncryptionHeadersFromTuple(self, crypto_tuple=None):
    """Returns headers dict matching crypto_tuple, or empty dict."""
    headers = {}
    if crypto_tuple and crypto_tuple.crypto_type == CryptoKeyType.CSEK:
      headers['x-goog-encryption-algorithm'] = crypto_tuple.crypto_alg
      headers['x-goog-encryption-key'] = crypto_tuple.crypto_key
      headers['x-goog-encryption-key-sha256'] = (
          Base64Sha256FromBase64EncryptionKey(crypto_tuple.crypto_key))
    return headers

  def _RewriteCryptoHeadersFromTuples(self,
                                      decryption_tuple=None,
                                      encryption_tuple=None):
    """Returns headers dict matching the provided tuples, or empty dict."""
    headers = {}
    if decryption_tuple and decryption_tuple.crypto_type == CryptoKeyType.CSEK:
      headers['x-goog-copy-source-encryption-algorithm'] = (
          decryption_tuple.crypto_alg)
      headers['x-goog-copy-source-encryption-key'] = (
          decryption_tuple.crypto_key)
      headers['x-goog-copy-source-encryption-key-sha256'] = (
          decryption_tuple.crypto_key_sha256)

    if encryption_tuple and encryption_tuple.crypto_type == CryptoKeyType.CSEK:
      headers['x-goog-encryption-algorithm'] = encryption_tuple.crypto_alg
      headers['x-goog-encryption-key'] = encryption_tuple.crypto_key
      headers['x-goog-encryption-key-sha256'] = (
          encryption_tuple.crypto_key_sha256)

    return headers

  def _GetObjectMetadataHelper(self,
                               bucket_name,
                               object_name,
                               generation=None,
                               fields=None,
                               decryption_tuple=None):
    """Get metadata, adding necessary headers for CSEK decryption if necessary.

    Args:
      bucket_name: (str) Bucket containing the object.
      object_name: (str) Object name.
      generation: (int) Generation of the object to retrieve.
      fields: (list<str>) If present, return only these Object metadata fields,
          for example: ['acl', 'updated'].
      decryption_tuple: (gslib.utils.encryption_helper.CryptoKeyWrapper) The
          CryptoKeyWrapper for the desired decryption key.

    Raises:
      ArgumentException for errors during input validation.
      ServiceException for errors interacting with cloud storage providers.

    Returns:
      (apitools_message.Object) The retrieved object metadata.
    """
    apitools_request = self._CreateApitoolsObjectMetadataGetRequest(
        bucket_name, object_name, generation=generation, fields=fields)
    global_params = self._GetApitoolsObjectMetadataGlobalParams(fields=fields)

    try:
      # Add special headers if fetching metadata for a CSEK-encrypted object.
      if decryption_tuple:
        with self._ApitoolsRequestHeaders(
            self._EncryptionHeadersFromTuple(crypto_tuple=decryption_tuple)):
          return self.api_client.objects.Get(apitools_request,
                                             global_params=global_params)
      else:
        return self.api_client.objects.Get(apitools_request,
                                           global_params=global_params)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=bucket_name,
                                       object_name=object_name,
                                       generation=generation)

  def _CreateApitoolsObjectMetadataGetRequest(self,
                                              bucket_name,
                                              object_name,
                                              generation=None,
                                              fields=None):
    self._ValidateEncryptionFieldsForMetadataGetRequest(fields=fields)
    projection = (apitools_messages.StorageObjectsGetRequest.
                  ProjectionValueValuesEnum.noAcl)
    if self._FieldsContainsAclField(fields):
      projection = (apitools_messages.StorageObjectsGetRequest.
                    ProjectionValueValuesEnum.full)
    if generation:
      generation = long(generation)

    return apitools_messages.StorageObjectsGetRequest(
        bucket=bucket_name,
        object=object_name,
        projection=projection,
        generation=generation,
        userProject=self.user_project)

  def _GetApitoolsObjectMetadataGlobalParams(self, fields=None):
    global_params = apitools_messages.StandardQueryParameters()
    if fields:
      global_params.fields = ','.join(set(fields))
    return global_params

  def GetObjectMetadata(self,
                        bucket_name,
                        object_name,
                        generation=None,
                        provider=None,
                        fields=None):
    """See CloudApi class for function doc strings."""
    try:
      object_metadata = self._GetObjectMetadataHelper(bucket_name,
                                                      object_name,
                                                      generation=generation,
                                                      fields=fields)
      if not self._ObjectCSEKEncryptedAndNeedHashes(object_metadata,
                                                    fields=fields):
        return object_metadata

      # CSEK-encrypted objects require corresponding decryption information to
      # be added to the StorageObjectsGetRequest in order to retrieve hash
      # fields.
      key_sha256 = object_metadata.customerEncryption.keySha256
      if six.PY3:
        if not isinstance(key_sha256, bytes):
          key_sha256 = key_sha256.encode('ascii')
      decryption_key = FindMatchingCSEKInBotoConfig(key_sha256, config)
      if not decryption_key:
        raise EncryptionException(
            'Missing decryption key with SHA256 hash %s. No decryption key '
            'matches object %s://%s/%s' %
            (key_sha256, self.provider, bucket_name, object_name))
      if six.PY3:
        if not isinstance(decryption_key, bytes):
          decryption_key = decryption_key.encode(UTF8)
      return self._GetObjectMetadataHelper(
          bucket_name,
          object_name,
          generation=generation,
          fields=fields,
          decryption_tuple=CryptoKeyWrapperFromKey(decryption_key))
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=bucket_name,
                                       object_name=object_name,
                                       generation=generation)

  def _ObjectIsEncrypted(self, object_metadata):
    return bool(object_metadata.customerEncryption or
                object_metadata.kmsKeyName)

  def _RaiseIfNoDesiredHashesPresentForUnencryptedObject(
      self, object_metadata, fields=None):
    """Raise an exception if none of the desired hash fields are present."""
    if fields is None:
      return

    md5_requested_but_missing = ('md5Hash' in fields and
                                 not object_metadata.md5Hash)
    crc32c_requested_but_missing = ('crc32c' in fields and
                                    not object_metadata.crc32c)

    # md5 not available for composite objects; in this case, don't raise an
    # exception if that was the only hash we requested.
    if (md5_requested_but_missing and not object_metadata.componentCount and
        crc32c_requested_but_missing):
      raise ServiceException(
          'Service did not provide requested hashes in metadata for '
          'unencrypted object %s' % object_metadata.name)

  def _ObjectKMSEncryptedAndNeedHashes(self, object_metadata, fields=None):
    """Checks if an object is KMS-encrypted and lacking requested hash fields.

    Args:
      object_metadata: (apitools_messages.Object) Object metadata returned from
          an API call; may or may not contain hash-related metadata fields.
      fields: (list<str>) Requested object metadata fields.

    Returns:
      True if a GetObjectMetadata request should be issued on the KMS-encrypted
      object in order to retrieve encrypted hash fields, False otherwise.
    """
    if fields is not None and not _ENCRYPTED_HASHES_SET.intersection(fields):
      # No potentially encrypted metadata fields were requested.
      return False

    return (object_metadata.kmsKeyName and not object_metadata.crc32c and
            not object_metadata.md5Hash)

  def _ObjectCSEKEncryptedAndNeedHashes(self, object_metadata, fields=None):
    """Checks if an object is CSEK-encrypted and lacking requested hash fields.

    Args:
      object_metadata: (apitools_messages.Object) Object metadata returned from
          an API call; may or may not contain hash-related metadata fields.
      fields: (list<str>) Requested object metadata fields.

    Returns:
      True if a GetObjectMetadata request including a decryption key should be
      issued on the CSEK-encrypted object in order to retrieve encrypted hash
      fields, False otherwise.
    """
    if fields is None or not _ENCRYPTED_HASHES_SET.intersection(fields):
      # No potentially encrypted metadata fields were requested.
      return False

    return (object_metadata.customerEncryption and
            not object_metadata.crc32c and not object_metadata.md5Hash)

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
    if generation:
      generation = long(generation)

    # 'outer_total_size' is only used for formatting user output, and is
    # expected to be one higher than the last byte that should be downloaded.
    # TODO: Change DownloadCallbackConnectionClassFactory and progress callbacks
    # to more elegantly handle total size for components of files.
    outer_total_size = object_size
    if end_byte:
      outer_total_size = end_byte + 1
    elif serialization_data:
      outer_total_size = json.loads(
          six.ensure_str(serialization_data))['total_size']

    if progress_callback:
      if outer_total_size is None:
        raise ArgumentException('Download size is required when callbacks are '
                                'requested for a download, but no size was '
                                'provided.')
      progress_callback(start_byte, outer_total_size)

    bytes_downloaded_container = BytesTransferredContainer()
    bytes_downloaded_container.bytes_transferred = start_byte

    callback_class_factory = DownloadCallbackConnectionClassFactory(
        bytes_downloaded_container,
        total_size=outer_total_size,
        progress_callback=progress_callback,
        digesters=digesters)
    download_http_class = callback_class_factory.GetConnectionClass()

    # Point our download HTTP at our download stream.
    self.download_http.stream = download_stream
    self.download_http.connections = {'https': download_http_class}

    if serialization_data:
      # If we have an apiary trace token, add it to the URL.
      # TODO: Add query parameter support to apitools downloads so there is
      # a well-defined way to express query parameters. Currently, we assume
      # the URL ends in ?alt=media, and this will break if that changes.
      if self.trace_token:
        serialization_dict = json.loads(six.ensure_str(serialization_data))
        serialization_dict['url'] += '&trace=token%%3A%s' % self.trace_token
        serialization_data = json.dumps(serialization_dict)

      apitools_download = apitools_transfer.Download.FromData(
          download_stream,
          serialization_data,
          self.api_client.http,
          num_retries=self.num_retries,
          client=self.api_client)
    else:
      apitools_download = apitools_transfer.Download.FromStream(
          download_stream,
          auto_transfer=False,
          total_size=object_size,
          num_retries=self.num_retries)

    apitools_download.bytes_http = self.authorized_download_http
    apitools_request = apitools_messages.StorageObjectsGetRequest(
        bucket=bucket_name,
        object=object_name,
        generation=generation,
        userProject=self.user_project)

    # Disable retries in apitools. We will handle them explicitly for
    # resumable downloads; one-shot downloads are not retryable as we do
    # not track how many bytes were written to the stream.
    apitools_download.retry_func = LogAndHandleRetries(
        is_data_transfer=True, status_queue=self.status_queue)

    try:
      if download_strategy == CloudApi.DownloadStrategy.RESUMABLE:
        return self._PerformResumableDownload(
            bucket_name,
            object_name,
            download_stream,
            apitools_request,
            apitools_download,
            bytes_downloaded_container,
            compressed_encoding=compressed_encoding,
            generation=generation,
            start_byte=start_byte,
            end_byte=end_byte,
            serialization_data=serialization_data,
            decryption_tuple=decryption_tuple)
      else:
        return self._PerformDownload(bucket_name,
                                     object_name,
                                     download_stream,
                                     apitools_request,
                                     apitools_download,
                                     generation=generation,
                                     compressed_encoding=compressed_encoding,
                                     start_byte=start_byte,
                                     end_byte=end_byte,
                                     serialization_data=serialization_data,
                                     decryption_tuple=decryption_tuple)
    # If you are fighting a redacted exception spew in multiprocess/multithread
    # calls, add your exception to TRANSLATABLE_APITOOLS_EXCEPTIONS and put
    # something like this immediately after the following except statement:
    # import sys, traceback; sys.stderr.write('\n{}\n'.format(
    #     traceback.format_exc())); sys.stderr.flush()
    # This may hang, but you should get a stack trace spew after Ctrl-C.
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=bucket_name,
                                       object_name=object_name,
                                       generation=generation)

  def _PerformResumableDownload(self,
                                bucket_name,
                                object_name,
                                download_stream,
                                apitools_request,
                                apitools_download,
                                bytes_downloaded_container,
                                generation=None,
                                compressed_encoding=False,
                                start_byte=0,
                                end_byte=None,
                                serialization_data=None,
                                decryption_tuple=None):
    retries = 0
    last_progress_byte = start_byte
    while retries <= self.num_retries:
      try:
        return self._PerformDownload(bucket_name,
                                     object_name,
                                     download_stream,
                                     apitools_request,
                                     apitools_download,
                                     generation=generation,
                                     compressed_encoding=compressed_encoding,
                                     start_byte=start_byte,
                                     end_byte=end_byte,
                                     serialization_data=serialization_data,
                                     decryption_tuple=decryption_tuple)
      except HTTP_TRANSFER_EXCEPTIONS as e:
        self._ValidateHttpAccessTokenRefreshError(e)
        start_byte = download_stream.tell()
        bytes_downloaded_container.bytes_transferred = start_byte
        if start_byte > last_progress_byte:
          # We've made progress, so allow a fresh set of retries.
          last_progress_byte = start_byte
          retries = 0
        retries += 1
        if retries > self.num_retries:
          ##### DEBUG
          # If you are fighting a redacted exception spew in
          # multiprocess/multithread calls, add your exception to
          # HTTP_TRANSFER_EXCEPTIONS and uncomment the following block.  This
          # may hang, but you should get a stack trace spew after Ctrl-C.
          #####
          # import re, sys, traceback
          # from gslib.utils import text_util
          # message = 'some exception happened'
          # stack_trace = traceback.format_exc()
          # err = ('DEBUG: Exception stack trace:\n    %s\n%s\n' % (
          #     re.sub('\\n', '\n    ', stack_trace),
          #     message,
          # ))
          # dest_fd = sys.stderr
          # text_util.print_to_fd(err, end='', file=dest_fd)
          # dest_fd.flush()
          ##### END DEBUG
          raise ResumableDownloadException(
              'Transfer failed after %d retries. Final exception: %s' %
              (self.num_retries, GetPrintableExceptionString(e)))
        time.sleep(CalculateWaitForRetry(retries, max_wait=self.max_retry_wait))
        if self.logger.isEnabledFor(logging.DEBUG):
          self.logger.debug(
              'Retrying download from byte %s after exception: %s. Trace: %s',
              start_byte, GetPrintableExceptionString(e),
              traceback.format_exc())
        apitools_http_wrapper.RebuildHttpConnections(
            apitools_download.bytes_http)

  def _PerformDownload(self,
                       bucket_name,
                       object_name,
                       download_stream,
                       apitools_request,
                       apitools_download,
                       generation=None,
                       compressed_encoding=False,
                       start_byte=0,
                       end_byte=None,
                       serialization_data=None,
                       decryption_tuple=None):
    if not serialization_data:
      try:
        self.api_client.objects.Get(apitools_request,
                                    download=apitools_download)
      except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
        self._TranslateExceptionAndRaise(e,
                                         bucket_name=bucket_name,
                                         object_name=object_name,
                                         generation=generation)

    # Disable apitools' default print callbacks.
    def _NoOpCallback(unused_response, unused_download_object):
      pass

    # TODO: If we have a resumable download with accept-encoding:gzip
    # on a object that is compressible but not in gzip form in the cloud,
    # on-the-fly compression may gzip the object.  In this case if our
    # download breaks, future requests will ignore the range header and just
    # return the object (gzipped) in its entirety.  Ideally, we would unzip
    # the bytes that we have locally and send a range request without
    # accept-encoding:gzip so that we can download only the (uncompressed) bytes
    # that we don't yet have.

    # Since bytes_http is created in this function, we don't get the
    # user-agent header from api_client's http automatically.
    additional_headers = {
        'user-agent': self.api_client.user_agent,
    }
    AddAcceptEncodingGzipIfNeeded(additional_headers,
                                  compressed_encoding=compressed_encoding)

    self._UpdateHeaders(additional_headers)
    additional_headers.update(
        self._EncryptionHeadersFromTuple(decryption_tuple))

    if start_byte or end_byte is not None:
      apitools_download.GetRange(additional_headers=additional_headers,
                                 start=start_byte,
                                 end=end_byte,
                                 use_chunks=False)
    else:
      apitools_download.StreamMedia(callback=_NoOpCallback,
                                    finish_callback=_NoOpCallback,
                                    additional_headers=additional_headers,
                                    use_chunks=False)
    return apitools_download.encoding

  def PatchObjectMetadata(self,
                          bucket_name,
                          object_name,
                          metadata,
                          canned_acl=None,
                          generation=None,
                          preconditions=None,
                          provider=None,
                          fields=None,
                          user_project=None):
    """See CloudApi class for function doc strings."""
    projection = (apitools_messages.StorageObjectsPatchRequest.
                  ProjectionValueValuesEnum.noAcl)
    if self._FieldsContainsAclField(fields):
      projection = (apitools_messages.StorageObjectsPatchRequest.
                    ProjectionValueValuesEnum.full)

    if not preconditions:
      preconditions = Preconditions()

    if generation:
      generation = long(generation)

    predefined_acl = None
    apitools_include_fields = []
    if canned_acl:
      # Must null out existing ACLs to apply a canned ACL.
      apitools_include_fields.append('acl')
      predefined_acl = (apitools_messages.StorageObjectsPatchRequest.
                        PredefinedAclValueValuesEnum(
                            self._ObjectCannedAclToPredefinedAcl(canned_acl)))

    # Provide the ability to delete response headers from metadata.
    if metadata.cacheControl == '':
      apitools_include_fields.append('cacheControl')
    if metadata.contentDisposition == '':
      apitools_include_fields.append('contentDisposition')
    if metadata.contentEncoding == '':
      apitools_include_fields.append('contentEncoding')
    if metadata.contentLanguage == '':
      apitools_include_fields.append('contentLanguage')

    apitools_request = apitools_messages.StorageObjectsPatchRequest(
        bucket=bucket_name,
        object=object_name,
        objectResource=metadata,
        generation=generation,
        projection=projection,
        ifGenerationMatch=preconditions.gen_match,
        ifMetagenerationMatch=preconditions.meta_gen_match,
        predefinedAcl=predefined_acl,
        userProject=self.user_project)
    global_params = apitools_messages.StandardQueryParameters()
    if fields:
      global_params.fields = ','.join(set(fields))

    try:
      with self.api_client.IncludeFields(apitools_include_fields):
        return self.api_client.objects.Patch(apitools_request,
                                             global_params=global_params)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=bucket_name,
                                       object_name=object_name,
                                       generation=generation)

  def _UploadObject(self,
                    upload_stream,
                    object_metadata,
                    canned_acl=None,
                    size=None,
                    preconditions=None,
                    encryption_tuple=None,
                    provider=None,
                    fields=None,
                    serialization_data=None,
                    tracker_callback=None,
                    progress_callback=None,
                    apitools_strategy=apitools_transfer.SIMPLE_UPLOAD,
                    total_size=0,
                    gzip_encoded=False):
    # pylint: disable=g-doc-args
    """Upload implementation. Cloud API arguments, plus two more.

    Additional args:
      apitools_strategy: SIMPLE_UPLOAD or RESUMABLE_UPLOAD.
      total_size: Total size of the upload; None if it is unknown (streaming).

    Returns:
      Uploaded object metadata.
    """
    # pylint: enable=g-doc-args
    ValidateDstObjectMetadata(object_metadata)
    predefined_acl = None
    if canned_acl:
      predefined_acl = (apitools_messages.StorageObjectsInsertRequest.
                        PredefinedAclValueValuesEnum(
                            self._ObjectCannedAclToPredefinedAcl(canned_acl)))

    bytes_uploaded_container = BytesTransferredContainer()

    if progress_callback and size:
      total_size = size
      progress_callback(0, size)

    callback_class_factory = UploadCallbackConnectionClassFactory(
        bytes_uploaded_container,
        total_size=total_size,
        progress_callback=progress_callback,
        logger=self.logger,
        debug=self.debug)

    upload_http_class = callback_class_factory.GetConnectionClass()
    self.upload_http.connections = {
        'http': upload_http_class,
        'https': upload_http_class,
    }

    # Since bytes_http is created in this function, we don't get the
    # user-agent header from api_client's http automatically.
    additional_headers = {
        'user-agent': self.api_client.user_agent,
    }
    self._UpdateHeaders(additional_headers)

    try:
      content_type = None
      apitools_request = None
      global_params = None

      if not serialization_data:
        # This is a new upload, set up initial upload state.
        content_type = object_metadata.contentType
        if not content_type:
          content_type = DEFAULT_CONTENT_TYPE

        if not preconditions:
          preconditions = Preconditions()

        apitools_request = apitools_messages.StorageObjectsInsertRequest(
            bucket=object_metadata.bucket,
            object=object_metadata,
            ifGenerationMatch=preconditions.gen_match,
            ifMetagenerationMatch=preconditions.meta_gen_match,
            predefinedAcl=predefined_acl,
            userProject=self.user_project)
        global_params = apitools_messages.StandardQueryParameters()
        if fields:
          global_params.fields = ','.join(set(fields))

      encryption_headers = self._EncryptionHeadersFromTuple(
          crypto_tuple=encryption_tuple)

      if apitools_strategy == apitools_transfer.SIMPLE_UPLOAD:
        # One-shot upload.
        apitools_upload = apitools_transfer.Upload(upload_stream,
                                                   content_type,
                                                   total_size=size,
                                                   auto_transfer=True,
                                                   num_retries=self.num_retries,
                                                   gzip_encoded=gzip_encoded)
        apitools_upload.strategy = apitools_strategy
        apitools_upload.bytes_http = self.authorized_upload_http

        with self._ApitoolsRequestHeaders(encryption_headers):
          return self.api_client.objects.Insert(apitools_request,
                                                upload=apitools_upload,
                                                global_params=global_params)
      else:  # Resumable upload.
        # Since bytes_http is created in this function, we don't get the
        # user-agent header from api_client's http automatically.
        additional_headers = {
            'user-agent': self.api_client.user_agent,
        }
        additional_headers.update(encryption_headers)
        self._UpdateHeaders(additional_headers)

        return self._PerformResumableUpload(
            upload_stream, self.authorized_upload_http, content_type, size,
            serialization_data, apitools_strategy, apitools_request,
            global_params, bytes_uploaded_container, tracker_callback,
            additional_headers, progress_callback, gzip_encoded)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      not_found_exception = CreateNotFoundExceptionForObjectWrite(
          self.provider, object_metadata.bucket)
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=object_metadata.bucket,
                                       object_name=object_metadata.name,
                                       not_found_exception=not_found_exception)

  def _PerformResumableUpload(self, upload_stream, authorized_upload_http,
                              content_type, size, serialization_data,
                              apitools_strategy, apitools_request,
                              global_params, bytes_uploaded_container,
                              tracker_callback, addl_headers, progress_callback,
                              gzip_encoded):
    try:
      if serialization_data:
        # Resuming an existing upload.
        apitools_upload = apitools_transfer.Upload.FromData(
            upload_stream,
            serialization_data,
            self.api_client.http,
            num_retries=self.num_retries,
            gzip_encoded=gzip_encoded,
            client=self.api_client)
        apitools_upload.chunksize = GetJsonResumableChunkSize()
        apitools_upload.bytes_http = authorized_upload_http
      else:
        # New resumable upload.
        apitools_upload = apitools_transfer.Upload(
            upload_stream,
            content_type,
            total_size=size,
            chunksize=GetJsonResumableChunkSize(),
            auto_transfer=False,
            num_retries=self.num_retries,
            gzip_encoded=gzip_encoded)
        apitools_upload.strategy = apitools_strategy
        apitools_upload.bytes_http = authorized_upload_http
        with self._ApitoolsRequestHeaders(addl_headers):
          self.api_client.objects.Insert(apitools_request,
                                         upload=apitools_upload,
                                         global_params=global_params)
      # Disable retries in apitools. We will handle them explicitly here.
      apitools_upload.retry_func = LogAndHandleRetries(
          is_data_transfer=True, status_queue=self.status_queue)

      # Disable apitools' default print callbacks.
      def _NoOpCallback(unused_response, unused_upload_object):
        pass

      # If we're resuming an upload, apitools has at this point received
      # from the server how many bytes it already has. Update our
      # callback class with this information.
      bytes_uploaded_container.bytes_transferred = apitools_upload.progress

      if tracker_callback:
        tracker_callback(json.dumps(apitools_upload.serialization_data))

      retries = 0
      last_progress_byte = apitools_upload.progress
      while retries <= self.num_retries:
        try:
          # TODO: On retry, this will seek to the bytes that the server has,
          # causing the hash to be recalculated. Make HashingFileUploadWrapper
          # save a digest according to json_resumable_chunk_size.
          if not gzip_encoded and size and not JsonResumableChunkSizeDefined():
            # If size is known and the request doesn't need to be compressed,
            # we can send it all in one request and avoid making a
            # round-trip per chunk. Compression is not supported for
            # non-chunked streaming uploads because supporting resumability
            # for that feature results in degraded upload performance and
            # adds significant complexity to the implementation.
            http_response = apitools_upload.StreamMedia(
                callback=_NoOpCallback,
                finish_callback=_NoOpCallback,
                additional_headers=addl_headers)
          else:
            # Otherwise it's a streaming request and we need to ensure that we
            # send the bytes in chunks so that we can guarantee that we never
            # need to seek backwards more than our buffer (and also that the
            # chunks are aligned to 256KB).
            http_response = apitools_upload.StreamInChunks(
                callback=_NoOpCallback,
                finish_callback=_NoOpCallback,
                additional_headers=addl_headers)
          processed_response = self.api_client.objects.ProcessHttpResponse(
              self.api_client.objects.GetMethodConfig('Insert'), http_response)
          if size is None and progress_callback:
            # Make final progress callback; total size should now be known.
            # This works around the fact the send function counts header bytes.
            # However, this will make the progress appear to go slightly
            # backwards at the end.
            progress_callback(apitools_upload.total_size,
                              apitools_upload.total_size)
          return processed_response
        except HTTP_TRANSFER_EXCEPTIONS as e:
          self._ValidateHttpAccessTokenRefreshError(e)
          apitools_http_wrapper.RebuildHttpConnections(
              apitools_upload.bytes_http)
          while retries <= self.num_retries:
            try:
              # TODO: Simulate the refresh case in tests. Right now, our
              # mocks are not complex enough to simulate a failure.
              apitools_upload.RefreshResumableUploadState()
              start_byte = apitools_upload.progress
              bytes_uploaded_container.bytes_transferred = start_byte
              break
            except HTTP_TRANSFER_EXCEPTIONS as e2:
              self._ValidateHttpAccessTokenRefreshError(e2)
              apitools_http_wrapper.RebuildHttpConnections(
                  apitools_upload.bytes_http)
              retries += 1
              if retries > self.num_retries:
                raise ResumableUploadException(
                    'Transfer failed after %d retries. Final exception: %s' %
                    (self.num_retries, e2))
              time.sleep(
                  CalculateWaitForRetry(retries, max_wait=self.max_retry_wait))
          if start_byte > last_progress_byte:
            # We've made progress, so allow a fresh set of retries.
            last_progress_byte = start_byte
            retries = 0
          else:
            retries += 1
            if retries > self.num_retries:
              raise ResumableUploadException(
                  'Transfer failed after %d retries. Final exception: %s' %
                  (self.num_retries, GetPrintableExceptionString(e)))
            time.sleep(
                CalculateWaitForRetry(retries, max_wait=self.max_retry_wait))
          if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(
                'Retrying upload from byte %s after exception: %s. Trace: %s',
                start_byte, GetPrintableExceptionString(e),
                traceback.format_exc())
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      resumable_ex = self._TranslateApitoolsResumableUploadException(e)
      if resumable_ex:
        raise resumable_ex
      else:
        raise

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
    """See CloudApi class for function doc strings."""
    return self._UploadObject(upload_stream,
                              object_metadata,
                              canned_acl=canned_acl,
                              size=size,
                              preconditions=preconditions,
                              progress_callback=progress_callback,
                              encryption_tuple=encryption_tuple,
                              fields=fields,
                              apitools_strategy=apitools_transfer.SIMPLE_UPLOAD,
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
    """See CloudApi class for function doc strings."""
    # Streaming indicated by not passing a size.
    # Resumable capabilities are present up to the resumable chunk size using
    # a buffered stream.
    return self._UploadObject(
        upload_stream,
        object_metadata,
        canned_acl=canned_acl,
        preconditions=preconditions,
        progress_callback=progress_callback,
        encryption_tuple=encryption_tuple,
        fields=fields,
        apitools_strategy=apitools_transfer.RESUMABLE_UPLOAD,
        total_size=None,
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
    """See CloudApi class for function doc strings."""
    return self._UploadObject(
        upload_stream,
        object_metadata,
        canned_acl=canned_acl,
        preconditions=preconditions,
        fields=fields,
        size=size,
        serialization_data=serialization_data,
        tracker_callback=tracker_callback,
        progress_callback=progress_callback,
        encryption_tuple=encryption_tuple,
        apitools_strategy=apitools_transfer.RESUMABLE_UPLOAD,
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
    """See CloudApi class for function doc strings."""
    ValidateDstObjectMetadata(dst_obj_metadata)
    predefined_acl = None
    if canned_acl:
      predefined_acl = (apitools_messages.StorageObjectsRewriteRequest.
                        DestinationPredefinedAclValueValuesEnum(
                            self._ObjectCannedAclToPredefinedAcl(canned_acl)))

    if src_generation:
      src_generation = long(src_generation)

    if not preconditions:
      preconditions = Preconditions()

    projection = (apitools_messages.StorageObjectsRewriteRequest.
                  ProjectionValueValuesEnum.noAcl)
    if self._FieldsContainsAclField(fields):
      projection = (apitools_messages.StorageObjectsRewriteRequest.
                    ProjectionValueValuesEnum.full)
    global_params = apitools_messages.StandardQueryParameters()
    if fields:
      # Rewrite returns the resultant object under the 'resource' field.
      new_fields = set([
          'done',
          'objectSize',
          'rewriteToken',
          'totalBytesRewritten',
      ])
      for field in fields:
        new_fields.add('resource/' + field)
      global_params.fields = ','.join(set(new_fields))

    dec_key_sha256 = None
    if decryption_tuple and decryption_tuple.crypto_type == CryptoKeyType.CSEK:
      dec_key_sha256 = decryption_tuple.crypto_key_sha256

    enc_key_sha256 = None
    if encryption_tuple:
      if encryption_tuple.crypto_type == CryptoKeyType.CSEK:
        enc_key_sha256 = encryption_tuple.crypto_key_sha256
      elif encryption_tuple.crypto_type == CryptoKeyType.CMEK:
        dst_obj_metadata.kmsKeyName = encryption_tuple.crypto_key

    # Check to see if we are resuming a rewrite.
    tracker_file_name = GetRewriteTrackerFilePath(src_obj_metadata.bucket,
                                                  src_obj_metadata.name,
                                                  dst_obj_metadata.bucket,
                                                  dst_obj_metadata.name, 'JSON')
    rewrite_params_hash = HashRewriteParameters(
        src_obj_metadata,
        dst_obj_metadata,
        projection,
        src_generation=src_generation,
        gen_match=preconditions.gen_match,
        meta_gen_match=preconditions.meta_gen_match,
        canned_acl=predefined_acl,
        max_bytes_per_call=max_bytes_per_call,
        src_dec_key_sha256=dec_key_sha256,
        dst_enc_key_sha256=enc_key_sha256,
        fields=global_params.fields)
    resume_rewrite_token = ReadRewriteTrackerFile(tracker_file_name,
                                                  rewrite_params_hash)
    crypto_headers = self._RewriteCryptoHeadersFromTuples(
        decryption_tuple=decryption_tuple, encryption_tuple=encryption_tuple)

    progress_cb_with_timeout = None
    try:
      last_bytes_written = long(0)
      while True:
        with self._ApitoolsRequestHeaders(crypto_headers):
          apitools_request = apitools_messages.StorageObjectsRewriteRequest(
              sourceBucket=src_obj_metadata.bucket,
              sourceObject=src_obj_metadata.name,
              destinationBucket=dst_obj_metadata.bucket,
              # TODO(KMS): Remove the destinationKmsKeyName parameter once the
              # API begins pulling key name from the dest obj metadata.
              destinationKmsKeyName=dst_obj_metadata.kmsKeyName,
              destinationObject=dst_obj_metadata.name,
              projection=projection,
              object=dst_obj_metadata,
              sourceGeneration=src_generation,
              ifGenerationMatch=preconditions.gen_match,
              ifMetagenerationMatch=preconditions.meta_gen_match,
              destinationPredefinedAcl=predefined_acl,
              rewriteToken=resume_rewrite_token,
              maxBytesRewrittenPerCall=max_bytes_per_call,
              userProject=self.user_project)
          rewrite_response = self.api_client.objects.Rewrite(
              apitools_request, global_params=global_params)
        bytes_written = long(rewrite_response.totalBytesRewritten)
        if progress_callback and not progress_cb_with_timeout:
          progress_cb_with_timeout = ProgressCallbackWithTimeout(
              long(rewrite_response.objectSize), progress_callback)
        if progress_cb_with_timeout:
          progress_cb_with_timeout.Progress(bytes_written - last_bytes_written)

        if rewrite_response.done:
          break
        elif not resume_rewrite_token:
          # Save the token and make a tracker file if they don't already exist.
          resume_rewrite_token = rewrite_response.rewriteToken
          WriteRewriteTrackerFile(tracker_file_name, rewrite_params_hash,
                                  rewrite_response.rewriteToken)
        last_bytes_written = bytes_written

      DeleteTrackerFile(tracker_file_name)
      return rewrite_response.resource
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
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

  def DeleteObject(self,
                   bucket_name,
                   object_name,
                   preconditions=None,
                   generation=None,
                   provider=None):
    """See CloudApi class for function doc strings."""
    if not preconditions:
      preconditions = Preconditions()

    if generation:
      generation = long(generation)

    apitools_request = apitools_messages.StorageObjectsDeleteRequest(
        bucket=bucket_name,
        object=object_name,
        generation=generation,
        ifGenerationMatch=preconditions.gen_match,
        ifMetagenerationMatch=preconditions.meta_gen_match,
        userProject=self.user_project)
    try:
      return self.api_client.objects.Delete(apitools_request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e,
                                       bucket_name=bucket_name,
                                       object_name=object_name,
                                       generation=generation)

  def ComposeObject(self,
                    src_objs_metadata,
                    dst_obj_metadata,
                    preconditions=None,
                    encryption_tuple=None,
                    provider=None,
                    fields=None):
    """See CloudApi class for function doc strings."""
    ValidateDstObjectMetadata(dst_obj_metadata)

    dst_obj_name = dst_obj_metadata.name
    dst_obj_metadata.name = None
    dst_bucket_name = dst_obj_metadata.bucket
    dst_obj_metadata.bucket = None
    if not dst_obj_metadata.contentType:
      dst_obj_metadata.contentType = DEFAULT_CONTENT_TYPE

    if not preconditions:
      preconditions = Preconditions()

    global_params = apitools_messages.StandardQueryParameters()
    if fields:
      global_params.fields = ','.join(set(fields))

    src_objs_compose_request = apitools_messages.ComposeRequest(
        sourceObjects=src_objs_metadata, destination=dst_obj_metadata)

    encryption_headers = self._EncryptionHeadersFromTuple(
        crypto_tuple=encryption_tuple)

    kmsKeyName = None
    if encryption_tuple:
      if encryption_tuple.crypto_type == CryptoKeyType.CMEK:
        kmsKeyName = encryption_tuple.crypto_key

    with self._ApitoolsRequestHeaders(encryption_headers):
      apitools_request = apitools_messages.StorageObjectsComposeRequest(
          composeRequest=src_objs_compose_request,
          destinationBucket=dst_bucket_name,
          destinationObject=dst_obj_name,
          ifGenerationMatch=preconditions.gen_match,
          ifMetagenerationMatch=preconditions.meta_gen_match,
          userProject=self.user_project,
          kmsKeyName=kmsKeyName)
      try:
        return self.api_client.objects.Compose(apitools_request,
                                               global_params=global_params)
      except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
        # We can't be sure which object was missing in the 404 case.
        if (isinstance(e, apitools_exceptions.HttpError) and
            e.status_code == 404):
          raise NotFoundException('One of the source objects does not exist.')
        else:
          self._TranslateExceptionAndRaise(e)

  def WatchBucket(self,
                  bucket_name,
                  address,
                  channel_id,
                  token=None,
                  provider=None,
                  fields=None):
    """See CloudApi class for function doc strings."""
    projection = (apitools_messages.StorageObjectsWatchAllRequest.
                  ProjectionValueValuesEnum.full)

    channel = apitools_messages.Channel(address=address,
                                        id=channel_id,
                                        token=token,
                                        type='WEB_HOOK')

    apitools_request = apitools_messages.StorageObjectsWatchAllRequest(
        bucket=bucket_name,
        channel=channel,
        projection=projection,
        userProject=self.user_project)

    global_params = apitools_messages.StandardQueryParameters()
    if fields:
      global_params.fields = ','.join(set(fields))

    try:
      return self.api_client.objects.WatchAll(apitools_request,
                                              global_params=global_params)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

  def StopChannel(self, channel_id, resource_id, provider=None):
    """See CloudApi class for function doc strings."""
    channel = apitools_messages.Channel(id=channel_id, resourceId=resource_id)
    try:
      self.api_client.channels.Stop(channel)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def ListChannels(self, bucket_name, provider=None, fields=None):
    """See CloudApi class for function doc strings."""
    apitools_request = apitools_messages.StorageBucketsListChannelsRequest(
        bucket=bucket_name, userProject=self.user_project)

    try:
      return self.api_client.buckets.ListChannels(apitools_request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, bucket_name=bucket_name)

  def GetProjectServiceAccount(self, project_number):
    """See CloudApi class for function doc strings."""
    try:
      request = apitools_messages.StorageProjectsServiceAccountGetRequest(
          projectId=six.text_type(project_number))
      return self.api_client.projects_serviceAccount.Get(request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def CreateNotificationConfig(self,
                               bucket_name,
                               pubsub_topic,
                               payload_format,
                               event_types=None,
                               custom_attributes=None,
                               object_name_prefix=None):
    """See CloudApi class for function doc strings."""
    try:
      notification = apitools_messages.Notification(
          topic=pubsub_topic, payload_format=payload_format)
      if event_types:
        notification.event_types = event_types
      if custom_attributes:
        additional_properties = [
            NotificationAdditionalProperty(key=key, value=value)
            for key, value in custom_attributes.items()
        ]
        notification.custom_attributes = NotificationCustomAttributesValue(
            additionalProperties=additional_properties)
      if object_name_prefix:
        notification.object_name_prefix = object_name_prefix

      request = apitools_messages.StorageNotificationsInsertRequest(
          bucket=bucket_name,
          notification=notification,
          userProject=self.user_project)
      return self.api_client.notifications.Insert(request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def DeleteNotificationConfig(self, bucket_name, notification):
    """See CloudApi class for function doc strings."""
    try:
      request = apitools_messages.StorageNotificationsDeleteRequest(
          bucket=bucket_name,
          notification=notification,
          userProject=self.user_project)
      return self.api_client.notifications.Delete(request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def ListNotificationConfigs(self, bucket_name):
    """See CloudApi class for function doc strings."""
    try:
      request = apitools_messages.StorageNotificationsListRequest(
          bucket=bucket_name, userProject=self.user_project)
      response = self.api_client.notifications.List(request)
      for notification in response.items:
        yield notification
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def CreateHmacKey(self, project_id, service_account_email):
    """See CloudApi class for function doc strings."""
    try:
      request = apitools_messages.StorageProjectsHmacKeysCreateRequest(
          projectId=project_id, serviceAccountEmail=service_account_email)
      return self.api_client.hmacKeys.Create(request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def DeleteHmacKey(self, project_id, access_id):
    """See CloudApi class for function doc strings."""
    try:
      request = apitools_messages.StorageProjectsHmacKeysDeleteRequest(
          projectId=project_id, accessId=access_id)
      return self.api_client.hmacKeys.Delete(request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def GetHmacKey(self, project_id, access_id):
    """See CloudApi class for function doc strings."""
    try:
      request = apitools_messages.StorageProjectsHmacKeysGetRequest(
          projectId=project_id, accessId=access_id)
      return self.api_client.hmacKeys.Get(request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def ListHmacKeys(self,
                   project_id,
                   service_account_email,
                   show_deleted_keys=True):
    """See CloudApi class for function doc strings."""
    try:
      request = apitools_messages.StorageProjectsHmacKeysListRequest(
          projectId=project_id,
          serviceAccountEmail=service_account_email,
          showDeletedKeys=show_deleted_keys,
          maxResults=NUM_BUCKETS_PER_LIST_PAGE)

      response = self.api_client.hmacKeys.List(request)
      for key in response.items:
        yield key
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

    while response.nextPageToken:
      request = apitools_messages.StorageProjectsHmacKeysListRequest(
          projectId=project_id,
          serviceAccountEmail=service_account_email,
          showDeletedKeys=show_deleted_keys,
          pageToken=response.nextPageToken,
          maxResults=NUM_BUCKETS_PER_LIST_PAGE)
      try:
        response = self.api_client.hmacKeys.List(request)
      except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
        self._TranslateExceptionAndRaise(e)

      for key in response.items:
        yield key

  def UpdateHmacKey(self, project_id, access_id, state, etag):
    """See CloudApi class for function doc strings."""
    try:
      request = apitools_messages.StorageProjectsHmacKeysUpdateRequest(
          projectId=project_id, accessId=access_id)
      metadata = apitools_messages.HmacKeyMetadata()
      metadata.state = state
      if etag:
        metadata.etag = etag
      request.resource = metadata
      return self.api_client.hmacKeys.Update(request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e)

  def _BucketCannedAclToPredefinedAcl(self, canned_acl_string):
    """Translates the input string to a bucket PredefinedAcl string.

    Args:
      canned_acl_string: Canned ACL string.

    Returns:
      String that can be used as a query parameter with the JSON API. This
      corresponds to a flavor of *PredefinedAclValueValuesEnum and can be
      used as input to apitools requests that affect bucket access controls.
    """
    if canned_acl_string in _BUCKET_PREDEFINED_ACL_XML_TO_JSON_TRANSLATION:
      return _BUCKET_PREDEFINED_ACL_XML_TO_JSON_TRANSLATION[canned_acl_string]
    raise ArgumentException('Invalid canned ACL %s' % canned_acl_string)

  def _ObjectCannedAclToPredefinedAcl(self, canned_acl_string):
    """Translates the input string to an object PredefinedAcl string.

    Args:
      canned_acl_string: Canned ACL string.

    Returns:
      String that can be used as a query parameter with the JSON API. This
      corresponds to a flavor of *PredefinedAclValueValuesEnum and can be
      used as input to apitools requests that affect object access controls.
    """
    if canned_acl_string in _OBJECT_PREDEFINED_ACL_XML_TO_JSON_TRANSLATION:
      return _OBJECT_PREDEFINED_ACL_XML_TO_JSON_TRANSLATION[canned_acl_string]
    raise ArgumentException('Invalid canned ACL %s' % canned_acl_string)

  def _ValidateHttpAccessTokenRefreshError(self, e):
    if (isinstance(e, oauth2client.client.HttpAccessTokenRefreshError) and
        not (e.status == 429 or e.status >= 500)):
      raise

  def _TranslateExceptionAndRaise(self,
                                  e,
                                  bucket_name=None,
                                  object_name=None,
                                  generation=None,
                                  not_found_exception=None):
    """Translates an HTTP exception and raises the translated or original value.

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
    if self.logger.isEnabledFor(logging.DEBUG):
      self.logger.debug('TranslateExceptionAndRaise: %s',
                        traceback.format_exc())
    translated_exception = self._TranslateApitoolsException(
        e,
        bucket_name=bucket_name,
        object_name=object_name,
        generation=generation,
        not_found_exception=not_found_exception)
    if translated_exception:
      raise translated_exception
    else:
      raise

  def _GetMessageFromHttpError(self, http_error):
    if isinstance(http_error, apitools_exceptions.HttpError):
      if getattr(http_error, 'content', None):
        try:
          json_obj = json.loads(six.ensure_str(http_error.content))
          if 'error' in json_obj and 'message' in json_obj['error']:
            return json_obj['error']['message']
        except Exception:  # pylint: disable=broad-except
          # If we couldn't decode anything, just leave the message as None.
          pass

  def _GetAcceptableScopesFromHttpError(self, http_error):
    try:
      www_authenticate = http_error.response['www-authenticate']
      # In the event of a scope error, the www-authenticate field of the HTTP
      # response should contain text of the form
      #
      # 'Bearer realm="https://oauth2.googleapis.com/",
      # error=insufficient_scope, scope="${space separated list of acceptable
      # scopes}"'
      #
      # Here we use a quick string search to find the scope list, just looking
      # for a substring with the form 'scope="${scopes}"'.
      scope_idx = www_authenticate.find('scope="')
      if scope_idx >= 0:
        scopes = www_authenticate[scope_idx:].split('"')[1]
        return 'Acceptable scopes: %s' % scopes
    except Exception:  # pylint: disable=broad-except
      # Return None if we have any trouble parsing out the acceptable scopes.
      pass

  def _TranslateApitoolsResumableUploadException(self, e):
    if isinstance(e, apitools_exceptions.HttpError):
      message = self._GetMessageFromHttpError(e)
      if e.status_code >= 500:
        return ResumableUploadException(message or 'Server Error',
                                        status=e.status_code)
      elif e.status_code == 429:
        return ResumableUploadException(message or 'Too Many Requests',
                                        status=e.status_code)
      elif e.status_code == 410:
        return ResumableUploadStartOverException(message or 'Bad Request',
                                                 status=e.status_code)
      elif e.status_code == 404:
        return ResumableUploadStartOverException(message or 'Bad Request',
                                                 status=e.status_code)
      elif e.status_code >= 400:
        return ResumableUploadAbortException(message or 'Bad Request',
                                             status=e.status_code)
    if isinstance(e, apitools_exceptions.StreamExhausted):
      return ResumableUploadAbortException(
          '%s; if this issue persists, try deleting the tracker files present'
          ' under ~/.gsutil/tracker-files/' % str(e))
    if isinstance(e, apitools_exceptions.TransferError):
      if ('Aborting transfer' in str(e) or
          'Not enough bytes in stream' in str(e)):
        return ResumableUploadAbortException(str(e))
      elif 'additional bytes left in stream' in str(e):
        return ResumableUploadAbortException(
            '%s; this can happen if a file changes size while being uploaded' %
            str(e))

  def _TranslateApitoolsException(self,
                                  e,
                                  bucket_name=None,
                                  object_name=None,
                                  generation=None,
                                  not_found_exception=None):
    """Translates apitools exceptions into their gsutil Cloud Api equivalents.

    Args:
      e: Any exception in TRANSLATABLE_APITOOLS_EXCEPTIONS.
      bucket_name: Optional bucket name in request that caused the exception.
      object_name: Optional object name in request that caused the exception.
      generation: Optional generation in request that caused the exception.
      not_found_exception: Optional exception to raise in the not-found case.

    Returns:
      ServiceException for translatable exceptions, None
      otherwise.
    """
    if isinstance(e, apitools_exceptions.HttpError):
      message = self._GetMessageFromHttpError(e)
      if e.status_code == 400:
        # It is possible that the Project ID is incorrect.  Unfortunately the
        # JSON API does not give us much information about what part of the
        # request was bad.
        return BadRequestException(message or 'Bad Request',
                                   status=e.status_code)
      elif e.status_code == 401:
        if 'Login Required' in str(e):
          return AccessDeniedException(message or
                                       'Access denied: login required.',
                                       status=e.status_code)
        elif 'insufficient_scope' in str(e):
          # If the service includes insufficient scope error detail in the
          # response body, this check can be removed.
          return AccessDeniedException(
              _INSUFFICIENT_OAUTH2_SCOPE_MESSAGE,
              status=e.status_code,
              body=self._GetAcceptableScopesFromHttpError(e))
      elif e.status_code == 403:
        if 'The account for the specified project has been disabled' in str(e):
          return AccessDeniedException(message or 'Account disabled.',
                                       status=e.status_code)
        elif 'Daily Limit for Unauthenticated Use Exceeded' in str(e):
          return AccessDeniedException(message or
                                       'Access denied: quota exceeded. '
                                       'Is your project ID valid?',
                                       status=e.status_code)
        elif 'The bucket you tried to delete was not empty.' in str(e):
          return NotEmptyException('BucketNotEmpty (%s)' % bucket_name,
                                   status=e.status_code)
        elif ('The bucket you tried to create requires domain ownership '
              'verification.' in str(e)):
          return AccessDeniedException(
              'The bucket you tried to create requires domain ownership '
              'verification. Please see '
              'https://cloud.google.com/storage/docs/naming'
              '?hl=en#verification for more details.',
              status=e.status_code)
        elif 'User Rate Limit Exceeded' in str(e):
          return AccessDeniedException(
              'Rate limit exceeded. Please retry this '
              'request later.',
              status=e.status_code)
        elif 'Access Not Configured' in str(e):
          return AccessDeniedException(
              'Access Not Configured. Please go to the Google Cloud Platform '
              'Console (https://cloud.google.com/console#/project) for your '
              'project, select APIs and Auth and enable the '
              'Google Cloud Storage JSON API.',
              status=e.status_code)
        elif 'insufficient_scope' in str(e):
          # If the service includes insufficient scope error detail in the
          # response body, this check can be removed.
          return AccessDeniedException(
              _INSUFFICIENT_OAUTH2_SCOPE_MESSAGE,
              status=e.status_code,
              body=self._GetAcceptableScopesFromHttpError(e))
        elif 'does not have permission to publish messages' in str(e):
          return PublishPermissionDeniedException(message, status=e.status_code)
        else:
          return AccessDeniedException(message or str(e), status=e.status_code)
      elif e.status_code == 404:
        if not_found_exception:
          # The exception is pre-constructed prior to translation; the HTTP
          # status code isn't available at that time.
          setattr(not_found_exception, 'status', e.status_code)
          return not_found_exception
        elif bucket_name:
          if object_name:
            return CreateObjectNotFoundException(e.status_code,
                                                 self.provider,
                                                 bucket_name,
                                                 object_name,
                                                 generation=generation)
          return CreateBucketNotFoundException(e.status_code, self.provider,
                                               bucket_name)
        return NotFoundException(message or e.message, status=e.status_code)

      elif e.status_code == 409 and bucket_name:
        if 'The bucket you tried to delete is not empty.' in str(e):
          return NotEmptyException('BucketNotEmpty (%s)' % bucket_name,
                                   status=e.status_code)
        return ServiceException(
            'A Cloud Storage bucket named \'%s\' already exists. Try another '
            'name. Bucket names must be globally unique across all Google Cloud '
            'projects, including those outside of your '
            'organization.' % bucket_name,
            status=e.status_code)
      elif e.status_code == 412:
        return PreconditionException(message, status=e.status_code)
      return ServiceException(message, status=e.status_code)
    elif isinstance(e, apitools_exceptions.TransferInvalidError):
      return ServiceException('Transfer invalid (possible encoding error: %s)' %
                              str(e))

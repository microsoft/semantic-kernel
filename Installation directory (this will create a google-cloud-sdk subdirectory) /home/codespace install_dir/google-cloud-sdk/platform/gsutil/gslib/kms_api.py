# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc. All Rights Reserved.
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

import json
import logging
import traceback

from apitools.base.py import exceptions as apitools_exceptions
from boto import config
from gslib.cloud_api import AccessDeniedException
from gslib.cloud_api import BadRequestException
from gslib.cloud_api import NotFoundException
from gslib.cloud_api import PreconditionException
from gslib.cloud_api import ServiceException
from gslib.gcs_json_credentials import SetUpJsonCredentialsAndCache
from gslib.no_op_credentials import NoOpCredentials
from gslib.third_party.kms_apitools import cloudkms_v1_client as apitools_client
from gslib.third_party.kms_apitools import cloudkms_v1_messages as apitools_messages
from gslib.utils import system_util
from gslib.utils.boto_util import GetCertsFile
from gslib.utils.boto_util import GetMaxRetryDelay
from gslib.utils.boto_util import GetNewHttp
from gslib.utils.boto_util import GetNumRetries

TRANSLATABLE_APITOOLS_EXCEPTIONS = (apitools_exceptions.HttpError)

if system_util.InvokedViaCloudSdk():
  _INSUFFICIENT_OAUTH2_SCOPE_MESSAGE = (
      'Insufficient OAuth2 scope to perform this operation. '
      'Please re-run `gcloud auth login`')
else:
  _INSUFFICIENT_OAUTH2_SCOPE_MESSAGE = (
      'Insufficient OAuth2 scope to perform this operation. '
      'Please re-run `gsutil config`')


class KmsApi(object):
  """Wraps calls to the Cloud KMS v1 interface via apitools."""

  def __init__(self, logger=None, credentials=None, debug=0):
    """Performs necessary setup for interacting with Google Cloud KMS.

    Args:
      logger: logging.logger for outputting log messages.
      credentials: Credentials to be used for interacting with Cloud KMS
      debug: Debug level for the API implementation (0..3).
    """
    super(KmsApi, self).__init__()
    self.logger = logger

    self.certs_file = GetCertsFile()
    self.http = GetNewHttp()
    self.http_base = 'https://'
    self.host_base = config.get('Credentials', 'gs_kms_host',
                                'cloudkms.googleapis.com')
    gs_kms_port = config.get('Credentials', 'gs_kms_port', None)
    self.host_port = (':' + gs_kms_port) if gs_kms_port else ''
    self.url_base = (self.http_base + self.host_base + self.host_port)

    SetUpJsonCredentialsAndCache(self, logger, credentials=credentials)

    log_request = (debug >= 3)
    log_response = (debug >= 3)

    self.api_client = apitools_client.CloudkmsV1(url=self.url_base,
                                                 http=self.http,
                                                 log_request=log_request,
                                                 log_response=log_response,
                                                 credentials=self.credentials)

    self.num_retries = GetNumRetries()
    self.api_client.num_retries = self.num_retries

    self.max_retry_wait = GetMaxRetryDelay()
    self.api_client.max_retry_wait = self.max_retry_wait

    if isinstance(self.credentials, NoOpCredentials):
      # This API key is not secret and is used to identify gsutil during
      # anonymous requests.
      self.api_client.AddGlobalParam(
          'key', u'AIzaSyDnacJHrKma0048b13sh8cgxNUwulubmJM')

  def GetKeyIamPolicy(self, key_name):
    request = (apitools_messages.
               CloudkmsProjectsLocationsKeyRingsCryptoKeysGetIamPolicyRequest(
                   resource=key_name))
    try:
      return (self.api_client.projects_locations_keyRings_cryptoKeys.
              GetIamPolicy(request))
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, key_name=key_name)

  def SetKeyIamPolicy(self, key_name, policy):
    policy_request = apitools_messages.SetIamPolicyRequest(policy=policy)
    request = (apitools_messages.
               CloudkmsProjectsLocationsKeyRingsCryptoKeysSetIamPolicyRequest(
                   resource=key_name, setIamPolicyRequest=policy_request))
    try:
      return (self.api_client.projects_locations_keyRings_cryptoKeys.
              SetIamPolicy(request))
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, key_name=key_name)

  def CreateKeyRing(self, project, keyring_name, location='global'):
    """Attempts to create the specified keyRing.

    Args:
      project: (str) The project id in which to create the keyRing and key.
      keyring_name: (str) The name of the keyRing, e.g. my-keyring. Note
          that this must be unique within the location.
      location: (str) The location in which to create the keyRing. Defaults to
          'global'.

    Returns:
      (str) The fully-qualified name of the keyRing, e.g.:
      projects/my-project/locations/global/keyRings/my-keyring

    Raises:
      Translated CloudApi exception if we were unable to create the keyRing.
      Note that in the event of a 409 status code (resource already exists) when
      attempting creation, we continue and treat this as a success.
    """
    keyring_msg = apitools_messages.KeyRing(
        name='projects/%s/locations/%s/keyRings/%s' %
        (project, location, keyring_name))
    keyring_create_request = (
        apitools_messages.CloudkmsProjectsLocationsKeyRingsCreateRequest(
            keyRing=keyring_msg,
            keyRingId=keyring_name,
            parent='projects/%s/locations/%s' % (project, location)))
    try:
      self.api_client.projects_locations_keyRings.Create(keyring_create_request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      if e.status_code != 409:
        raise
    return 'projects/%s/locations/%s/keyRings/%s' % (project, location,
                                                     keyring_name)

  def CreateCryptoKey(self, keyring_fqn, key_name):
    """Attempts to create the specified cryptoKey.

    Args:
      keyring_fqn: (str) The fully-qualified name of the keyRing, e.g.
          projects/my-project/locations/global/keyRings/my-keyring.
      key_name: (str) The name of the desired key, e.g. my-key. Note that
          this must be unique within the keyRing.

    Returns:
      (str) The fully-qualified name of the cryptoKey, e.g.:
      projects/my-project/locations/global/keyRings/my-keyring/cryptoKeys/my-key

    Raises:
      Translated CloudApi exception if we were unable to create the cryptoKey.
      Note that in the event of a 409 status code (resource already exists) when
      attempting creation, we continue and treat this as a success.
    """
    cryptokey_msg = apitools_messages.CryptoKey(purpose=(
        apitools_messages.CryptoKey.PurposeValueValuesEnum.ENCRYPT_DECRYPT))
    cryptokey_create_request = (
        apitools_messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysCreateRequest(
            cryptoKey=cryptokey_msg, cryptoKeyId=key_name, parent=keyring_fqn))
    try:
      self.api_client.projects_locations_keyRings_cryptoKeys.Create(
          cryptokey_create_request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      if e.status_code != 409:
        raise
    return '%s/cryptoKeys/%s' % (keyring_fqn.rstrip('/'), key_name)

  def _TranslateExceptionAndRaise(self, e, key_name=None):
    """Translates an HTTP exception and raises the translated or original value.

    Args:
      e: Any Exception.
      key_name: Optional key name in request that caused the exception.

    Raises:
      Translated CloudApi exception, or the original exception if it was not
      translatable.
    """
    if self.logger.isEnabledFor(logging.DEBUG):
      self.logger.debug('TranslateExceptionAndRaise: %s',
                        traceback.format_exc())
    translated_exception = self._TranslateApitoolsException(e,
                                                            key_name=key_name)
    if translated_exception:
      raise translated_exception
    else:
      raise

  def _GetMessageFromHttpError(self, http_error):
    if isinstance(http_error, apitools_exceptions.HttpError):
      if getattr(http_error, 'content', None):
        try:
          json_obj = json.loads(http_error.content)
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
      # error=insufficient_scope,
      # scope="${space separated list of acceptable scopes}"'
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

  def _TranslateApitoolsException(self, e, key_name=None):
    """Translates apitools exceptions into their gsutil equivalents.

    Args:
      e: Any exception in TRANSLATABLE_APITOOLS_EXCEPTIONS.
      key_name: Optional key name in request that caused the exception.

    Returns:
      CloudStorageApiServiceException for translatable exceptions, None
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
        elif 'User Rate Limit Exceeded' in str(e):
          return AccessDeniedException(
              'Rate limit exceeded. Please retry this '
              'request later.',
              status=e.status_code)
        elif 'Access Not Configured' in str(e):
          return AccessDeniedException(
              'Access Not Configured. Please go to the Google Cloud Platform '
              'Console (https://cloud.google.com/console#/project) for your '
              'project, select APIs & services, and enable the Google Cloud '
              'KMS API.',
              status=e.status_code)
        elif 'insufficient_scope' in str(e):
          # If the service includes insufficient scope error detail in the
          # response body, this check can be removed.
          return AccessDeniedException(
              _INSUFFICIENT_OAUTH2_SCOPE_MESSAGE,
              status=e.status_code,
              body=self._GetAcceptableScopesFromHttpError(e))
        else:
          return AccessDeniedException(message or e.message or key_name,
                                       status=e.status_code)
      elif e.status_code == 404:
        return NotFoundException(message or e.message, status=e.status_code)

      elif e.status_code == 409 and key_name:
        return ServiceException('The key %s already exists.' % key_name,
                                status=e.status_code)
      elif e.status_code == 412:
        return PreconditionException(message, status=e.status_code)
      return ServiceException(message, status=e.status_code)

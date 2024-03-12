# -*- coding: utf-8 -*-
# Copyright 2019 Google Inc. All Rights Reserved.
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
from gslib.no_op_credentials import NoOpCredentials
from gslib.third_party.iamcredentials_apitools import iamcredentials_v1_client as apitools_client
from gslib.third_party.iamcredentials_apitools import iamcredentials_v1_messages as apitools_messages
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


class IamcredentailsApi(object):
  """Wraps calls to the Cloud IAM Credentials v1 interface via apitools."""

  def __init__(self, logger=None, credentials=None, debug=0):
    """Performs necessary setup for interacting with Google Cloud IAM
    Credentials.

    Args:
      logger: logging.logger for outputting log messages.
      credentials: Credentials to be used for interacting with Cloud IAM
      debug: Debug level for the API implementation (0..3).
    """
    super(IamcredentailsApi, self).__init__()

    self.logger = logger
    self.credentials = credentials

    self.certs_file = GetCertsFile()
    self.http = GetNewHttp()
    self.http_base = 'https://'
    # The original config option had a typo; supporting it as a fall-back
    # for legacy reasons.
    legacy_typo = 'gs_iamcredentails_host'
    self.host_base = config.get(
        'Credentials', 'gs_iamcredentials_host',
        config.get('Credentials', legacy_typo, 'iamcredentials.googleapis.com'))
    gs_iamcred_port = config.get('Credentials', 'gs_iamcredentails_port', None)
    self.host_port = (':' + gs_iamcred_port) if gs_iamcred_port else ''
    self.url_base = (self.http_base + self.host_base + self.host_port)

    log_request = (debug >= 3)
    log_response = (debug >= 3)

    self.api_client = apitools_client.IamcredentialsV1(
        url=self.url_base,
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

  def SignBlob(self, service_account_id, message):
    """Sign the blob using iamcredentials.SignBlob API."""
    name = 'projects/-/serviceAccounts/%s' % service_account_id
    sign_blob_request = apitools_messages.SignBlobRequest(payload=message)
    request = (
        apitools_messages.IamcredentialsProjectsServiceAccountsSignBlobRequest(
            name=name, signBlobRequest=sign_blob_request))
    try:
      return self.api_client.projects_serviceAccounts.SignBlob(request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, service_account_id)

  def GenerateAccessToken(self, service_account_id, scopes):
    """Generates an access token for the given service account."""
    name = 'projects/-/serviceAccounts/%s' % service_account_id
    generate_access_token_request = apitools_messages.GenerateAccessTokenRequest(
        scope=scopes)
    request = (apitools_messages.
               IamcredentialsProjectsServiceAccountsGenerateAccessTokenRequest(
                   name=name,
                   generateAccessTokenRequest=generate_access_token_request))

    try:
      return self.api_client.projects_serviceAccounts.GenerateAccessToken(
          request)
    except TRANSLATABLE_APITOOLS_EXCEPTIONS as e:
      self._TranslateExceptionAndRaise(e, service_account_id)

  def _TranslateExceptionAndRaise(self, e, service_account_id=None):
    """Translates an HTTP exception and raises the translated or original value.

    Args:
      e: Any Exception.
      service_account_id: Optional service account in request that caused the exception.

    Raises:
      Translated CloudApi exception, or the original exception if it was not
      translatable.
    """
    if self.logger.isEnabledFor(logging.DEBUG):
      self.logger.debug('TranslateExceptionAndRaise: %s',
                        traceback.format_exc())
    translated_exception = self._TranslateApitoolsException(
        e, service_account_id=service_account_id)
    if translated_exception:
      raise translated_exception
    else:
      raise

  def _TranslateApitoolsException(self, e, service_account_id=None):
    """Translates apitools exceptions into their gsutil equivalents.

    Args:
      e: Any exception in TRANSLATABLE_APITOOLS_EXCEPTIONS.
      service_account_id: Optional service account ID that caused the exception.

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
        # Messaging for when the the originating credentials don't have access
        # to impersonate a service account.
        if 'The caller does not have permission' in str(e):
          return AccessDeniedException(
              'Service account impersonation failed. Please go to the Google '
              'Cloud Platform Console (https://cloud.google.com/console), '
              'select IAM & admin, then Service Accounts, and grant your '
              'originating account the Service Account Token Creator role on '
              'the target service account.')
        # The server's errors message when IAM Credentials API aren't enabled
        # are pretty great so we just display them.
        if 'IAM Service Account Credentials API has not been used' in str(e):
          return AccessDeniedException(message)
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
              'IAM Credentials API.',
              status=e.status_code)
        elif 'insufficient_scope' in str(e):
          # If the service includes insufficient scope error detail in the
          # response body, this check can be removed.
          return AccessDeniedException(
              _INSUFFICIENT_OAUTH2_SCOPE_MESSAGE,
              status=e.status_code,
              body=self._GetAcceptableScopesFromHttpError(e))
        else:
          return AccessDeniedException(message or e.message or
                                       service_account_id,
                                       status=e.status_code)
      elif e.status_code == 404:
        return NotFoundException(message or e.message, status=e.status_code)

      elif e.status_code == 409 and service_account_id:
        return ServiceException('The key %s already exists.' %
                                service_account_id,
                                status=e.status_code)
      elif e.status_code == 412:
        return PreconditionException(message, status=e.status_code)
      return ServiceException(message, status=e.status_code)

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

# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Backend service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import batch
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.compute import exceptions
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.core import properties
from six.moves.urllib import parse

# Upper bound on batch size
# https://cloud.google.com/compute/docs/api/how-tos/batch
_BATCH_SIZE_LIMIT = 1000


class Error(exceptions.Error):
  """Errors raised by this module."""


def _GetBatchUrl(endpoint_url, api_version):
  """Return a batch URL for the given endpoint URL."""
  parsed_endpoint = parse.urlparse(endpoint_url)
  return parse.urljoin(
      '{0}://{1}'.format(parsed_endpoint.scheme, parsed_endpoint.netloc),
      'batch/compute/' + api_version)


def _ForceBatchRequest():
  """Check if compute/force_batch_request property is set."""
  return properties.VALUES.compute.force_batch_request.GetBool()


class ClientAdapter(object):
  """Encapsulates compute apitools interactions."""
  _API_NAME = 'compute'

  def __init__(self, api_version=None, no_http=False, client=None):
    self._api_version = core_apis.ResolveVersion(
        self._API_NAME, api_version=api_version)
    self._client = client or core_apis.GetClientInstance(
        self._API_NAME, self._api_version, no_http=no_http)

    # Turn the endpoint into just the host.
    # eg. https://compute.googleapis.com/compute/v1 -> https://compute.googleapis.com
    endpoint_url = core_apis.GetEffectiveApiEndpoint(self._API_NAME,
                                                     self._api_version)
    self._batch_url = _GetBatchUrl(endpoint_url, self._api_version)

  @property
  def api_version(self):
    return self._api_version

  @property
  def apitools_client(self):
    return self._client

  @property
  def batch_url(self):
    return self._batch_url

  @property
  def messages(self):
    return self._client.MESSAGES_MODULE

  def MakeRequests(
      self,
      requests,
      errors_to_collect=None,
      project_override=None,
      progress_tracker=None,
      no_followup=False,
      always_return_operation=False,
      followup_overrides=None,
      log_warnings=True,
      log_result=True,
      timeout=None,
  ):
    """Sends given request.

    Args:
      requests: A list of requests to make. Each element must be a 3-element
        tuple where the first element is the service, the second element is the
        string name of the method on the service, and the last element is a
        protocol buffer representing the request.
      errors_to_collect: A list for capturing errors. If any response contains
        an error, it is added to this list.
      project_override: The override project for the returned operation to poll
        from.
      progress_tracker: progress tracker to be ticked while waiting for
        operations to finish.
      no_followup: If True, do not followup operation with a GET request.
      always_return_operation: If True, return operation object even if
        operation fails.
      followup_overrides: A list of new resource names to GET once the operation
        finishes. Generally used in renaming calls.
      log_warnings: Whether warnings for completed operation should be printed.
      log_result: Whether the Operation Waiter should print the result in past
        tense of each request.
      timeout: The maximum amount of time, in seconds, to wait for the
        operations to reach the DONE state.

    Returns:
      A response for each request. For deletion requests, no corresponding
      responses are returned.
    """

    errors = errors_to_collect if errors_to_collect is not None else []
    objects = list(
        request_helper.MakeRequests(
            requests=requests,
            http=self._client.http,
            batch_url=self._batch_url,
            errors=errors,
            project_override=project_override,
            progress_tracker=progress_tracker,
            no_followup=no_followup,
            always_return_operation=always_return_operation,
            followup_overrides=followup_overrides,
            log_warnings=log_warnings,
            log_result=log_result,
            timeout=timeout,
        )
    )
    if errors_to_collect is None and errors:
      utils.RaiseToolException(
          errors, error_message='Could not fetch resource:')
    return objects

  def AsyncRequests(self, requests, errors_to_collect=None):
    """Issues async request for given set of requests.

    Return immediately without waiting for the operation in progress to complete

    Args:
      requests: list(tuple(service, method, payload)), where service is
        apitools.base.py.base_api.BaseApiService, method is str, method name,
        e.g. 'Get', 'CreateInstance', payload is a subclass of
        apitools.base.protorpclite.messages.Message.
      errors_to_collect: list, output only, can be None, contains instances of
        api_exceptions.HttpException for each request with exception.

    Returns:
      list of responses, matching list of requests. Some responses can be
        errors.
    """
    if not _ForceBatchRequest() and len(requests) == 1:
      responses = []
      errors = errors_to_collect if errors_to_collect is not None else []
      service, method, request_body = requests[0]
      num_retries = service.client.num_retries
      # stop the default retry behavior of http_wrapper.MakeRequest
      service.client.num_retries = 0
      try:
        response = getattr(service, method)(request=request_body)
        responses.append(response)
      except apitools_exceptions.HttpError as exception:
        errors.append(api_exceptions.HttpException(exception))
        responses.append(None)
      except apitools_exceptions.Error as exception:
        if hasattr(exception, 'message'):
          errors.append(Error(exception.message))
        else:
          errors.append((Error(exception)))
        responses.append(None)
      service.client.num_retries = num_retries
      return responses
    else:
      batch_request = batch.BatchApiRequest(batch_url=self._batch_url)
      for service, method, request in requests:
        batch_request.Add(service, method, request)

      payloads = batch_request.Execute(
          self._client.http, max_batch_size=_BATCH_SIZE_LIMIT
      )

      responses = []
      errors = errors_to_collect if errors_to_collect is not None else []

      for payload in payloads:
        if payload.is_error:
          if isinstance(payload.exception, apitools_exceptions.HttpError):
            errors.append(api_exceptions.HttpException(payload.exception))
          else:
            errors.append(Error(payload.exception.message))

        responses.append(payload.response)
    return responses

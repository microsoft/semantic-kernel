# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Helpers for making batch requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import batch
from apitools.base.py import exceptions

from googlecloudsdk.api_lib.compute import operation_quota_utils
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties

# Upper bound on batch size
# https://cloud.google.com/compute/docs/api/how-tos/batch
_BATCH_SIZE_LIMIT = 1000


class BatchChecker(object):
  """Class to conveniently curry the prompted_service_tokens cache."""

  def __init__(self, prompted_service_tokens):
    """Initialize class.

    Args:
      prompted_service_tokens: a set of string tokens that have already been
        prompted for enablement.
    """
    self.prompted_service_tokens = prompted_service_tokens

  # pylint: disable=unused-argument
  def BatchCheck(self, http_response, exception):
    """Callback for apitools batch responses.

    This will use self.prompted_service_tokens to cache service tokens that
    have already been prompted. In this way, if the same service has multiple
    batch requests and is enabled on the first, the user won't get a bunch of
    superflous messages. Note that this cannot be reused between batch uses
    because of the mutation.

    Args:
      http_response: Deserialized http_wrapper.Response object.
      exception: apiclient.errors.HttpError object if an error occurred.
    """
    # If there is no exception, then there is not an api enablement error.
    # Also, if prompting to enable is disabled, then we let the batch module
    # fail the batch request.
    if (exception is None
        or not properties.VALUES.core.should_prompt_to_enable_api.GetBool()):
      return
    enablement_info = apis.GetApiEnablementInfo(exception)
    if not enablement_info:  # Exception was not an api enablement error.
      return
    project, service_token, exception = enablement_info
    if service_token not in self.prompted_service_tokens:  # Only prompt once.
      self.prompted_service_tokens.add(service_token)
      apis.PromptToEnableApi(project, service_token, exception,
                             is_batch_request=True)


def MakeRequests(requests, http, batch_url=None):
  """Makes batch requests.

  Args:
    requests: A list of tuples. Each tuple must be of the form
        (service, method, request object).
    http: An HTTP object.
    batch_url: The URL to which to send the requests.

  Returns:
    A tuple where the first element is a list of all objects returned
    from the calls and the second is a list of error messages.
  """
  retryable_codes = []
  if properties.VALUES.core.should_prompt_to_enable_api.GetBool():
    # If the compute API is not enabled, then a 403 error is returned. We let
    # the batch module handle retrying requests by adding 403 to the list of
    # retryable codes for the batch request. If we should not prompt, then
    # we keep retryable_codes empty, so the request fails.
    retryable_codes.append(apis.API_ENABLEMENT_ERROR_EXPECTED_STATUS_CODE)
  batch_request = batch.BatchApiRequest(batch_url=batch_url,
                                        retryable_codes=retryable_codes)
  for service, method, request in requests:
    batch_request.Add(service, method, request)

  # TODO(b/36030477) this shouldn't be necessary in the future when batch and
  # non-batch error handling callbacks are unified
  batch_checker = BatchChecker(set())
  responses = batch_request.Execute(
      http, max_batch_size=_BATCH_SIZE_LIMIT,
      batch_request_callback=batch_checker.BatchCheck)

  objects = []
  errors = []

  for response in responses:
    objects.append(response.response)

    if response.is_error:
      # TODO(b/33771874): Use HttpException to decode error payloads.
      error_message = None
      if isinstance(response.exception, exceptions.HttpError):
        try:
          data = json.loads(response.exception.content)
          if utils.JsonErrorHasDetails(data):
            error_message = (response.exception.status_code,
                             BuildMessageForErrorWithDetails(data))
          else:
            error_message = (response.exception.status_code,
                             data.get('error', {}).get('message'))
        except ValueError:
          pass
        if not error_message:
          error_message = (response.exception.status_code,
                           response.exception.content)
      else:
        error_message = (None, response.exception.message)

      errors.append(error_message)

  return objects, errors


def BuildMessageForErrorWithDetails(json_data):
  if (operation_quota_utils.IsJsonOperationQuotaError(
      json_data.get('error', {}))):
    return operation_quota_utils.CreateOperationQuotaExceededMsg(json_data)
  else:
    return json_data.get('error', {}).get('message')

# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Helpers for making single request requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import exceptions
from googlecloudsdk.api_lib.compute import operation_quota_utils
from googlecloudsdk.api_lib.compute import utils
import six


def _GenerateErrorMessage(exception):
  """Generate Error Message given exception."""
  error_message = None
  try:
    data = json.loads(exception.content)
    if isinstance(
        exception, exceptions.HttpError
    ) and utils.JsonErrorHasDetails(data):
      error_message = (
          exception.status_code,
          BuildMessageForErrorWithDetails(data),
      )
    else:
      error_message = (
          exception.status_code,
          data.get('error', {}).get('message'),
      )
  except ValueError:
    pass
  if not error_message:
    error_message = (exception.status_code, exception.content)
  return error_message


def MakeSingleRequest(service, method, request_body):
  """Makes single request.

  Args:
    service: a BaseApiService Object.
    method: a string of method name.
    request_body: a protocol buffer requesting the requests.

  Returns:
    a length-one response list and error list.
  """
  responses, errors = [], []
  num_retries = service.client.num_retries
  # stop the default retry behavior of http_wrapper.MakeRequest
  service.client.num_retries = 0
  try:
    response = getattr(service, method)(request=request_body)
    responses.append(response)
  except exceptions.HttpError as exception:
    # TODO(b/260144046): Add Enable Service Prompt and Retry.
    error_message = _GenerateErrorMessage(exception)
    errors.append(error_message)
    # keep the same code behavior with batch_helper
    responses.append(None)
  # After enabling the Compute API, it will still throw a Request Error.
  # Catch the exception and retry.
  except exceptions.RequestError as exception:
    if six.text_type(exception) == 'Retry':
      response = getattr(service, method)(request=request_body)
      responses.append(response)
    else:
      raise exception
  service.client.num_retries = num_retries
  return responses, errors


# TODO(b/269805885): move to common formatter library
def BuildMessageForErrorWithDetails(json_data):
  if operation_quota_utils.IsJsonOperationQuotaError(
      json_data.get('error', {})
  ):
    return operation_quota_utils.CreateOperationQuotaExceededMsg(json_data)
  else:
    return json_data.get('error', {}).get('message')

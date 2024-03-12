# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Module for making API requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import json

from googlecloudsdk.api_lib.compute import batch_helper
from googlecloudsdk.api_lib.compute import single_request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute import waiters
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

import six
from six.moves import zip  # pylint: disable=redefined-builtin


def _RequestsAreListRequests(requests):
  """Checks if all requests are of list requests."""
  list_requests = [
      method in (
          'List', 'AggregatedList', 'ListInstances', 'ListManagedInstances'
          ) for _, method, _ in requests
  ]
  if all(list_requests):
    return True
  elif not any(list_requests):
    return False
  else:
    raise ValueError(
        'All requests must be either list requests or non-list requests.')


def _HandleJsonList(response, service, method, errors):
  """Extracts data from one *List response page as JSON and stores in dicts.

  Args:
    response: str, The *List response in JSON
    service: The service which responded to *List request
    method: str, Method used to list resources. One of 'List' or
      'AggregatedList'.
    errors: list, Errors from response will be appended to  this list.

  Returns:
    Pair of:
    - List of items returned in response as dicts
    - Next page token (if present, otherwise None).
  """
  items = []

  response = json.loads(response)

  # If the request is a list call, then yield the items directly.
  if method in ('List', 'ListInstances'):
    items = response.get('items', [])
  elif method == 'ListManagedInstances':
    items = response.get('managedInstances', [])

  # If the request is an aggregatedList call, then do all the
  # magic necessary to get the actual resources because the
  # aggregatedList responses are very complicated data
  # structures...
  elif method == 'AggregatedList':
    items_field_name = service.GetMethodConfig(
        'AggregatedList').relative_path.split('/')[-1]
    for scope_result in six.itervalues(response['items']):
      # If the given scope is unreachable, record the warning
      # message in the errors list.
      warning = scope_result.get('warning', None)
      if warning and warning['code'] == 'UNREACHABLE':
        errors.append((None, warning['message']))

      items.extend(scope_result.get(items_field_name, []))

  return items, response.get('nextPageToken', None)


def _HandleMessageList(response, service, method, errors):
  """Extracts data from one *List response page as Message object."""
  items = []

  # If the request is a list call, then yield the items directly.
  if method in ('List', 'ListInstances'):
    items = response.items
  elif method == 'ListManagedInstances':
    items = response.managedInstances
  # If the request is an aggregatedList call, then do all the
  # magic necessary to get the actual resources because the
  # aggregatedList responses are very complicated data
  # structures...
  else:
    items_field_name = service.GetMethodConfig(
        'AggregatedList').relative_path.split('/')[-1]
    for scope_result in response.items.additionalProperties:
      # If the given scope is unreachable, record the warning
      # message in the errors list.
      warning = scope_result.value.warning
      if warning and warning.code == warning.CodeValueValuesEnum.UNREACHABLE:
        errors.append((None, warning.message))

      items.extend(getattr(scope_result.value, items_field_name))

  return items, response.nextPageToken


def _ListCore(requests, http, batch_url, errors, response_handler):
  """Makes a series of list and/or aggregatedList batch requests.

  Args:
    requests: A list of requests to make. Each element must be a 3-element tuple
      where the first element is the service, the second element is the method
      ('List' or 'AggregatedList'), and the third element is a protocol buffer
      representing either a list or aggregatedList request.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors. If any response contains an error, it
      is added to this list.
    response_handler: The function to extract information responses.

  Yields:
    Resources encapsulated in format chosen by response_handler as they are
      received from the server.
  """
  while requests:
    if not _ForceBatchRequest() and len(requests) == 1:
      service, method, request_body = requests[0]
      responses, request_errors = single_request_helper.MakeSingleRequest(
          service, method, request_body
      )
      errors.extend(request_errors)
    else:
      responses, request_errors = batch_helper.MakeRequests(
          requests=requests, http=http, batch_url=batch_url
      )
      errors.extend(request_errors)

    new_requests = []

    for i, response in enumerate(responses):
      if not response:
        continue

      service, method, request_protobuf = requests[i]

      items, next_page_token = response_handler(response, service, method,
                                                errors)
      for item in items:
        yield item

      if next_page_token:
        new_request_protobuf = copy.deepcopy(request_protobuf)
        new_request_protobuf.pageToken = next_page_token
        new_requests.append((service, method, new_request_protobuf))

    requests = new_requests


def _List(requests, http, batch_url, errors):
  """Makes a series of list and/or aggregatedList batch requests.

  Args:
    requests: A list of requests to make. Each element must be a 3-element tuple
      where the first element is the service, the second element is the method
      ('List' or 'AggregatedList'), and the third element is a protocol buffer
      representing either a list or aggregatedList request.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors. If any response contains an error, it
      is added to this list.

  Returns:
    Resources encapsulated as protocol buffers as they are received
      from the server.
  """
  return _ListCore(requests, http, batch_url, errors, _HandleMessageList)


def _IsEmptyOperation(operation, service):
  """Checks whether operation argument is empty.

  Args:
    operation: Operation thats checked for emptyness.
    service: Variable used to access service.client.MESSAGES_MODULE.Operation.

  Returns:
    True if operation is empty, False otherwise.
  """
  if not isinstance(operation, service.client.MESSAGES_MODULE.Operation):
    raise ValueError('operation must be instance of'
                     + 'service.client.MESSAGES_MODULE.Operation')

  for field in operation.all_fields():
    if (field.name != 'kind' and field.name != 'warnings' and
        getattr(operation, field.name) is not None):
      return False
  return True


def _ForceBatchRequest():
  """Check if compute/force_batch_request property is set."""
  return properties.VALUES.compute.force_batch_request.GetBool()


def ListJson(requests, http, batch_url, errors):
  """Makes a series of list and/or aggregatedList batch requests.

  This function does all of:
  - Sends batch of List/AggregatedList requests
  - Extracts items from responses
  - Handles pagination

  All requests must be sent to the same client - Compute.

  Args:
    requests: A list of requests to make. Each element must be a 3-element tuple
      where the first element is the service, the second element is the method
      ('List' or 'AggregatedList'), and the third element is a protocol buffer
      representing either a list or aggregatedList request.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors. If any response contains an error, it
      is added to this list.

  Yields:
    Resources in dicts as they are received from the server.
  """
  # This is compute-specific helper. It is assumed at this point that all
  # requests are being sent to the same client (for example Compute).
  with requests[0][0].client.JsonResponseModel():
    for item in _ListCore(requests, http, batch_url, errors, _HandleJsonList):
      yield item


def MakeRequests(
    requests,
    http,
    batch_url,
    errors,
    project_override=None,
    progress_tracker=None,
    no_followup=False,
    always_return_operation=False,
    followup_overrides=None,
    log_result=True,
    log_warnings=True,
    timeout=None,
):
  """Makes one or more requests to the API.

  Each request can be either a synchronous API call or an asynchronous
  one. For synchronous calls (e.g., get and list), the result from the
  server is yielded immediately. For asynchronous calls (e.g., calls
  that return operations like insert), this function waits until the
  operation reaches the DONE state and fetches the corresponding
  object and yields that object (nothing is yielded for deletions).

  Currently, a heterogeneous set of synchronous calls can be made
  (e.g., get request to fetch a disk and instance), however, the
  asynchronous requests must be homogenous (e.g., they must all be the
  same verb on the same collection). In the future, heterogeneous
  asynchronous requests will be supported. For now, it is up to the
  client to ensure that the asynchronous requests are
  homogenous. Synchronous and asynchronous requests can be mixed.

  Args:
    requests: A list of requests to make. Each element must be a 3-element tuple
      where the first element is the service, the second element is the string
      name of the method on the service, and the last element is a protocol
      buffer representing the request.
    http: An httplib2.Http-like object.
    batch_url: The handler for making batch requests.
    errors: A list for capturing errors. If any response contains an error, it
      is added to this list.
    project_override: The override project for the returned operation to poll
      from.
    progress_tracker: progress tracker to be ticked while waiting for operations
      to finish.
    no_followup: If True, do not followup operation with a GET request.
    always_return_operation: If True, return operation object even if operation
      fails.
    followup_overrides: A list of new resource names to GET once the operation
      finishes. Generally used in renaming calls.
    log_result: Whether the Operation Waiter should print the result in past
      tense of each request.
    log_warnings: Whether warnings for completed operation should be printed.
    timeout: The maximum amount of time, in seconds, to wait for the operations
      to reach the DONE state.

  Yields:
    A response for each request. For deletion requests, no corresponding
    responses are returned.
  """
  if _RequestsAreListRequests(requests):
    for item in _List(
        requests=requests, http=http, batch_url=batch_url, errors=errors
    ):
      yield item
    return

  # send single request only if the requests size one and if enable_single_
  # request is set to true
  if not _ForceBatchRequest() and len(requests) == 1:
    service, method, request_body = requests[0]
    responses, new_errors = single_request_helper.MakeSingleRequest(
        service=service, method=method, request_body=request_body
    )
  else:
    responses, new_errors = batch_helper.MakeRequests(
        requests=requests, http=http, batch_url=batch_url)
  errors.extend(new_errors)

  operation_service = None
  resource_service = None

  # Collects all operation objects in a list so they can be waited on
  # and yields all non-operation objects since non-operation responses
  # cannot be waited on.
  operations_data = []

  if not followup_overrides:
    followup_overrides = [None for _ in requests]
  for request, response, followup_override in zip(requests, responses,
                                                  followup_overrides):
    if response is None:
      continue

    service, _, request_body = request
    if (isinstance(response, service.client.MESSAGES_MODULE.Operation) and
        not _IsEmptyOperation(response, service) and
        service.__class__.__name__ not in (
            'GlobalOperationsService', 'RegionOperationsService',
            'ZoneOperationsService', 'GlobalOrganizationOperationsService',
            'GlobalAccountsOperationsService')):

      resource_service = service
      project = None
      if hasattr(request_body, 'project'):
        if project_override:
          project = project_override
        else:
          project = request_body.project

        if response.zone:
          operation_service = service.client.zoneOperations
        elif response.region:
          operation_service = service.client.regionOperations
        else:
          operation_service = service.client.globalOperations
      else:
        operation_service = service.client.globalOrganizationOperations
      # TODO: b/313849714 - Leave only else block once the bug is fixed.
      if hasattr(request_body, 'instanceGroupManagerResizeRequest'):
        operations_data.append(
            waiters.OperationData(
                response,
                operation_service,
                resource_service,
                project=project,
                resize_request_name=request_body.instanceGroupManagerResizeRequest.name,
                no_followup=no_followup,
                followup_override=followup_override,
                always_return_operation=always_return_operation,
            )
        )
      else:
        operations_data.append(
            waiters.OperationData(
                response,
                operation_service,
                resource_service,
                project=project,
                no_followup=no_followup,
                followup_override=followup_override,
                always_return_operation=always_return_operation))

    else:
      yield response

  if operations_data:
    warnings = []
    for response in waiters.WaitForOperations(
        operations_data=operations_data,
        http=http,
        batch_url=batch_url,
        warnings=warnings,
        progress_tracker=progress_tracker,
        errors=errors,
        log_result=log_result,
        timeout=timeout,
    ):
      yield response

    if warnings and log_warnings:
      log.warning(
          utils.ConstructList('Some requests generated warnings:', warnings))

# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""KRM API Hosting API utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core import resources

_DEFAULT_API_VERSION = 'v1'

# The maximum amount of time to wait in between polling long-running operations.
_WAIT_CEILING_MS = 10 * 1000

# The maximum amount of time to wait for the long-running operation.
_MAX_WAIT_TIME_MS = 30 * 60 * 1000


def GetMessagesModule(api_version=_DEFAULT_API_VERSION):
  return apis.GetMessagesModule('krmapihosting', api_version)


def GetClientInstance(api_version=_DEFAULT_API_VERSION, use_http=True):
  """Returns an instance of the KRM API Hosting client.

  Args:
    api_version: The desired api version.
    use_http: bool, True to create an http object for this client.

  Returns:
    base_api.BaseApiClient, An instance of the Cloud Build client.
  """
  return apis.GetClientInstance(
      'krmapihosting', api_version, no_http=(not use_http))


def GetKrmApiHost(name):
  """Fetches a KRMApiHost instance, and returns it as a messages.KrmApiHost.

  Calls into the GetKrmApiHosts API.

  Args:
    name: the fully qualified name of the instance, e.g.
      "projects/p/locations/l/krmApiHosts/k".

  Returns:
    A messages.KrmApiHost.

  Raises:
    HttpNotFoundError: if the instance didn't exist.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  return client.projects_locations_krmApiHosts.Get(
      messages.KrmapihostingProjectsLocationsKrmApiHostsGetRequest(name=name))


def ListKrmApiHosts(parent):
  """Calls into the ListKrmApiHosts API.

  Args:
    parent: the fully qualified name of the parent, e.g.
      "projects/p/locations/l".

  Returns:
    A list of messages.KrmApiHost.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  resp = client.projects_locations_krmApiHosts.List(
      messages.KrmapihostingProjectsLocationsKrmApiHostsListRequest(
          parent=parent))
  return resp.krmApiHosts


def CreateKrmApiHost(parent, krm_api_host_id, krm_api_host):
  """Creates a KRMApiHost instance, and returns the creation Operation.

  Calls into the CreateKrmApiHost API.

  Args:
    parent: the fully qualified name of the parent, e.g.
      "projects/p/locations/l".
    krm_api_host_id: the ID of the krmApiHost, e.g. "my-cluster" in
      "projects/p/locations/l/krmApiHosts/my-cluster".
    krm_api_host: a messages.KrmApiHost resource (containing properties like
      the bundle config)

  Returns:
    A messages.OperationMetadata representing the long-running operation.
  """
  client = GetClientInstance()
  messages = client.MESSAGES_MODULE
  return client.projects_locations_krmApiHosts.Create(
      messages.KrmapihostingProjectsLocationsKrmApiHostsCreateRequest(
          parent=parent, krmApiHost=krm_api_host, krmApiHostId=krm_api_host_id))


def WaitForCreateKrmApiHostOperation(
    operation,
    progress_message='Waiting for cluster to create',
    max_wait_ms=_MAX_WAIT_TIME_MS):
  """Waits for the given "create" LRO to complete.

  Args:
    operation: the operation to poll.
    progress_message: the message to display while waiting for the operation.
    max_wait_ms: number of ms to wait before raising TimeoutError.

  Raises:
    apitools.base.py.HttpError: if the request returns an HTTP error.

  Returns:
    A messages.KrmApiHost resource.
  """
  client = GetClientInstance()
  operation_ref = resources.REGISTRY.ParseRelativeName(
      operation.name, collection='krmapihosting.projects.locations.operations')
  poller = waiter.CloudOperationPollerNoResources(
      client.projects_locations_operations)
  result = waiter.WaitFor(
      poller,
      operation_ref,
      progress_message,
      max_wait_ms=max_wait_ms,
      wait_ceiling_ms=_WAIT_CEILING_MS)
  json = encoding.MessageToJson(result)
  messages = GetMessagesModule()
  return encoding.JsonToMessage(messages.KrmApiHost, json)

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
"""services vpc-peering helper functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.services import exceptions
from googlecloudsdk.api_lib.util import apis

NETWORK_URL_FORMAT = 'projects/%s/global/networks/%s'


def CreateConnection(project_number, service, network, ranges):
  """Make API call to create a connection to a specific service.

  Args:
    project_number: The number of the project for which to peer the service.
    service: The name of the service to peer with.
    network: The network in consumer project to peer with.
    ranges: The names of IP CIDR ranges for peering service to use.

  Raises:
    exceptions.CreateConnectionsPermissionDeniedException: when the create
        connection API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the peering
        service.

  Returns:
    The result of the create connection operation.
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  # the API only takes project number, so we cannot use resource parser.
  request = messages.ServicenetworkingServicesConnectionsCreateRequest(
      parent='services/' + service,
      connection=messages.Connection(
          network=NETWORK_URL_FORMAT % (project_number, network),
          reservedPeeringRanges=ranges,
      ),
  )
  try:
    return client.services_connections.Create(request)
  except (
      apitools_exceptions.HttpForbiddenError,
      apitools_exceptions.HttpNotFoundError,
  ) as e:
    exceptions.ReraiseError(
        e, exceptions.CreateConnectionsPermissionDeniedException
    )


def DeleteConnection(project_number, service, network):
  """Make API call to delete an existing connection to a specific service.

  Args:
    project_number: The number of the project which is peered to the service.
    service: The name of the service peered with.
    network: The network in consumer project peered with.

  Raises:
    exceptions.DeleteConnectionsPermissionDeniedException: when the delete
        connection API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the peering
        service.

  Returns:
    The result of the delete connection operation.
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  # the API only takes project number, so we cannot use resource parser.
  request = (
      messages.ServicenetworkingServicesConnectionsDeleteConnectionRequest(
          name='services/%s/connections/-' % service,
          deleteConnectionRequest=messages.DeleteConnectionRequest(
              consumerNetwork=NETWORK_URL_FORMAT % (project_number, network)
          ),
      )
  )
  try:
    return client.services_connections.DeleteConnection(request)
  except (
      apitools_exceptions.HttpForbiddenError,
      apitools_exceptions.HttpNotFoundError,
  ) as e:
    exceptions.ReraiseError(
        e, exceptions.DeleteConnectionsPermissionDeniedException
    )


def UpdateConnection(project_number, service, network, ranges, force):
  """Make API call to update a connection to a specific service.

  Args:
    project_number: The number of the project for which to peer the service.
    service: The name of the service to peer with.
    network: The network in consumer project to peer with.
    ranges: The names of IP CIDR ranges for peering service to use.
    force: If true, update the connection even if the update can be destructive.

  Raises:
    exceptions.UpdateConnectionsPermissionDeniedException: when the update
        connection API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the peering
        service.

  Returns:
    The result of the update connection operation.
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  # the API only takes project number, so we cannot use resource parser.
  request = messages.ServicenetworkingServicesConnectionsPatchRequest(
      name='services/%s/connections/-' % service,
      connection=messages.Connection(
          network=NETWORK_URL_FORMAT % (project_number, network),
          reservedPeeringRanges=ranges,
      ),
      force=force,
  )
  try:
    return client.services_connections.Patch(request)
  except (
      apitools_exceptions.HttpForbiddenError,
      apitools_exceptions.HttpNotFoundError,
  ) as e:
    exceptions.ReraiseError(
        e, exceptions.UpdateConnectionsPermissionDeniedException
    )


def ListConnections(project_number, service, network):
  """Make API call to list connections of a network for a specific service.

  Args:
    project_number: The number of the project for which to peer the service.
    service: The name of the service to peer with.
    network: The network in consumer project to peer with.

  Raises:
    exceptions.ListConnectionsPermissionDeniedException: when the list
    connections API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the peering
        service.

  Returns:
    The list of connections.
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  # The API only takes project number, so we cannot use resource parser.
  request = messages.ServicenetworkingServicesConnectionsListRequest(
      parent='services/' + service,
      network='projects/{0}/global/networks/{1}'.format(
          project_number, network
      ),
  )
  try:
    return client.services_connections.List(request).connections
  except (
      apitools_exceptions.HttpForbiddenError,
      apitools_exceptions.HttpNotFoundError,
  ) as e:
    exceptions.ReraiseError(
        e, exceptions.ListConnectionsPermissionDeniedException
    )


def EnableVpcServiceControls(project_number, service, network):
  """Make API call to enable VPC service controls for a specific service.

  Args:
    project_number: The number of the project which is peered with the service.
    service: The name of the service to enable VPC service controls for.
    network: The network in the consumer project peered with the service.

  Raises:
    exceptions.EnableVpcServiceControlsPermissionDeniedException: when the
    enable VPC service controls API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the peering
        service.

  Returns:
    The result of the enable VPC service controls operation.
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  # the API only takes project number, so we cannot use resource parser.
  request = messages.ServicenetworkingServicesEnableVpcServiceControlsRequest(
      enableVpcServiceControlsRequest=messages.EnableVpcServiceControlsRequest(
          consumerNetwork=NETWORK_URL_FORMAT % (project_number, network)
      ),
      parent='services/' + service,
  )
  try:
    return client.services.EnableVpcServiceControls(request)
  except (
      apitools_exceptions.HttpForbiddenError,
      apitools_exceptions.HttpNotFoundError,
  ) as e:
    exceptions.ReraiseError(
        e, exceptions.EnableVpcServiceControlsPermissionDeniedException
    )


def GetVpcServiceControls(project_number, service, network):
  """Make API call to get VPC service controls for a specific service.

  Args:
    project_number: The number of the project which is peered with the service.
    service: The name of the service to get VPC service controls for.
    network: The network in the consumer project peered with the service.

  Raises:
    exceptions.GetVpcServiceControlsPermissionDeniedException: when the
    get VPC service controls API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the peering
    service.

  Returns:
    The state of the VPC service controls for the peering connection.
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE
  request = messages.ServicenetworkingServicesProjectsGlobalNetworksGetVpcServiceControlsRequest(
      name='services/%s/projects/%s/global/networks/%s'
      % (service, project_number, network)
  )
  try:
    return client.services_projects_global_networks.GetVpcServiceControls(
        request
    )
  except (
      apitools_exceptions.HttpForbiddenError,
      apitools_exceptions.HttpNotFoundError,
  ) as e:
    exceptions.ReraiseError(
        e, exceptions.GetVpcServiceControlsPermissionDeniedException
    )


def DisableVpcServiceControls(project_number, service, network):
  """Make API call to disable VPC service controls for a specific service.

  Args:
    project_number: The number of the project which is peered with the service.
    service: The name of the service to disable VPC service controls for.
    network: The network in the consumer project peered with the service.

  Raises:
    exceptions.DisableVpcServiceControlsPermissionDeniedException: when the
    disable VPC service controls API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the peering
        service.

  Returns:
    The result of the disable VPC service controls operation.
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  # the API only takes project number, so we cannot use resource parser.
  request = messages.ServicenetworkingServicesDisableVpcServiceControlsRequest(
      disableVpcServiceControlsRequest=messages.DisableVpcServiceControlsRequest(
          consumerNetwork=NETWORK_URL_FORMAT % (project_number, network)
      ),
      parent='services/' + service,
  )
  try:
    return client.services.DisableVpcServiceControls(request)
  except (
      apitools_exceptions.HttpForbiddenError,
      apitools_exceptions.HttpNotFoundError,
  ) as e:
    exceptions.ReraiseError(
        e, exceptions.DisableVpcServiceControlsPermissionDeniedException
    )


def CreatePeeredDnsDomain(project_number, service, network, name, dns_suffix):
  """Make API call to create a peered DNS domain for a specific connection.

  Args:
    project_number: The number of the project which is peered with the service.
    service: The name of the service to create a peered DNS domain for.
    network: The network in the consumer project peered with the service.
    name: The name of the peered DNS domain.
    dns_suffix: The DNS domain name suffix of the peered DNS domain.

  Raises:
    exceptions.CreatePeeredDnsDomainPermissionDeniedException: when the create
    peered DNS domain API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the peering
    service.

  Returns:
    The result of the create peered DNS domain operation.
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  # the API only takes project number, so we cannot use resource parser.
  request = messages.ServicenetworkingServicesProjectsGlobalNetworksPeeredDnsDomainsCreateRequest(
      parent='services/%s/projects/%s/global/networks/%s'
      % (service, project_number, network),
      peeredDnsDomain=messages.PeeredDnsDomain(dnsSuffix=dns_suffix, name=name),
  )
  try:
    return client.services_projects_global_networks_peeredDnsDomains.Create(
        request
    )
  except (
      apitools_exceptions.HttpForbiddenError,
      apitools_exceptions.HttpNotFoundError,
  ) as e:
    exceptions.ReraiseError(
        e,
        exceptions.CreatePeeredDnsDomainPermissionDeniedException,
    )


def DeletePeeredDnsDomain(project_number, service, network, name):
  """Make API call to delete a peered DNS domain for a specific connection.

  Args:
    project_number: The number of the project which is peered with the service.
    service: The name of the service to delete a peered DNS domain for.
    network: The network in the consumer project peered with the service.
    name: The name of the peered DNS domain.

  Raises:
    exceptions.DeletePeeredDnsDomainPermissionDeniedException: when the delete
    peered DNS domain API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the peering
    service.

  Returns:
    The result of the delete peered DNS domain operation.
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  # the API only takes project number, so we cannot use resource parser.
  request = messages.ServicenetworkingServicesProjectsGlobalNetworksPeeredDnsDomainsDeleteRequest(
      name='services/%s/projects/%s/global/networks/%s/peeredDnsDomains/%s'
      % (service, project_number, network, name)
  )
  try:
    return client.services_projects_global_networks_peeredDnsDomains.Delete(
        request
    )
  except (
      apitools_exceptions.HttpForbiddenError,
      apitools_exceptions.HttpNotFoundError,
  ) as e:
    exceptions.ReraiseError(
        e,
        exceptions.DeletePeeredDnsDomainPermissionDeniedException,
    )


def ListPeeredDnsDomains(project_number, service, network):
  """Make API call to list the peered DNS domains for a specific connection.

  Args:
    project_number: The number of the project which is peered with the service.
    service: The name of the service to list the peered DNS domains for.
    network: The network in the consumer project peered with the service.

  Raises:
    exceptions.ListPeeredDnsDomainsPermissionDeniedException: when the delete
    peered DNS domain API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the peering
    service.

  Returns:
    The list of peered DNS domains.
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE

  # the API only takes project number, so we cannot use resource parser.
  request = messages.ServicenetworkingServicesProjectsGlobalNetworksPeeredDnsDomainsListRequest(
      parent='services/%s/projects/%s/global/networks/%s'
      % (service, project_number, network)
  )
  try:
    return client.services_projects_global_networks_peeredDnsDomains.List(
        request
    ).peeredDnsDomains
  except (
      apitools_exceptions.HttpForbiddenError,
      apitools_exceptions.HttpNotFoundError,
  ) as e:
    exceptions.ReraiseError(
        e,
        exceptions.ListPeeredDnsDomainsPermissionDeniedException,
    )


def GetOperation(name):
  """Make API call to get an operation.

  Args:
    name: The name of operation.

  Raises:
    exceptions.OperationErrorException: when the getting operation API fails.
    apitools_exceptions.HttpError: Another miscellaneous error with the peering
        service.

  Returns:
    The long running operation.
  """
  client = _GetClientInstance()
  messages = client.MESSAGES_MODULE
  request = messages.ServicenetworkingOperationsGetRequest(name=name)
  try:
    return client.operations.Get(request)
  except (
      apitools_exceptions.HttpForbiddenError,
      apitools_exceptions.HttpNotFoundError,
  ) as e:
    exceptions.ReraiseError(e, exceptions.OperationErrorException)


def _GetClientInstance():
  return apis.GetClientInstance('servicenetworking', 'v1', no_http=False)

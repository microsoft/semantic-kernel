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
"""Public delegated prefixes api client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.core.exceptions import Error


class PublicDelegatedPrefixPatchError(Error):
  """Raised when an invalid update to PublicDelegatedPrefix is attempted."""


class PublicDelegatedPrefixesClient(object):
  """Client for public delegated prefixes service in the GCE API."""

  def __init__(self, client, messages, resources):
    self.client = client
    self.messages = messages
    self.resources = resources
    self._global_service = (
        self.client.apitools_client.globalPublicDelegatedPrefixes
    )
    self._regional_service = self.client.apitools_client.publicDelegatedPrefixes

  def Create(
      self,
      pdp_ref,
      parent_pap_prefix,
      parent_pdp_prefix,
      ip_cidr_range,
      description,
      enable_live_migration,
      mode,
      allocatable_prefix_length,
  ):
    """Creates a public delegated prefix."""
    is_regional = hasattr(pdp_ref, 'region')

    if parent_pdp_prefix:
      parent_prefix_ref = self.resources.Parse(
          parent_pdp_prefix,
          {'project': pdp_ref.project, 'region': pdp_ref.region},
          collection='compute.publicDelegatedPrefixes',
      )
    else:
      parent_prefix_ref = self.resources.Parse(
          parent_pap_prefix,
          {'project': pdp_ref.project},
          collection='compute.publicAdvertisedPrefixes',
      )

    parent_prefix_uri = parent_prefix_ref.SelfLink()

    public_delegated_prefix = self.messages.PublicDelegatedPrefix(
        name=pdp_ref.Name(),
        parentPrefix=parent_prefix_uri,
        ipCidrRange=ip_cidr_range,
        description=description,
        isLiveMigration=enable_live_migration,
    )

    if mode is not None:
      public_delegated_prefix.mode = mode

    if allocatable_prefix_length is not None:
      public_delegated_prefix.allocatablePrefixLength = (
          allocatable_prefix_length
      )

    if is_regional:
      request = self.messages.ComputePublicDelegatedPrefixesInsertRequest(
          publicDelegatedPrefix=public_delegated_prefix,
          project=pdp_ref.project,
          region=pdp_ref.region,
      )

      return self.client.MakeRequests(
          [(self._regional_service, 'Insert', request)]
      )[0]
    else:
      request = self.messages.ComputeGlobalPublicDelegatedPrefixesInsertRequest(
          publicDelegatedPrefix=public_delegated_prefix, project=pdp_ref.project
      )

      return self.client.MakeRequests(
          [(self._global_service, 'Insert', request)]
      )[0]

  def Delete(self, pdp_ref):
    """Deletes a public delegated prefix."""

    is_regional = hasattr(pdp_ref, 'region')

    if is_regional:
      request = self.messages.ComputePublicDelegatedPrefixesDeleteRequest(
          publicDelegatedPrefix=pdp_ref.Name(),
          project=pdp_ref.project,
          region=pdp_ref.region,
      )

      return self.client.MakeRequests(
          [(self._regional_service, 'Delete', request)]
      )
    else:
      request = self.messages.ComputeGlobalPublicDelegatedPrefixesDeleteRequest(
          publicDelegatedPrefix=pdp_ref.Name(), project=pdp_ref.project
      )

      return self.client.MakeRequests(
          [(self._global_service, 'Delete', request)]
      )

  def Get(self, pdp_ref):
    """Gets a public delegated prefix."""

    is_regional = hasattr(pdp_ref, 'region')

    if is_regional:
      request = self.messages.ComputePublicDelegatedPrefixesGetRequest(
          publicDelegatedPrefix=pdp_ref.Name(),
          project=pdp_ref.project,
          region=pdp_ref.region,
      )

      return self.client.MakeRequests(
          [(self._regional_service, 'Get', request)]
      )[0]
    else:
      request = self.messages.ComputeGlobalPublicDelegatedPrefixesGetRequest(
          publicDelegatedPrefix=pdp_ref.Name(), project=pdp_ref.project
      )

      return self.client.MakeRequests([(self._global_service, 'Get', request)])[
          0
      ]

  def _Patch(self, pdp_ref, resource):
    """Patches a public delegated prefix resource.

    Args:
      pdp_ref: resource reference.
      resource: PublicDelegatedPrefix resource.

    Returns:
      Operation result from the poller.
    """
    # Drop all fields except fingerprint and modifiable ones.
    resource = self.messages.PublicDelegatedPrefix(
        fingerprint=resource.fingerprint,
        publicDelegatedSubPrefixs=resource.publicDelegatedSubPrefixs,
    )
    include_fields = []
    if not resource.publicDelegatedSubPrefixs:
      include_fields.append('publicDelegatedSubPrefixs')

    is_regional = hasattr(pdp_ref, 'region')

    if is_regional:
      request = self.messages.ComputePublicDelegatedPrefixesPatchRequest(
          publicDelegatedPrefix=pdp_ref.Name(),
          publicDelegatedPrefixResource=resource,
          project=pdp_ref.project,
          region=pdp_ref.region,
      )

      with self.client.apitools_client.IncludeFields(include_fields):
        operation = self._regional_service.Patch(request)
      operation_ref = self.resources.Parse(
          operation.selfLink, collection='compute.regionOperations'
      )
      operation_poller = poller.Poller(self._regional_service)
    else:
      request = self.messages.ComputeGlobalPublicDelegatedPrefixesPatchRequest(
          publicDelegatedPrefix=pdp_ref.Name(),
          publicDelegatedPrefixResource=resource,
          project=pdp_ref.project,
      )

      with self.client.apitools_client.IncludeFields(include_fields):
        operation = self._global_service.Patch(request)
      operation_ref = self.resources.Parse(
          operation.selfLink, collection='compute.globalOperations'
      )
      operation_poller = poller.Poller(self._global_service)

    return waiter.WaitFor(
        operation_poller,
        operation_ref,
        'Updating public delegated prefix [{}].'.format(pdp_ref.Name()),
    )

  def AddSubPrefix(
      self,
      pdp_ref,
      name,
      ip_cidr_range,
      description,
      delegatee_project,
      is_addresses,
  ):
    """Adds a delegated sub prefix to public delegated prefix using PATCH.

    Args:
      pdp_ref: resource reference.
      name: sub prefix name.
      ip_cidr_range: sub prefix IP address range.
      description: sub prefix description.
      delegatee_project: sub prefix target project.
      is_addresses: sub prefix isAddress parameter.

    Returns:
      Operation result from the poller.

    Raises:
      PublicDelegatedPrefixPatchError:
        when delegated prefix already has a sub prefix with specified name.
    """

    resource = self.Get(pdp_ref)

    for sub_prefix in resource.publicDelegatedSubPrefixs:
      if sub_prefix.name == name:
        raise PublicDelegatedPrefixPatchError(
            'Delegated sub prefix [{}] already exists in public delegated '
            'prefix [{}]'.format(name, pdp_ref.Name())
        )

    resource.publicDelegatedSubPrefixs.append(
        self.messages.PublicDelegatedPrefixPublicDelegatedSubPrefix(
            name=name,
            description=description,
            ipCidrRange=ip_cidr_range,
            delegateeProject=delegatee_project,
            isAddress=is_addresses,
        )
    )

    return self._Patch(pdp_ref, resource)

  def RemoveSubPrefix(self, pdp_ref, name):
    """Removes a delegated sub prefix from public delegated prefix using PATCH.

    Args:
      pdp_ref: resource reference.
      name: name of sub prefix to remove.

    Returns:
      Operation result from the poller.

    Raises:
      PublicDelegatedPrefixPatchError:
        when delegated prefix does not have a sub prefix with specified name.
    """

    resource = self.Get(pdp_ref)

    index_to_remove = None
    for i, sub_prefix in enumerate(resource.publicDelegatedSubPrefixs):
      if sub_prefix.name == name:
        index_to_remove = i

    if index_to_remove is None:
      raise PublicDelegatedPrefixPatchError(
          'Delegated sub prefix [{}] does not exist in public delegated '
          'prefix [{}]'.format(name, pdp_ref.Name())
      )

    resource.publicDelegatedSubPrefixs.pop(index_to_remove)

    return self._Patch(pdp_ref, resource)

  def Announce(self, pdp_ref):
    """Announce a public delegated prefix."""

    request = self.messages.ComputePublicDelegatedPrefixesAnnounceRequest(
        publicDelegatedPrefix=pdp_ref.Name(),
        project=pdp_ref.project,
        region=pdp_ref.region,
    )

    return self.client.MakeRequests(
        [(self._regional_service, 'Announce', request)]
    )

  def Withdraw(self, pdp_ref):
    """Withdraw a public delegated prefix."""

    request = self.messages.ComputePublicDelegatedPrefixesWithdrawRequest(
        publicDelegatedPrefix=pdp_ref.Name(),
        project=pdp_ref.project,
        region=pdp_ref.region,
    )

    return self.client.MakeRequests(
        [(self._regional_service, 'Withdraw', request)]
    )

# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Convenience functions for dealing with instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ipaddress
from googlecloudsdk.api_lib.compute import alias_ip_range_utils
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.command_lib.compute import scope as compute_scopes
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
import six


def CreateNetworkInterfaceMessage(
    resources,
    compute_client,
    network,
    subnet,
    project,
    location,
    scope,
    nic_type=None,
    no_address=None,
    address=None,
    private_network_ip=None,
    alias_ip_ranges_string=None,
    network_tier=None,
    no_public_dns=None,
    public_dns=None,
    no_public_ptr=None,
    public_ptr=None,
    no_public_ptr_domain=None,
    public_ptr_domain=None,
    stack_type=None,
    ipv6_network_tier=None,
    ipv6_public_ptr_domain=None,
    queue_count=None,
    ipv6_address=None,
    ipv6_prefix_length=None,
    internal_ipv6_address=None,
    internal_ipv6_prefix_length=None,
    network_attachment=None,
    external_ipv6_address=None,
    external_ipv6_prefix_length=None,
    parent_nic_name=None,
    vlan=None,
    igmp_query=None,
):
  """Returns a new NetworkInterface message."""
  # TODO(b/30460572): instance reference should have zone name, not zone URI.
  if scope == compute_scopes.ScopeEnum.ZONE:
    region = utils.ZoneNameToRegionName(location.split('/')[-1])
  elif scope == compute_scopes.ScopeEnum.REGION:
    region = location
  messages = compute_client.messages
  network_interface = messages.NetworkInterface()
  # By default interface is attached to default network. If network or subnet
  # are specified they're used instead.
  if subnet is not None:
    subnet_ref = resources.Parse(
        subnet,
        collection='compute.subnetworks',
        params={'project': project, 'region': region},
    )
    network_interface.subnetwork = subnet_ref.SelfLink()
  if network is not None:
    network_ref = resources.Parse(
        network,
        params={
            'project': project,
        },
        collection='compute.networks',
    )
    network_interface.network = network_ref.SelfLink()
  # We only populate the default network when network-attachment is not
  # specified because for a network interface targeting a network attachment,
  # both network and subnetwork should not be there.
  elif subnet is None and network_attachment is None:
    network_ref = resources.Parse(
        constants.DEFAULT_NETWORK,
        params={'project': project},
        collection='compute.networks',
    )
    network_interface.network = network_ref.SelfLink()

  if network_attachment is not None:
    network_interface.networkAttachment = network_attachment

  if private_network_ip is not None:
    # Try interpreting the address as IP address.
    try:
      # ipaddress only allows unicode input
      ipaddress.ip_address(six.text_type(private_network_ip))
      network_interface.networkIP = private_network_ip
    except ValueError:
      # ipaddress could not resolve as an IP address.
      network_interface.networkIP = instances_flags.GetAddressRef(
          resources, private_network_ip, region
      ).SelfLink()

  if nic_type is not None:
    network_interface.nicType = (
        messages.NetworkInterface.NicTypeValueValuesEnum(nic_type)
    )

  if queue_count is not None:
    network_interface.queueCount = queue_count

  if alias_ip_ranges_string:
    network_interface.aliasIpRanges = (
        alias_ip_range_utils.CreateAliasIpRangeMessagesFromString(
            messages, True, alias_ip_ranges_string
        )
    )

  if stack_type is not None:
    network_interface.stackType = (
        messages.NetworkInterface.StackTypeValueValuesEnum(stack_type)
    )

  # Can't use StackTypeValueValuesEnum to compare because in some api versions
  # IPv6 Only instances may not be supported yet and StackTypeValueValuesEnum
  # may not contain IPV6_ONLY at all
  no_access_config = stack_type == 'IPV6_ONLY'

  # For a ipv6-only network interface or a network interface targeting a
  # network attachment, access config is not needed/wanted.
  if not no_access_config and not no_address and network_attachment is None:
    access_config = messages.AccessConfig(
        name=constants.DEFAULT_ACCESS_CONFIG_NAME,
        type=messages.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT,
    )
    if network_tier is not None:
      access_config.networkTier = (
          messages.AccessConfig.NetworkTierValueValuesEnum(network_tier)
      )

    # If the user provided an external IP, populate the access
    # config with it.
    address_resource = instances_flags.ExpandAddressFlag(
        resources, compute_client, address, region
    )
    if address_resource:
      access_config.natIP = address_resource

    if no_public_dns:
      access_config.setPublicDns = False
    elif public_dns:
      access_config.setPublicDns = True

    if no_public_ptr:
      access_config.setPublicPtr = False
    elif public_ptr:
      access_config.setPublicPtr = True

    if not no_public_ptr_domain and public_ptr_domain is not None:
      access_config.publicPtrDomainName = public_ptr_domain

    network_interface.accessConfigs = [access_config]

  # New flag has higher priority than the old one.
  if external_ipv6_address is None:
    external_ipv6_address = ipv6_address

  if external_ipv6_prefix_length is None:
    external_ipv6_prefix_length = ipv6_prefix_length

  if (
      ipv6_network_tier is not None
      or ipv6_public_ptr_domain is not None
      or external_ipv6_address
  ):
    ipv6_access_config = messages.AccessConfig(
        name=constants.DEFAULT_IPV6_ACCESS_CONFIG_NAME,
        type=messages.AccessConfig.TypeValueValuesEnum.DIRECT_IPV6,
    )
    network_interface.ipv6AccessConfigs = [ipv6_access_config]

  if ipv6_network_tier is not None:
    ipv6_access_config.networkTier = (
        messages.AccessConfig.NetworkTierValueValuesEnum(ipv6_network_tier)
    )

  if ipv6_public_ptr_domain is not None:
    ipv6_access_config.publicPtrDomainName = ipv6_public_ptr_domain

  if external_ipv6_address:
    # Try interpreting the address as IPv6.
    try:
      # ipaddress only allows unicode input
      ipaddress.ip_address(six.text_type(external_ipv6_address))
      ipv6_access_config.externalIpv6 = external_ipv6_address
    except ValueError:
      # ipaddress could not resolve as an IPv6 address.
      ipv6_access_config.externalIpv6 = instances_flags.GetAddressRef(
          resources, external_ipv6_address, region
      ).SelfLink()
    if external_ipv6_prefix_length:
      ipv6_access_config.externalIpv6PrefixLength = external_ipv6_prefix_length
    else:
      ipv6_access_config.externalIpv6PrefixLength = 96

  if internal_ipv6_address is not None:
    # Try interpreting the address as IPv6.
    try:
      # ipaddress only allows unicode input
      if '/' in six.text_type(internal_ipv6_address):
        ipaddress.ip_network(six.text_type(internal_ipv6_address))
      else:
        ipaddress.ip_address(six.text_type(internal_ipv6_address))
      network_interface.ipv6Address = internal_ipv6_address
    except ValueError:
      # ipaddress could not resolve as an IPv6 address.
      network_interface.ipv6Address = instances_flags.GetAddressRef(
          resources, internal_ipv6_address, region
      ).SelfLink()

  if internal_ipv6_prefix_length is not None:
    network_interface.internalIpv6PrefixLength = internal_ipv6_prefix_length

  if parent_nic_name is not None:
    network_interface.parentNicName = parent_nic_name

  if vlan is not None:
    network_interface.vlan = vlan

  if igmp_query is not None:
    network_interface.igmpQuery = (
        messages.NetworkInterface.IgmpQueryValueValuesEnum(igmp_query)
    )

  return network_interface

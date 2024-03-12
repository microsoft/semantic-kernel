# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for update to instance network interfaces."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ipaddress

from googlecloudsdk.api_lib.compute import alias_ip_range_utils
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import utils as api_utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instances import flags as instances_flags
from googlecloudsdk.command_lib.compute.instances.network_interfaces import flags as network_interfaces_flags
from googlecloudsdk.command_lib.compute.security_policies import (
    flags as security_policy_flags,
)
import six


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  r"""Update a Compute Engine virtual machine network interface.

  *{command}* updates network interfaces of a Compute Engine
  virtual machine. For example:

    $ {command} example-instance --zone us-central1-a --aliases r1:172.16.0.1/32

  sets 172.16.0.1/32 from range r1 of the default interface's subnetwork
  as the interface's alias IP.
  """

  support_ipv6_assignment = False

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    instances_flags.INSTANCE_ARG.AddArgument(parser)
    network_interfaces_flags.AddNetworkInterfaceArgForUpdate(parser)
    network_interfaces_flags.AddNetworkArg(parser)
    network_interfaces_flags.AddSubnetworkArg(parser)
    network_interfaces_flags.AddPrivateNetworkIpArg(parser)
    network_interfaces_flags.AddAliasesArg(parser)
    network_interfaces_flags.AddStackTypeArg(parser)
    network_interfaces_flags.AddIpv6NetworkTierArg(parser)
    network_interfaces_flags.AddExternalIpv6AddressArg(parser)
    network_interfaces_flags.AddExternalIpv6PrefixLengthArg(parser)
    network_interfaces_flags.AddInternalIpv6AddressArg(parser)
    network_interfaces_flags.AddInternalIpv6PrefixLengthArg(parser)

    if cls.support_ipv6_assignment:
      network_interfaces_flags.AddIpv6AddressArg(parser)
      network_interfaces_flags.AddIpv6PrefixLengthArg(parser)

    cls.SECURITY_POLICY_ARG = (
        security_policy_flags.SecurityPolicyRegionalArgumentForTargetResource(
            resource='instance network interface'
        )
    )
    cls.SECURITY_POLICY_ARG.AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client.apitools_client
    messages = holder.client.messages
    resources = holder.resources

    instance_ref = instances_flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetDefaultScopeLister(holder.client),
    )

    instance = client.instances.Get(
        messages.ComputeInstancesGetRequest(**instance_ref.AsDict())
    )
    for i in instance.networkInterfaces:
      if i.name == args.network_interface:
        fingerprint = i.fingerprint
        break
    else:
      raise exceptions.UnknownArgumentException(
          'network-interface',
          'Instance does not have a network interface [{}], '
          'present interfaces are [{}].'.format(
              args.network_interface,
              ', '.join([i.name for i in instance.networkInterfaces]),
          ),
      )

    # Empty string is a valid value.
    if getattr(args, 'security_policy', None) is not None:
      if getattr(args, 'security_policy', None):
        security_policy_ref = self.SECURITY_POLICY_ARG.ResolveAsResource(
            args, holder.resources).SelfLink()
      # If security policy is an empty string we should clear the current policy
      else:
        security_policy_ref = None
      request_body = messages.InstancesSetSecurityPolicyRequest(
          networkInterfaces=[args.network_interface],
          securityPolicy=security_policy_ref,
      )
      request = messages.ComputeInstancesSetSecurityPolicyRequest(
          project=instance_ref.project,
          instance=instance_ref.instance,
          zone=instance_ref.zone,
          instancesSetSecurityPolicyRequest=request_body,
      )
      operation = client.instances.SetSecurityPolicy(request)
      operation_ref = holder.resources.Parse(
          operation.selfLink, collection='compute.zoneOperations'
      )

      operation_poller = poller.Poller(client.instances)
      return waiter.WaitFor(
          operation_poller,
          operation_ref,
          'Setting security policy for network interface [{0}] of instance'
          ' [{1}]'.format(args.network_interface, instance_ref.Name()),
      )

    network_uri = None
    if getattr(args, 'network', None) is not None:
      network_uri = resources.Parse(
          args.network,
          {'project': instance_ref.project},
          collection='compute.networks',
      ).SelfLink()

    subnetwork_uri = None
    region = api_utils.ZoneNameToRegionName(instance_ref.zone)
    if getattr(args, 'subnetwork', None) is not None:
      subnetwork_uri = resources.Parse(
          args.subnetwork,
          {'project': instance_ref.project, 'region': region},
          collection='compute.subnetworks',
      ).SelfLink()

    stack_type = getattr(args, 'stack_type', None)
    ipv6_address = getattr(args, 'ipv6_address', None)
    ipv6_prefix_length = getattr(args, 'ipv6_prefix_length', None)
    external_ipv6_address = getattr(args, 'external_ipv6_address', None)
    external_ipv6_prefix_length = getattr(
        args, 'external_ipv6_prefix_length', None
    )
    internal_ipv6_address = getattr(args, 'internal_ipv6_address', None)
    internal_ipv6_prefix_length = getattr(
        args, 'internal_ipv6_prefix_length', None
    )
    if stack_type is not None:
      stack_type_enum = messages.NetworkInterface.StackTypeValueValuesEnum(
          stack_type
      )
      ipv6_network_tier = getattr(args, 'ipv6_network_tier', None)

      ipv6_access_configs = []
      if ipv6_network_tier is not None:
        # If provide IPv6 network tier then set IPv6 access config in request.
        ipv6_access_config = messages.AccessConfig(
            name=constants.DEFAULT_IPV6_ACCESS_CONFIG_NAME,
            type=messages.AccessConfig.TypeValueValuesEnum.DIRECT_IPV6,
        )
        ipv6_access_config.networkTier = (
            messages.AccessConfig.NetworkTierValueValuesEnum(ipv6_network_tier)
        )
        if not external_ipv6_address and ipv6_address:
          # For alpha gcloud only
          external_ipv6_address = ipv6_address
        if not external_ipv6_prefix_length and ipv6_prefix_length:
          # For alpha gcloud only
          external_ipv6_prefix_length = ipv6_prefix_length
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
            ipv6_access_config.externalIpv6PrefixLength = (
                external_ipv6_prefix_length
            )
          else:
            ipv6_access_config.externalIpv6PrefixLength = 96
        ipv6_access_configs = [ipv6_access_config]
      if internal_ipv6_address:
        # Try interpreting the address as IPv6.
        try:
          # ipaddress only allows unicode input
          if '/' in six.text_type(internal_ipv6_address):
            ipaddress.ip_network(six.text_type(internal_ipv6_address))
          else:
            ipaddress.ip_address(six.text_type(internal_ipv6_address))
        except ValueError:
          # ipaddress could not resolve as an IPv6 address.
          internal_ipv6_address = instances_flags.GetAddressRef(
              resources, internal_ipv6_address, region
          ).SelfLink()
      patch_network_interface = messages.NetworkInterface(
          aliasIpRanges=(
              alias_ip_range_utils.CreateAliasIpRangeMessagesFromString(
                  messages, True, args.aliases
              )
          ),
          network=network_uri,
          subnetwork=subnetwork_uri,
          networkIP=getattr(args, 'private_network_ip', None),
          stackType=stack_type_enum,
          ipv6AccessConfigs=ipv6_access_configs,
          fingerprint=fingerprint,
          ipv6Address=internal_ipv6_address,
          internalIpv6PrefixLength=internal_ipv6_prefix_length,
      )
    else:
      patch_network_interface = messages.NetworkInterface(
          aliasIpRanges=(
              alias_ip_range_utils.CreateAliasIpRangeMessagesFromString(
                  messages, True, args.aliases
              )
          ),
          network=network_uri,
          subnetwork=subnetwork_uri,
          networkIP=getattr(args, 'private_network_ip', None),
          fingerprint=fingerprint,
      )

    request = messages.ComputeInstancesUpdateNetworkInterfaceRequest(
        project=instance_ref.project,
        instance=instance_ref.instance,
        zone=instance_ref.zone,
        networkInterface=args.network_interface,
        networkInterfaceResource=patch_network_interface,
    )

    cleared_fields = []
    if not patch_network_interface.aliasIpRanges:
      cleared_fields.append('aliasIpRanges')
    with client.IncludeFields(cleared_fields):
      operation = client.instances.UpdateNetworkInterface(request)
    operation_ref = holder.resources.Parse(
        operation.selfLink, collection='compute.zoneOperations'
    )

    operation_poller = poller.Poller(client.instances)
    return waiter.WaitFor(
        operation_poller,
        operation_ref,
        'Updating network interface [{0}] of instance [{1}]'.format(
            args.network_interface, instance_ref.Name()
        ),
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  r"""Update a Compute Engine virtual machine network interface.

  *{command}* updates network interfaces of a Compute Engine
  virtual machine. For example:

    $ {command} example-instance --zone us-central1-a --aliases r1:172.16.0.1/32

  sets 172.16.0.1/32 from range r1 of the default interface's subnetwork
  as the interface's alias IP.
  """

  support_ipv6_assignment = False


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(UpdateBeta):
  r"""Update a Compute Engine virtual machine network interface.

  *{command}* updates network interfaces of a Compute Engine
  virtual machine. For example:

    $ {command} example-instance --zone us-central1-a --aliases r1:172.16.0.1/32

  sets 172.16.0.1/32 from range r1 of the default interface's subnetwork
  as the interface's alias IP.
  """

  support_ipv6_assignment = True

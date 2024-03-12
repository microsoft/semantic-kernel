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
"""Command for updating access configs for virtual machine instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
        *{command}* is used to update access configurations for network
        interfaces of Compute Engine virtual machines. IPv4 and IPv6 access
        configurations cannot be updated together.
        """,
    'EXAMPLES':
        """
    To update public PTR record in IPv4 access config in network interface 'nic0' of an instance, run:

      $ {command} example-instance --network-interface=nic0 --zone=us-central1-b \
          --public-ptr --public-ptr-domain=exampledomain.com.

    To update public PTR record in IPv6 access config in default network interface 'nic0' of an instance, run:

      $ {command} example-instance --zone=us-central1-b \
          --ipv6-public-ptr-domain=exampledomain.com.
  """
}


def _Args(parser, support_public_dns, support_network_tier):
  """Register parser args common to all tracks."""

  flags.INSTANCE_ARG.AddArgument(parser)
  flags.AddNetworkInterfaceArgs(parser)
  flags.AddPublicPtrArgs(parser, instance=False)
  flags.AddIpv6PublicPtrArgs(parser)
  if support_public_dns:
    flags.AddPublicDnsArgs(parser, instance=False)
  if support_network_tier:
    flags.AddNetworkTierArgs(parser, instance=False, for_update=True)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateAccessConfigInstances(base.UpdateCommand):
  """Update a Compute Engine virtual machine access configuration."""

  _support_public_dns = False
  _support_network_tier = False

  @classmethod
  def Args(cls, parser):
    _Args(
        parser,
        support_public_dns=cls._support_public_dns,
        support_network_tier=cls._support_network_tier)

  def CreateReference(self, client, resources, args):
    return flags.INSTANCE_ARG.ResolveAsResource(
        args, resources, scope_lister=flags.GetInstanceZoneScopeLister(client))

  def CreateV4AddressConfig(self, client):
    return client.messages.AccessConfig(
        type=client.messages.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)

  def CreateV6AddressConfig(self, client):
    return client.messages.AccessConfig(
        type=client.messages.AccessConfig.TypeValueValuesEnum.DIRECT_IPV6)

  def GetGetRequest(self, client, instance_ref):
    return (client.apitools_client.instances, 'Get',
            client.messages.ComputeInstancesGetRequest(**instance_ref.AsDict()))

  def GetUpdateRequest(self, client, args, instance_ref, access_config):
    return (client.apitools_client.instances, 'UpdateAccessConfig',
            client.messages.ComputeInstancesUpdateAccessConfigRequest(
                instance=instance_ref.instance,
                networkInterface=args.network_interface,
                accessConfig=access_config,
                project=instance_ref.project,
                zone=instance_ref.zone))

  # Generate updated AccessConfig for PATCH semantic.
  def Modify(self, client, args, original):
    set_public_dns = None
    if self._support_public_dns:
      if args.public_dns:
        set_public_dns = True
      elif args.no_public_dns:
        set_public_dns = False

    set_ptr = None
    if args.public_ptr:
      set_ptr = True
    elif args.no_public_ptr:
      set_ptr = False

    set_ipv6_ptr = None
    if args.ipv6_public_ptr_domain:
      set_ipv6_ptr = True
    elif args.no_ipv6_public_ptr:
      set_ipv6_ptr = False

    if (set_ptr is not None and set_ipv6_ptr is not None):
      raise exceptions.InvalidArgumentException(
          '--ipv6-public-ptr-domain',
          'Cannot update --public-ptr-domain and --ipv6-public-ptr-domain at same time.'
      )

    if self._support_public_dns and set_public_dns is not None:
      access_config = self.CreateV4AddressConfig(client)
      access_config.setPublicDns = set_public_dns
      return access_config

    if set_ptr is not None:
      access_config = self.CreateV4AddressConfig(client)
      access_config.setPublicPtr = set_ptr
      new_ptr = '' if args.public_ptr_domain is None else args.public_ptr_domain
      access_config.publicPtrDomainName = new_ptr
      return access_config

    if set_ipv6_ptr is not None:
      access_config = self.CreateV6AddressConfig(client)
      new_ptr = '' if args.ipv6_public_ptr_domain is None else args.ipv6_public_ptr_domain
      access_config.publicPtrDomainName = new_ptr
      return access_config

    if self._support_network_tier and args.network_tier is not None:
      access_config = self.CreateV4AddressConfig(client)
      access_config.networkTier = (
          client.messages.AccessConfig.NetworkTierValueValuesEnum(
              args.network_tier))
      return access_config

    return None

  def Run(self, args):
    flags.ValidatePublicPtrFlags(args)
    flags.ValidateIpv6PublicPtrFlags(args)
    if self._support_public_dns:
      flags.ValidatePublicDnsFlags(args)
    if self._support_network_tier:
      flags.ValidateNetworkTierArgs(args)
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = self.CreateReference(client, holder.resources, args)
    get_request = self.GetGetRequest(client, instance_ref)

    objects = client.MakeRequests([get_request])

    new_access_config = self.Modify(client, args, objects[0])

    # If Modify() returns None, then there is no work to be done, so we
    # print the resource and return.
    if new_access_config is None:
      log.status.Print('No change requested; skipping update for [{0}].'.format(
          objects[0].name))
      return objects

    return client.MakeRequests(requests=[
        self.GetUpdateRequest(client, args, instance_ref, new_access_config)
    ])


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateAccessConfigInstancesBeta(UpdateAccessConfigInstances):
  """Update a Compute Engine virtual machine access configuration."""

  _support_public_dns = False
  _support_network_tier = False


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAccessConfigInstancesAlpha(UpdateAccessConfigInstances):
  """Update a Compute Engine virtual machine access configuration."""

  _support_public_dns = True
  _support_network_tier = True


UpdateAccessConfigInstances.detailed_help = DETAILED_HELP

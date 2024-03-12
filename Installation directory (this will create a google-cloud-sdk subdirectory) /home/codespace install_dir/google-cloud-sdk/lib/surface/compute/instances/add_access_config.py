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
"""Command for adding access configs to virtual machine instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags


DETAILED_HELP = {
    'DESCRIPTION': """
*{command}* is used to create access configurations for network
interfaces of Compute Engine virtual machines. This allows you
to assign a public, external IP to a virtual machine.
""",
    'EXAMPLES': """
To assign an public, externally accessible IP to a virtual machine named
``example-instance'' in zone ``us-central1-a'', run:

  $ {command} example-instance --zone=us-central1-a

To assign the specific, reserved public IP address ``123.456.789.123''
to the virtual machine, run:

  $ {command} example-instance --zone=us-central1-a --address=123.456.789.123
""",
}


def _Args(parser, support_public_dns):
  """Register parser args common to all tracks."""

  parser.add_argument(
      '--access-config-name',
      default=constants.DEFAULT_ACCESS_CONFIG_NAME,
      help="""\
      Specifies the name of the new access configuration. ``{0}''
      is used as the default if this flag is not provided. Since ONE_TO_ONE_NAT
      is currently the only access-config type, it is not recommended that you
      change this value.
      """.format(constants.DEFAULT_ACCESS_CONFIG_NAME))

  parser.add_argument(
      '--address',
      action=arg_parsers.StoreOnceAction,
      help="""\
      Specifies the external IP address of the new access
      configuration. If this is not specified, then the service will
      choose an available ephemeral IP address. If an explicit IP
      address is given, then that IP address must be reserved by the
      project and not be in use by another resource.
      """)

  flags.AddNetworkInterfaceArgs(parser)
  flags.AddPublicPtrArgs(parser, instance=False)
  if support_public_dns:
    flags.AddPublicDnsArgs(parser, instance=False)
  flags.AddNetworkTierArgs(parser, instance=False)
  flags.INSTANCE_ARG.AddArgument(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AddAccessConfigInstances(base.SilentCommand):
  """Create a Compute Engine virtual machine access configuration."""

  _support_public_dns = False

  @classmethod
  def Args(cls, parser):
    _Args(parser, support_public_dns=cls._support_public_dns)

  def Run(self, args):
    """Invokes request necessary for adding an access config."""
    flags.ValidateNetworkTierArgs(args)

    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))

    access_config = client.messages.AccessConfig(
        name=args.access_config_name,
        natIP=args.address,
        type=client.messages.AccessConfig.TypeValueValuesEnum.ONE_TO_ONE_NAT)

    if self._support_public_dns:
      flags.ValidatePublicDnsFlags(args)
      if args.no_public_dns is True:
        access_config.setPublicDns = False
      elif args.public_dns is True:
        access_config.setPublicDns = True

    flags.ValidatePublicPtrFlags(args)
    if args.no_public_ptr is True:
      access_config.setPublicPtr = False
    elif args.public_ptr is True:
      access_config.setPublicPtr = True

    if (args.no_public_ptr_domain is not True and
        args.public_ptr_domain is not None):
      access_config.publicPtrDomainName = args.public_ptr_domain

    network_tier = getattr(args, 'network_tier', None)
    if network_tier is not None:
      access_config.networkTier = (client.messages.AccessConfig.
                                   NetworkTierValueValuesEnum(network_tier))

    request = client.messages.ComputeInstancesAddAccessConfigRequest(
        accessConfig=access_config,
        instance=instance_ref.Name(),
        networkInterface=args.network_interface,
        project=instance_ref.project,
        zone=instance_ref.zone)

    return client.MakeRequests([(client.apitools_client.instances,
                                 'AddAccessConfig', request)])


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class AddAccessConfigInstancesBeta(AddAccessConfigInstances):
  """Create a Compute Engine virtual machine access configuration."""

  _support_public_dns = False


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddAccessConfigInstancesAlpha(AddAccessConfigInstances):
  """Create a Compute Engine virtual machine access configuration."""

  _support_public_dns = True

AddAccessConfigInstances.detailed_help = DETAILED_HELP

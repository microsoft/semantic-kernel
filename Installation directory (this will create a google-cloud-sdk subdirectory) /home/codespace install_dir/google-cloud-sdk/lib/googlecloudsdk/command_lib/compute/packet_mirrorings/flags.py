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
"""Flags for the compute packet mirroring commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags


class PacketMirroringCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(PacketMirroringCompleter, self).__init__(
        collection='compute.packetMirrorings',
        list_command='alpha compute packet-mirrorings list --uri',
        **kwargs)


def PacketMirroringArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='packet mirroring',
      completer=PacketMirroringCompleter,
      plural=plural,
      custom_plural='packet mirrorings',
      required=required,
      regional_collection='compute.packetMirrorings')


def AddCreateArgs(parser):
  """Adds flags for creating packet mirroring resources."""
  _AddArgs(parser)


def AddUpdateArgs(parser):
  """Adds flags for updating packet mirroring resources."""
  _AddArgs(parser, is_for_update=True)


def _AddArgs(parser, is_for_update=False):
  """Adds args for create/update subcommands."""
  # Network cannot be updated.
  if not is_for_update:
    _AddNetworkArg(parser)

  _AddCollectorIlbArg(parser, is_for_update)

  parser.add_argument(
      '--description',
      help='Optional, textual description for the packet mirroring.')

  parser.add_argument(
      '--enable',
      action='store_true',
      help="""Enable or disable the packet-mirroring.""",
      default=True if not is_for_update else None)

  _AddMirroredInstancesArg(parser, is_for_update)
  _AddMirroredTagsArg(parser, is_for_update)
  _AddMirroredSubnetsArg(parser, is_for_update)

  _AddFilterCidrRangesArg(parser, is_for_update)
  _AddFilterProtocolsArg(parser, is_for_update)
  _AddFilterDirectionArg(parser)


def _AddNetworkArg(parser):
  parser.add_argument(
      '--network',
      required=True,
      help="""\
        Network for this packet mirroring.
        Only the packets in this network will be mirrored. It is mandatory
        that all mirrored VMs have a network interface controller (NIC) in
        the given network. All mirrored subnetworks should belong to the
        given network.

        You can provide this as the full URL to the network, partial URL,
        or name.
        For example, the following are valid values:
          * https://compute.googleapis.com/compute/v1/projects/myproject/
            global/networks/network-1
          * projects/myproject/global/networks/network-1
          * network-1
        """)


def _AddCollectorIlbArg(parser, is_for_update=False):
  parser.add_argument(
      '--collector-ilb',
      required=not is_for_update,
      help="""\
      Forwarding rule configured as collector. This must be a regional
      forwarding rule (in the same region) with load balancing scheme INTERNAL
      and isMirroringCollector set to true.

      You can provide this as the full URL to the forwarding rule, partial URL,
      or name.
      For example, the following are valid values:
        * https://compute.googleapis.com/compute/v1/projects/myproject/
          regions/us-central1/forwardingRules/fr-1
        * projects/myproject/regions/us-central1/forwardingRules/fr-1
        * fr-1
      """)


def _AddMirroredInstancesArg(parser, is_for_update=False):
  """Adds args to specify mirrored instances."""
  if is_for_update:
    instances = parser.add_mutually_exclusive_group(help="""\
      Update the mirrored instances of this packet mirroring.
      """)
    instances.add_argument(
        '--add-mirrored-instances',
        type=arg_parsers.ArgList(),
        metavar='INSTANCE',
        help='List of instances to add to the packet mirroring.',
    )
    instances.add_argument(
        '--remove-mirrored-instances',
        type=arg_parsers.ArgList(),
        metavar='INSTANCE',
        help='List of instances to remove from the packet mirroring.'
    )
    instances.add_argument(
        '--set-mirrored-instances',
        type=arg_parsers.ArgList(),
        metavar='INSTANCE',
        help='List of instances to be mirrored on the packet mirroring.'
    )
    instances.add_argument(
        '--clear-mirrored-instances',
        action='store_true',
        default=None,
        help=('If specified, clear the existing instances '
              'from the packet mirroring.'))
  else:
    parser.add_argument(
        '--mirrored-instances',
        type=arg_parsers.ArgList(),
        metavar='INSTANCE',
        help="""\
        List of instances to be mirrored.
        You can provide this as the full or valid partial URL to the instance.
        For example, the following are valid values:
          * https://compute.googleapis.com/compute/v1/projects/myproject/
            zones/us-central1-a/instances/instance-
          * projects/myproject/zones/us-central1-a/instances/instance-1
        """)


def _AddMirroredSubnetsArg(parser, is_for_update=False):
  """Adds args to specify mirrored subnets."""
  if is_for_update:
    subnets = parser.add_mutually_exclusive_group(help="""\
      Update the mirrored subnets of this packet mirroring.
      """)
    subnets.add_argument(
        '--add-mirrored-subnets',
        type=arg_parsers.ArgList(),
        metavar='SUBNET',
        help='List of subnets to add to the packet mirroring.',
    )
    subnets.add_argument(
        '--remove-mirrored-subnets',
        type=arg_parsers.ArgList(),
        metavar='SUBNET',
        help='List of subnets to remove from the packet mirroring.'
    )
    subnets.add_argument(
        '--set-mirrored-subnets',
        type=arg_parsers.ArgList(),
        metavar='SUBNET',
        help='List of subnets to be mirrored on the packet mirroring.'
    )
    subnets.add_argument(
        '--clear-mirrored-subnets',
        action='store_true',
        default=None,
        help=('If specified, clear the existing subnets '
              'from the packet mirroring.'))
  else:
    parser.add_argument(
        '--mirrored-subnets',
        type=arg_parsers.ArgList(),
        metavar='SUBNET',
        help="""\
        List of subnets to be mirrored.
        You can provide this as the full URL to the subnet, partial URL, or
        name.
        For example, the following are valid values:
          * https://compute.googleapis.com/compute/v1/projects/myproject/
            regions/us-central1/subnetworks/subnet-1
          * projects/myproject/regions/us-central1/subnetworks/subnet-1
          * subnet-1
        """)


def _AddMirroredTagsArg(parser, is_for_update=False):
  """Adds args to specify mirrored tags."""
  if is_for_update:
    tags = parser.add_mutually_exclusive_group(help="""\
      Update the mirrored tags of this packet mirroring.

      To read more about configuring network tags, read this guide:
      https://cloud.google.com/vpc/docs/add-remove-network-tags

      The virtual machines with the provided tags must live
      in zones contained in the same region as this packet mirroring.
      """)
    tags.add_argument(
        '--add-mirrored-tags',
        type=arg_parsers.ArgList(),
        metavar='TAG',
        help='List of tags to add to the packet mirroring.',
    )
    tags.add_argument(
        '--remove-mirrored-tags',
        type=arg_parsers.ArgList(),
        metavar='TAG',
        help='List of tags to remove from the packet mirroring.'
    )
    tags.add_argument(
        '--set-mirrored-tags',
        type=arg_parsers.ArgList(),
        metavar='TAG',
        help='List of tags to be mirrored on the packet mirroring.'
    )
    tags.add_argument(
        '--clear-mirrored-tags', action='store_true', default=None,
        help='If specified, clear the existing tags from the packet mirroring.')
  else:
    parser.add_argument(
        '--mirrored-tags',
        type=arg_parsers.ArgList(),
        metavar='TAG',
        help="""\
        List of virtual machine instance tags to be mirrored.

        To read more about configuring network tags, read this guide:
        https://cloud.google.com/vpc/docs/add-remove-network-tags

        The virtual machines with the provided tags must live
        in zones contained in the same region as this packet mirroring.
        """)


def _AddFilterCidrRangesArg(parser, is_for_update=False):
  """Adds args to specify filter CIDR ranges."""
  if is_for_update:
    cidr_ranges = parser.add_mutually_exclusive_group(
        help='Update the filter CIDR ranges of this packet mirroring.')
    cidr_ranges.add_argument(
        '--add-filter-cidr-ranges',
        type=arg_parsers.ArgList(),
        metavar='CIDR_RANGE',
        help='List of filter CIDR ranges to add to the packet mirroring.'
    )
    cidr_ranges.add_argument(
        '--remove-filter-cidr-ranges',
        type=arg_parsers.ArgList(),
        metavar='CIDR_RANGE',
        help='List of filter CIDR ranges to remove from the packet mirroring.'
    )
    cidr_ranges.add_argument(
        '--set-filter-cidr-ranges',
        type=arg_parsers.ArgList(),
        metavar='CIDR_RANGE',
        help="""\
        List of filter CIDR ranges to be mirrored on the packet mirroring.
        """)
    cidr_ranges.add_argument(
        '--clear-filter-cidr-ranges',
        action='store_true',
        default=None,
        help="""\
        If specified, clear the existing filter CIDR ranges from the packet
        mirroring.
        """
    )
  else:
    parser.add_argument(
        '--filter-cidr-ranges',
        type=arg_parsers.ArgList(),
        metavar='CIDR_RANGE',
        help="""\
        List of IP CIDR ranges that apply as filters on the source or
        destination IP in the IP header for packet mirroring traffic. All
        traffic between the VM and the IPs listed here will be mirrored using
        this configuration. This can be a Public IP as well.
        If unspecified, the config applies to all traffic.
        """
    )


def _AddFilterProtocolsArg(parser, is_for_update=False):
  """Adds args to specify filter IP protocols."""
  if is_for_update:
    protocols = parser.add_mutually_exclusive_group(
        help='Update the filter protocols of this packet mirroring.')
    protocols.add_argument(
        '--add-filter-protocols',
        type=arg_parsers.ArgList(element_type=str),
        metavar='PROTOCOL',
        help="""\
        List of filter IP protocols to add to the packet mirroring.
        PROTOCOL can be one of tcp, udp, icmp, esp, ah, ipip, sctp, or an IANA
        protocol number.
        """)
    protocols.add_argument(
        '--remove-filter-protocols',
        type=arg_parsers.ArgList(element_type=str),
        metavar='PROTOCOL',
        help="""\
        List of filter IP protocols to remove from the packet mirroring.
        PROTOCOL can be one of tcp, udp, icmp, esp, ah, ipip, sctp, or an IANA
        protocol number.
        """)
    protocols.add_argument(
        '--set-filter-protocols',
        type=arg_parsers.ArgList(element_type=str),
        metavar='PROTOCOL',
        help="""\
        List of filter IP protocols to be mirrored on the packet mirroring.
        PROTOCOL can be one of tcp, udp, icmp, esp, ah, ipip, sctp, or an IANA
        protocol number.
        """)
    protocols.add_argument(
        '--clear-filter-protocols',
        action='store_true',
        default=None,
        help="""\
        If specified, clear the existing filter IP protocols from the packet
        mirroring.
        """)
  else:
    parser.add_argument(
        '--filter-protocols',
        type=arg_parsers.ArgList(element_type=str),
        metavar='PROTOCOL',
        help="""\
        List of IP protocols that apply as filters for packet mirroring traffic.
        If unspecified, the packet mirroring applies to all traffic.
        PROTOCOL can be one of tcp, udp, icmp, esp, ah, ipip, sctp, or an IANA
        protocol number.
        """,
    )


def _AddFilterDirectionArg(parser):
  """Adds args to specify filter direction."""
  parser.add_argument(
      '--filter-direction',
      choices=['both', 'egress', 'ingress'],
      metavar='DIRECTION',
      help="""\
        - For `ingress`, only ingress traffic is mirrored.
        - For `egress`, only egress traffic is mirrored.
        - For `both` (default), both directions are mirrored.
        """,
  )

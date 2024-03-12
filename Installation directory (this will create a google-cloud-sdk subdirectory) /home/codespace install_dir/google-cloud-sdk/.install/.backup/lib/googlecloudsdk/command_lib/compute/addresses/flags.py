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
"""Flags and helpers for the compute addresses commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util import completers


class RegionalAddressesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(RegionalAddressesCompleter, self).__init__(
        collection='compute.addresses',
        list_command='compute addresses list --filter=region:* --uri',
        **kwargs)


class GlobalAddressesCompleter(compute_completers.GlobalListCommandCompleter):

  def __init__(self, **kwargs):
    super(GlobalAddressesCompleter, self).__init__(
        collection='compute.globalAddresses',
        list_command='alpha compute addresses list --global --uri',
        **kwargs)


class AddressesCompleter(completers.MultiResourceCompleter):

  def __init__(self, **kwargs):
    super(AddressesCompleter, self).__init__(
        completers=[RegionalAddressesCompleter, GlobalAddressesCompleter],
        **kwargs)


def AddressArgument(required=True, plural=True):
  return compute_flags.ResourceArgument(
      resource_name='address',
      completer=AddressesCompleter,
      plural=plural,
      custom_plural='addresses',
      required=required,
      regional_collection='compute.addresses',
      global_collection='compute.globalAddresses')


def SubnetworkArgument():
  return compute_flags.ResourceArgument(
      name='--subnet',
      resource_name='subnet',
      required=False,
      regional_collection='compute.subnetworks',
      region_hidden=True,
      short_help='The subnet in which to reserve the addresses.',
      detailed_help="""\
      If specified, the subnet name in which the address(es) should be reserved.
      The subnet must be in the same region as the address.

      The address will represent an internal IP reservation from within the
      subnet. If --address is specified, it must be within the subnet's
      IP range.

      May not be specified with --global.
      """)


def NetworkArgument():
  return compute_flags.ResourceArgument(
      name='--network',
      resource_name='network',
      required=False,
      global_collection='compute.networks',
      short_help='The network in which to reserve the addresses.',
      detailed_help="""\
      If specified, the network resource in which the address(es) should be
      reserved.

      This is only available for global internal address, which represents
      an internal IP range reservation from within the network.
      """)


def AddAddresses(parser):
  """Adds the Addresses flag."""
  parser.add_argument(
      '--addresses',
      metavar='ADDRESS',
      type=arg_parsers.ArgList(min_length=1),
      help="""\
      Ephemeral IP addresses to promote to reserved status. Only addresses
      that are being used by resources in the project can be promoted. When
      providing this flag, a parallel list of names for the addresses can
      be provided. For example,

          $ {command} ADDRESS-1 ADDRESS-2 \
            --addresses 162.222.181.197,162.222.181.198 \
            --region us-central1

      will result in 162.222.181.197 being reserved as
      'ADDRESS-1' and 162.222.181.198 as 'ADDRESS-2'. If
      no names are given, server-generated names will be assigned
      to the IP addresses.
      """)


def AddPrefixLength(parser):
  """Adds the prefix-length flag."""
  parser.add_argument(
      '--prefix-length',
      type=arg_parsers.BoundedInt(lower_bound=8, upper_bound=96),
      help="""\
      The prefix length of the IP range. If the address is an IPv4 address, it
      must be a value between 8 and 30 inclusive. If the address is an IPv6
      address, the only allowed value is 96. If not present, it means the
      address field is a single IP address.

      This field is not applicable to external IPv4 addresses or global IPv6
      addresses.
      """)


def AddIpVersionGroup(parser):
  """Adds IP versions flag in a mutually exclusive group."""
  parser.add_argument(
      '--ip-version',
      choices=['IPV4', 'IPV6'],
      type=lambda x: x.upper(),
      help="""\
      Version of the IP address to be allocated and reserved.
      The default is IPV4.

      IP version can only be specified for global addresses that are generated
      automatically (i.e., along with
      the `--global` flag, given `--addresses` is not specified) and if the
      `--network-tier` is `PREMIUM`.
      """)


def AddAddressesAndIPVersions(parser, required=True):
  """Adds Addresses and IP versions flag."""
  group = parser.add_mutually_exclusive_group(required=required)
  AddIpVersionGroup(group)
  AddAddresses(group)


def AddDescription(parser):
  """Adds the Description flag."""
  parser.add_argument(
      '--description',
      help='An optional textual description for the addresses.')


def AddNetworkTier(parser):
  """Adds network tier flag."""
  # This arg is a string simulating enum NetworkTier because one of the
  # option SELECT is hidden since it's not advertised to all customers.
  parser.add_argument(
      '--network-tier',
      type=lambda x: x.upper(),
      help="""\
      The network tier to assign to the reserved IP addresses. ``NETWORK_TIER''
      must be one of: `PREMIUM`, `STANDARD`, `FIXED_STANDARD`.
      The default value is `PREMIUM`.

      While regional external addresses (`--region` specified, `--subnet`
      omitted) can use either `PREMIUM` or `STANDARD`, global external
      addresses (`--global` specified, `--subnet` omitted) can only use
      `PREMIUM`. Internal addresses can only use `PREMIUM`.
      """)


def AddIPv6EndPointType(parser):
  """Adds IPv6 EndPoint flag."""
  choices = ['VM', 'NETLB']
  parser.add_argument(
      '--endpoint-type',
      choices=choices,
      type=lambda x: x.upper(),
      help="""\
        The endpoint type of the external IPv6 address to be reserved.
      """)


def AddPurpose(parser, support_psc_google_apis):
  """Adds purpose flag."""
  choices = [
      'VPC_PEERING', 'SHARED_LOADBALANCER_VIP', 'GCE_ENDPOINT',
      'IPSEC_INTERCONNECT'
  ]
  if support_psc_google_apis:
    choices.append('PRIVATE_SERVICE_CONNECT')
  parser.add_argument(
      '--purpose',
      choices=choices,
      type=lambda x: x.upper(),
      help="""\
      The purpose of the address resource. This field is not applicable to
      external addresses.
      """)


def AddMoveArguments(parser):
  """Add flags for move."""
  parser.add_argument(
      '--target-project',
      required=True,
      help='The target project to move address to. It can be either a project '
      'name or a project numerical ID. It must not be the same as the current '
      'project.')
  parser.add_argument(
      '--new-name',
      help='Name of moved new address. If not specified, current '
      'address\'s name is used.')
  parser.add_argument('--description', help='Description of moved new address.')

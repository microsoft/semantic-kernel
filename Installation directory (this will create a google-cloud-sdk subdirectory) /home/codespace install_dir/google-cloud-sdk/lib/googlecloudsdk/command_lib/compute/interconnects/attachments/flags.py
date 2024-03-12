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
"""Flags and helpers for the compute interconnects commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util.apis import arg_utils

_BANDWIDTH_CHOICES = collections.OrderedDict([
    ('50m', '50 Mbit/s'),
    ('100m', '100 Mbit/s'),
    ('200m', '200 Mbit/s'),
    ('300m', '300 Mbit/s'),
    ('400m', '400 Mbit/s'),
    ('500m', '500 Mbit/s'),
    ('1g', '1 Gbit/s'),
    ('2g', '2 Gbit/s'),
    ('5g', '5 Gbit/s'),
    ('10g', '10 Gbit/s'),
    ('20g', '20 Gbit/s'),
    ('50g', '50 Gbit/s'),
])

_EDGE_AVAILABILITY_DOMAIN_CHOICES = {
    'availability-domain-1': 'Edge Availability Domain 1',
    'availability-domain-2': 'Edge Availability Domain 2',
    'any': 'Any Availability Domain',
}

_ENCRYPTION_CHOICES = ('IPSEC', 'NONE')


class InterconnectAttachmentsCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InterconnectAttachmentsCompleter, self).__init__(
        collection='compute.interconnectAttachments',
        list_command='alpha compute interconnects attachments list --uri',
        **kwargs
    )


def InterconnectAttachmentArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='interconnect attachment',
      completer=InterconnectAttachmentsCompleter,
      plural=plural,
      required=required,
      regional_collection='compute.interconnectAttachments',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def InterconnectAttachmentArgumentForRouter(required=False,
                                            plural=False,
                                            operation_type='added'):
  resource_name = 'interconnectAttachment{0}'.format('s' if plural else '')
  return compute_flags.ResourceArgument(
      resource_name=resource_name,
      name='--interconnect-attachment',
      completer=InterconnectAttachmentsCompleter,
      plural=plural,
      required=required,
      regional_collection='compute.interconnectAttachments',
      short_help='The interconnect attachment of the interface being {0}.'
      .format(operation_type),
      region_explanation='If not specified it will be set to the region of '
      'the router.')


def AddAdminEnabled(parser, default_behavior=True, update=False):
  """Adds adminEnabled flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
    default_behavior: A boolean indicates whether command allows user to set
      Administrative status.
    update: A boolean indicates whether the incoming request is update.
  """
  group = parser.add_group(mutex=True, required=False, help='')
  if update:
    # Update command
    help_text = """\
      Administrative status of the interconnect attachment.
      When this is enabled, the attachment is operational and will carry
      traffic. Use --no-enable-admin to disable it.
      """
  elif default_behavior:
    # Create command for dedicated attachments, backend default behavior is to
    # enable if not specified.
    help_text = """\
      Administrative status of the interconnect attachment. If not provided
      on creation, defaults to enabled.
      When this is enabled, the attachment is operational and will carry
      traffic. Use --no-enable-admin to disable it.
      """
  else:
    # Create command for partner attachments, backend default behavior is to
    # disabled if not specified.
    help_text = """\
      Administrative status of the interconnect attachment. If not provided
      on creation, defaults to disabled.
      When this is enabled, the attachment is operational and will carry
      traffic. Use --no-enable-admin to disable it.
      """

  group.add_argument(
      '--admin-enabled',
      hidden=True,
      default=None,
      action='store_true',
      help='(DEPRECATED) Use --enable-admin instead.')

  group.add_argument(
      '--enable-admin', action='store_true', default=None, help=help_text)


def AddBandwidth(parser, required):
  """Adds bandwidth flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
    required: A boolean indicates whether the Bandwidth is required.
  """
  help_text = """\
      Provisioned capacity of the attachment.
      """
  choices = _BANDWIDTH_CHOICES

  base.ChoiceArgument(
      '--bandwidth',
      # TODO(b/80311900): use arg_parsers.BinarySize()
      choices=choices,
      required=required,
      help_str=help_text).AddToParser(parser)


def AddVlan(parser):
  """Adds vlan flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--vlan',
      type=int,
      help="""\
      Desired VLAN for this attachment, in the range 2-4093. If not supplied,
      Google will automatically select a VLAN.
      """)


def AddPartnerAsn(parser):
  """Adds partner asn flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--partner-asn',
      type=int,
      help="""\
      BGP ASN of the partner. This should only be supplied by layer 3
      providers that have configured BGP on behalf of the customer.
      """)


def AddPartnerMetadata(parser, required=True):
  """Adds partner metadata flags to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
    required: A boolean indicates whether the PartnerMetadata is required.
  """
  group = parser.add_group(
      mutex=False, required=required, help='Partner metadata.')
  group.add_argument(
      '--partner-name',
      required=required,
      help="""\
      Plain text name of the Partner providing this attachment. This value
      may be validated to match approved Partner values.
      """)
  group.add_argument(
      '--partner-interconnect-name',
      required=required,
      help="""\
      Plain text name of the Interconnect this attachment is connected to,
      as displayed in the Partner's portal. For instance "Chicago 1".
      """)
  group.add_argument(
      '--partner-portal-url',
      required=required,
      help="""\
      URL of the Partner's portal for this Attachment. The Partner may wish
      to customize this to be a deep-link to the specific resource on the
      Partner portal. This value may be validated to match approved Partner
      values.
      """)


def AddPairingKey(parser):
  """Adds pairing key flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--pairing-key',
      required=True,
      help="""\
      Value of the pairing-key from the target partner attachment provided by
      the customer.
      """)


def AddEdgeAvailabilityDomain(parser):
  """Adds edge-availability-domain flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--edge-availability-domain',
      choices=_EDGE_AVAILABILITY_DOMAIN_CHOICES,
      required=True,
      metavar='AVAILABILITY_DOMAIN',
      help="""\
      Desired edge availability domain for this attachment:
      `availability-domain-1`, `availability-domain-2`, `any`.

      In each metro where the Partner can connect to Google, there are two sets
      of redundant hardware. These sets are described as edge availability
      domain 1 and 2. Within a metro, Google will only schedule maintenance in
      one availability domain at a time. This guarantee does not apply to
      availability domains outside the metro; Google may perform maintenance in
      (say) New York availability domain 1 at the same time as Chicago
      availability domain 1.
      """)


def AddDescription(parser):
  """Adds description flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--description',
      help='Human-readable plain-text description of attachment.')


def AddCandidateSubnets(parser):
  """Adds candidate subnets flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--candidate-subnets',
      type=arg_parsers.ArgList(max_length=16),
      metavar='SUBNET',
      help="""\
      Up to 16 candidate prefixes that can be used to restrict the allocation of
      `cloudRouterIpAddress` and `customerRouterIpAddress` for this
      attachment. All prefixes must be within link-local address space.
      Google attempts to select an unused subnet of SUBNET_LENGTH from the
      supplied candidate subnet(s), or all of link-local space if no subnets
      supplied. Google does not re-use a subnet already in-use by your project,
      even if it's contained in one of the candidate subnets. The request fails
      if all candidate subnets are in use at Google's edge.""",
      default=[],
  )


def AddDryRun(parser):
  """Adds dry-run flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--dry-run',
      default=None,
      action='store_true',
      help='If supplied, validates the attachment without creating it.')


def AddMtu(parser):
  """Adds mtu flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--mtu',
      type=int,
      help="""\
      Maximum transmission unit (MTU) is the size of the largest IP packet
      passing through this interconnect attachment. Only 1440 and 1500 are
      allowed values. If not specified, the value will default to 1440.
      """)


def AddEncryption(parser):
  """Adds encryption flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--encryption',
      required=False,
      choices=_ENCRYPTION_CHOICES,
      help="""\
      Indicates the user-supplied encryption option for this interconnect
      attachment (VLAN attachment).

      Possible values are:

      `NONE` - This is the default value, which means the interconnect attachment
      carries unencrypted traffic. VMs can send traffic to or
      receive traffic from such interconnect attachment.

      `IPSEC` - The interconnect attachment carries only traffic that is encrypted
      by an IPsec device; for example, an HA VPN gateway or third-party
      IPsec VPN. VMs cannot directly send traffic to or receive traffic from such
      an interconnect attachment. To use HA VPN over Cloud Interconnect,
      the interconnect attachment must be created with this option.

      """)


def GetAdminEnabledFlag(args):
  """Determines value of admin_enabled/enable_admin flag.

  Args:
    args: A list of arguments to be parsed.

  Returns:
    A boolean indicates whether admin mode is enabled in Arguments.
  """
  return args.enable_admin if args.enable_admin is not None else args.admin_enabled


def GetIpsecInternalAddressesFlag():
  """Adds ipsec-internal-addresses flag to the argparse.ArgumentParser."""
  return base.Argument(
      '--ipsec-internal-addresses',
      required=False,
      type=arg_parsers.ArgList(max_length=1),
      metavar='ADDRESSES',
      help="""\
      List of IP address range names that have been reserved for the interconnect
      attachment (VLAN attachment). Use this option only for an interconnect
      attachment that has its encryption option set as IPSEC. Currently only one
      internal IP address range can be specified for each attachment.
      When creating an HA VPN gateway for the interconnect attachment, if the
      attachment is configured to use a regional internal IP address, then the VPN
      gateway's IP address is allocated from the IP address range specified here.
      If this field is not specified when creating the interconnect attachment,
      then when creating any HA VPN gateways for this interconnect attachment,
      the HA VPN gateway's IP address is allocated from a regional external IP
      address pool.
      """)


def GetAddressRef(resources, name, region, project):
  """Generates an address reference from the specified name, region and project."""
  return resources.Parse(
      name,
      collection='compute.addresses',
      params={
          'project': project,
          'region': region
      })


def AddStackType(parser):
  """Adds stack-type flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--stack-type',
      choices={
          'IPV4_ONLY':
              'Only IPv4 protocol is enabled on this attachment.',
          'IPV4_IPV6':
              'Both IPv4 and IPv6 protocols are enabled on this attachment.',
      },
      type=arg_utils.ChoiceToEnumName,
      help=('The stack type of the protocol(s) enabled on this interconnect '
            'attachment.'))


def AddCandidateIpv6Subnets(parser):
  """Adds candidate ipv6 subnets flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--candidate-ipv6-subnets',
      type=arg_parsers.ArgList(max_length=16),
      metavar='IPV6_SUBNET',
      help="""The `candididate-ipv6-subnets` field is not available.""",
      default=[])


def AddCloudRouterIpv6InterfaceId(parser):
  """Adds cloud router ipv6 interface id flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--cloud-router-ipv6-interface-id',
      metavar='INTERFACE_ID',
      help="""The `cloud-router-ipv6-interface-id` field is not available.""")


def AddCustomerRouterIpv6InterfaceId(parser):
  """Adds customer router ipv6 interface id flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--customer-router-ipv6-interface-id',
      metavar='PEER_INTERFACE_ID',
      help="""The `customer-router-ipv6-interface-id` field is not available.""")


def AddSubnetLength(parser):
  """Adds subnet length flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
  """
  parser.add_argument(
      '--subnet-length',
      metavar='SUBNET_LENGTH',
      type=int,
      choices=frozenset({29, 30}),
      help="""\
      The length of the IPv4 subnet mask for this attachment. 29 is the
      default value, except for attachments on Cross-Cloud Interconnects whose
      remote location's "constraints.subnetLengthRange" field specifies a
      minimum subnet length of 30. In that case, the default value is 30.
      The default value is recommended when there's no requirement on the subnet
      length.
      """)


def AddEnableMulticast(parser, update=False):
  """Adds enableMulticast flag to the argparse.ArgumentParser.

  Args:
    parser: The argparse parser.
    update: A boolean indicates whether the incoming request is an update.
  """
  if update:
    # Update command.
    help_text = """\
      When enabled, the attachment will be able to carry multicast traffic.
      Use --no-enable-multicast to disable it.
      """
  else:
    # Create command for partner attachments, backend default behavior is to
    # disabled if not specified.
    help_text = """\
      If supplied, the attachment will be able to carry multicast traffic.
      If not provided on creation, defaults to disabled. Use
      --no-enable-multicast to disable it.
      """
  parser.add_argument(
      '--enable-multicast',
      default=None,
      action='store_true',
      help=help_text,
  )

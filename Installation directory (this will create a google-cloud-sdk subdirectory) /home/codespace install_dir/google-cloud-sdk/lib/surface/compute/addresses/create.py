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
"""Command for reserving IP addresses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import constants
from googlecloudsdk.api_lib.compute import name_generator
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.addresses import flags
import ipaddr
from six.moves import zip  # pylint: disable=redefined-builtin


def _Args(cls, parser, support_psc_google_apis):
  """Argument parsing."""

  cls.ADDRESSES_ARG = flags.AddressArgument(required=False)
  cls.ADDRESSES_ARG.AddArgument(parser, operation_type='create')
  flags.AddDescription(parser)
  parser.display_info.AddCacheUpdater(flags.AddressesCompleter)

  flags.AddAddressesAndIPVersions(parser, required=False)
  flags.AddNetworkTier(parser)
  flags.AddPrefixLength(parser)
  flags.AddPurpose(parser, support_psc_google_apis)
  flags.AddIPv6EndPointType(parser)

  cls.SUBNETWORK_ARG = flags.SubnetworkArgument()
  cls.SUBNETWORK_ARG.AddArgument(parser)

  cls.NETWORK_ARG = flags.NetworkArgument()
  cls.NETWORK_ARG.AddArgument(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  r"""Reserve IP addresses.

  *{command}* is used to reserve one or more IP addresses. Once an IP address
  is reserved, it will be associated with the project until it is released
  using 'gcloud compute addresses delete'. Ephemeral IP addresses that are in
  use by resources in the project can be reserved using the '--addresses' flag.

  ## EXAMPLES
  To reserve three IP addresses in the 'us-central1' region, run:

    $ {command} address-1 address-2 address-3 --region=us-central1

  To reserve ephemeral IP addresses '162.222.181.198' and '23.251.146.189' which
  are being used by virtual machine instances in the 'us-central1' region, run:

    $ {command} --addresses=162.222.181.198,23.251.146.189 --region=us-central1

  In the above invocation, the two addresses will be assigned random names.

  To reserve an IP address named subnet-address-1 from the subnet 'default' in
  the 'us-central1' region, run:

    $ {command} subnet-address-1 \
      --region=us-central1 \
      --subnet=default

  To reserve an IP range '10.110.0.0/16' from the network 'default' for
  'VPC_PEERING', run:

    $ {command} ip-range-1 --global --addresses=10.110.0.0 --prefix-length=16 \
      --purpose=VPC_PEERING --network=default

  To reserve any IP range with prefix length '16' from the network 'default' for
  'VPC_PEERING', run:

    $ {command} ip-range-1 --global --prefix-length=16 --purpose=VPC_PEERING \
      --network=default

  To reserve an address from network 'default' for PRIVATE_SERVICE_CONNECT, run:

    $ {command} psc-address-1 --global --addresses=10.110.0.10 \
      --purpose=PRIVATE_SERVICE_CONNECT --network=default

  """

  ADDRESSES_ARG = None
  SUBNETWORK_ARG = None
  NETWORK_ARG = None

  _support_psc_google_apis = True

  @classmethod
  def Args(cls, parser):
    _Args(
        cls,
        parser,
        support_psc_google_apis=cls._support_psc_google_apis)

  def ConstructNetworkTier(self, messages, args):
    if args.network_tier:
      network_tier = args.network_tier.upper()
      if network_tier in constants.NETWORK_TIER_CHOICES_FOR_INSTANCE:
        return messages.Address.NetworkTierValueValuesEnum(args.network_tier)
      else:
        raise exceptions.InvalidArgumentException(
            '--network-tier',
            'Invalid network tier [{tier}]'.format(tier=network_tier))
    else:
      return None

  def Run(self, args):
    """Issues requests necessary to create Addresses."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    names, addresses = self._GetNamesAndAddresses(args)
    if not args.name:
      args.name = names

    address_refs = self.ADDRESSES_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    requests = []
    for address, address_ref in zip(addresses, address_refs):
      address_msg = self.GetAddress(client.messages, args, address, address_ref,
                                    holder.resources)

      if address_ref.Collection() == 'compute.globalAddresses':
        requests.append((client.apitools_client.globalAddresses, 'Insert',
                         client.messages.ComputeGlobalAddressesInsertRequest(
                             address=address_msg, project=address_ref.project)))
      elif address_ref.Collection() == 'compute.addresses':
        requests.append((client.apitools_client.addresses, 'Insert',
                         client.messages.ComputeAddressesInsertRequest(
                             address=address_msg,
                             region=address_ref.region,
                             project=address_ref.project)))

    return client.MakeRequests(requests)

  def _GetNamesAndAddresses(self, args):
    """Returns names and addresses provided in args."""
    if not args.addresses and not args.name:
      raise exceptions.MinimumArgumentException(
          ['NAME', '--address'],
          'At least one name or address must be provided.')

    if args.name:
      names = args.name
    else:
      # If we dont have any names then we must some addresses.
      names = [name_generator.GenerateRandomName() for _ in args.addresses]

    if args.addresses:
      addresses = args.addresses
    else:
      # If we dont have any addresses then we must some names.
      addresses = [None] * len(args.name)

    if len(addresses) != len(names):
      raise exceptions.BadArgumentException(
          '--addresses',
          'If providing both, you must specify the same number of names as '
          'addresses.')

    return names, addresses

  def CheckPurposeInSubnetwork(self, messages, purpose):
    if (purpose != messages.Address.PurposeValueValuesEnum.GCE_ENDPOINT and
        purpose !=
        messages.Address.PurposeValueValuesEnum.SHARED_LOADBALANCER_VIP):
      raise exceptions.InvalidArgumentException(
          '--purpose',
          'must be GCE_ENDPOINT or SHARED_LOADBALANCER_VIP for regional '
          'internal addresses.')

  # TODO(b/266237285): Need to remove exceptions and break down function.
  def GetAddress(self, messages, args, address, address_ref, resource_parser):
    """Get and validate address setting.

    Retrieve address resource from input arguments and validate the address
    configuration for both external/internal IP address reservation/promotion.

    Args:
      messages: The client message proto includes all required GCE API fields.
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
      address: Address object.
      address_ref: Reference of the address.
      resource_parser: A resource parser used to parse resource name into url.

    Returns:
      An address resource proto message.

    Raises:
      ConflictingArgumentsException: If both network and subnetwork fields are
      set.
      MinimumArgumentException: Missing network or subnetwork with purpose
      field.
      InvalidArgumentException: The input argument is not set correctly or
      unable to be parsed.
      RequiredArgumentException: The required argument is missing from user
      input.
    """
    network_tier = self.ConstructNetworkTier(messages, args)

    if args.ip_version or (address is None and address_ref.Collection()
                           == 'compute.globalAddresses'):
      ip_version = messages.Address.IpVersionValueValuesEnum(args.ip_version or
                                                             'IPV4')
    else:
      # IP version is only specified in global and regional external Ipv6
      # requests if an address is not specified to determine whether an ipv4 or
      # ipv6 address should be allocated.
      ip_version = None

    if args.subnet and args.network:
      raise exceptions.ConflictingArgumentsException('--network', '--subnet')

    purpose = None
    if args.purpose and not args.network and not args.subnet:
      raise exceptions.MinimumArgumentException(['--network', '--subnet'],
                                                ' if --purpose is specified')

    # TODO(b/36862747): get rid of args.subnet check
    if args.subnet:
      if address_ref.Collection() == 'compute.globalAddresses':
        raise exceptions.BadArgumentException(
            '--subnet', '[--subnet] may not be specified for global addresses.')
      if not args.subnet_region:
        args.subnet_region = address_ref.region
      subnetwork_url = flags.SubnetworkArgument().ResolveAsResource(
          args, resource_parser).SelfLink()
      if not args.endpoint_type:
        # External IPv6 reservation does not need purpose field.
        purpose = messages.Address.PurposeValueValuesEnum(args.purpose or
                                                          'GCE_ENDPOINT')
        self.CheckPurposeInSubnetwork(messages, purpose)
    else:
      subnetwork_url = None

    network_url = None
    if args.network:
      purpose = messages.Address.PurposeValueValuesEnum(args.purpose or
                                                        'VPC_PEERING')
      network_url = flags.NetworkArgument().ResolveAsResource(
          args, resource_parser).SelfLink()
      if purpose != messages.Address.PurposeValueValuesEnum.IPSEC_INTERCONNECT:
        if address_ref.Collection() == 'compute.addresses':
          raise exceptions.InvalidArgumentException(
              '--network',
              'network may not be specified for regional addresses.')
        supported_purposes = {
            'VPC_PEERING': messages.Address.PurposeValueValuesEnum.VPC_PEERING
        }
        if self._support_psc_google_apis:
          supported_purposes['PRIVATE_SERVICE_CONNECT'] = (
              messages.Address.PurposeValueValuesEnum.PRIVATE_SERVICE_CONNECT
          )

        if purpose not in supported_purposes.values():
          raise exceptions.InvalidArgumentException(
              '--purpose', 'must be {} for '
              'global internal addresses.'.format(' or '.join(
                  supported_purposes.keys())))

    ipv6_endpoint_type = None
    if args.endpoint_type:
      ipv6_endpoint_type = messages.Address.Ipv6EndpointTypeValueValuesEnum(
          args.endpoint_type)

    address_type = None
    if args.endpoint_type:
      address_type = messages.Address.AddressTypeValueValuesEnum.EXTERNAL
    elif subnetwork_url or network_url:
      address_type = messages.Address.AddressTypeValueValuesEnum.INTERNAL

    if address is not None:
      try:
        ip_address = ipaddr.IPAddress(address)
      except ValueError:
        raise exceptions.InvalidArgumentException(
            '--addresses', 'Invalid IP address {e}'.format(e=address)
        )

    if args.prefix_length:
      if address and not address_type:
        # This is address promotion.
        address_type = messages.Address.AddressTypeValueValuesEnum.EXTERNAL
      elif (
          (address is None or ip_address.version != 6)
          and purpose != messages.Address.PurposeValueValuesEnum.VPC_PEERING
          and purpose
          != messages.Address.PurposeValueValuesEnum.IPSEC_INTERCONNECT
      ):
        raise exceptions.InvalidArgumentException(
            '--prefix-length',
            'can only be used with [--purpose VPC_PEERING/IPSEC_INTERCONNECT]'
            ' or Internal/External IPv6 reservation. Found {e}'.format(
                e=purpose
            ),
        )

    if not args.prefix_length:
      if purpose == messages.Address.PurposeValueValuesEnum.VPC_PEERING:
        raise exceptions.RequiredArgumentException(
            '--prefix-length',
            'prefix length is needed for reserving VPC peering IP ranges.')
      if purpose == messages.Address.PurposeValueValuesEnum.IPSEC_INTERCONNECT:
        raise exceptions.RequiredArgumentException(
            '--prefix-length', 'prefix length is needed for reserving IP ranges'
            ' for HA VPN over Cloud Interconnect.')

    return messages.Address(
        address=address,
        prefixLength=args.prefix_length,
        description=args.description,
        networkTier=network_tier,
        ipVersion=ip_version,
        name=address_ref.Name(),
        addressType=address_type,
        purpose=purpose,
        subnetwork=subnetwork_url,
        network=network_url,
        ipv6EndpointType=ipv6_endpoint_type)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(Create):
  # pylint: disable=line-too-long
  r"""Reserve IP addresses.

  *{command}* is used to reserve one or more IP addresses. Once an IP address
  is reserved, it will be associated with the project until it is released
  using 'gcloud compute addresses delete'. Ephemeral IP addresses that are in
  use by resources in the project can be reserved using the '--addresses' flag.

  ## EXAMPLES
  To reserve three IP addresses in the 'us-central1' region, run:

    $ {command} address-1 address-2 address-3 --region=us-central1

  To reserve ephemeral IP addresses '162.222.181.198' and '23.251.146.189' which
  are being used by virtual machine instances in the 'us-central1' region, run:

    $ {command} --addresses=162.222.181.198,23.251.146.189 --region=us-central1

  In the above invocation, the two addresses will be assigned random names.

  To reserve an IP address named subnet-address-1 from the subnet 'default' in
  the 'us-central1' region, run:

    $ {command} subnet-address-1 --region=us-central1 --subnet=default

  To reserve an IP address that can be used by multiple internal load balancers
  from the subnet 'default' in the 'us-central1' region, run:

    $ {command} shared-address-1 --region=us-central1 --subnet=default \
      --purpose=SHARED_LOADBALANCER_VIP

  To reserve an IP range '10.110.0.0/16' from the network 'default' for
  'VPC_PEERING', run:

    $ {command} ip-range-1 --global --addresses=10.110.0.0 --prefix-length=16 \
      --purpose=VPC_PEERING --network=default

  To reserve any IP range with prefix length '16' from the network 'default' for
  'VPC_PEERING', run:

    $ {command} ip-range-1 --global --prefix-length=16 --purpose=VPC_PEERING \
      --network=default

  To reserve an address from network 'default' for PRIVATE_SERVICE_CONNECT, run:

    $ {command} psc-address-1 --global --addresses=10.110.0.10 \
      --purpose=PRIVATE_SERVICE_CONNECT --network=default

  """

  _support_psc_google_apis = True


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  # pylint: disable=line-too-long
  r"""Reserve IP addresses.

  *{command}* is used to reserve one or more IP addresses. Once an IP address
  is reserved, it will be associated with the project until it is released
  using 'gcloud compute addresses delete'. Ephemeral IP addresses that are in
  use by resources in the project can be reserved using the '--addresses' flag.

  ## EXAMPLES
  To reserve three IP addresses in the 'us-central1' region, run:

    $ {command} address-1 address-2 address-3 --region=us-central1

  To reserve ephemeral IP addresses '162.222.181.198' and '23.251.146.189' which
  are being used by virtual machine instances in the 'us-central1' region, run:

    $ {command} --addresses=162.222.181.198,23.251.146.189 --region=us-central1

  In the above invocation, the two addresses will be assigned random names.

  To reserve an IP address named subnet-address-1 from the subnet 'default' in
  the 'us-central1' region, run:

    $ {command} subnet-address-1 --region=us-central1 --subnet=default

  To reserve an IP address that can be used by multiple internal load balancers
  from the subnet 'default' in the 'us-central1' region, run:

    $ {command} shared-address-1 --region=us-central1 --subnet=default \
      --purpose=SHARED_LOADBALANCER_VIP

  To reserve an IP range '10.110.0.0/16' from the network 'default' for
  'VPC_PEERING', run:

    $ {command} ip-range-1 --global --addresses=10.110.0.0 --prefix-length=16 \
      --purpose=VPC_PEERING --network=default

  To reserve any IP range with prefix length '16' from the network 'default' for
  'VPC_PEERING', run:

    $ {command} ip-range-1 --global --prefix-length=16 --purpose=VPC_PEERING \
      --network=default

  To reserve an address from network 'default' for PRIVATE_SERVICE_CONNECT, run:

    $ {command} psc-address-1 --global --addresses=10.110.0.10 \
      --purpose=PRIVATE_SERVICE_CONNECT --network=default
  """

  _support_psc_google_apis = True

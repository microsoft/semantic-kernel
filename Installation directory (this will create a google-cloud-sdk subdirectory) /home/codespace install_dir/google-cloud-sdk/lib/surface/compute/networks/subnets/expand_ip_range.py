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
"""Command for expanding IP range of a subnetwork."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as exceptions
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute.networks.subnets import flags
from googlecloudsdk.core.console import console_io
import ipaddress
import six


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class ExpandIpRange(base.SilentCommand):
  """Expand IP range of a subnetwork."""

  SUBNETWORK_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SUBNETWORK_ARG = flags.SubnetworkArgument()
    cls.SUBNETWORK_ARG.AddArgument(parser)

    parser.add_argument(
        '--prefix-length',
        type=int,
        help=(
            'The new prefix length of the subnet. It must be smaller than the '
            'original and in the private address space 10.0.0.0/8, '
            '172.16.0.0/12 or 192.168.0.0/16 defined in RFC 1918.'),
        required=True)

  def Run(self, args):
    """Issues requests for expanding IP CIDR range."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    new_prefix_length = self._ValidatePrefixLength(args.prefix_length)
    subnetwork_ref = self.SUBNETWORK_ARG.ResolveAsResource(
        args, holder.resources)
    original_ip_cidr_range = self._GetOriginalIpCidrRange(
        client, subnetwork_ref)
    new_ip_cidr_range = self._InferNewIpCidrRange(
        subnetwork_ref.Name(), original_ip_cidr_range, new_prefix_length)
    self._PromptToConfirm(
        subnetwork_ref.Name(), original_ip_cidr_range, new_ip_cidr_range)
    request = self._CreateExpandIpCidrRangeRequest(client, subnetwork_ref,
                                                   new_ip_cidr_range)
    return client.MakeRequests([(client.apitools_client.subnetworks,
                                 'ExpandIpCidrRange', request)])

  def _ValidatePrefixLength(self, new_prefix_length):
    if not 0 <= new_prefix_length <= 29:
      raise exceptions.InvalidArgumentException(
          '--prefix-length',
          'Prefix length must be in the range [0, 29].')
    return new_prefix_length

  def _GetOriginalIpCidrRange(self, client, subnetwork_ref):
    subnetwork = self._GetSubnetwork(client, subnetwork_ref)
    if not subnetwork:
      raise compute_exceptions.ArgumentError(
          'Subnet [{subnet}] was not found in region {region}.'.format(
              subnet=subnetwork_ref.Name(), region=subnetwork_ref.region))

    return subnetwork.ipCidrRange

  def _InferNewIpCidrRange(
      self, subnet_name, original_ip_cidr_range, new_prefix_length):
    unmasked_new_ip_range = '{0}/{1}'.format(
        original_ip_cidr_range.split('/')[0],
        new_prefix_length)
    # ipaddress only allows unicode input
    network = ipaddress.IPv4Network(six.text_type(unmasked_new_ip_range),
                                    strict=False)
    return six.text_type(network)

  def _PromptToConfirm(
      self, subnetwork_name, original_ip_cidr_range, new_ip_cidr_range):
    prompt_message_template = (
        'The IP range of subnetwork [{0}] will be expanded from {1} to {2}. '
        'This operation may take several minutes to complete '
        'and cannot be undone.')
    prompt_message = prompt_message_template.format(
        subnetwork_name, original_ip_cidr_range, new_ip_cidr_range)
    if not console_io.PromptContinue(message=prompt_message, default=True):
      raise compute_exceptions.AbortedError('Operation aborted by user.')

  def _CreateExpandIpCidrRangeRequest(self, client, subnetwork_ref,
                                      new_ip_cidr_range):
    request_body = client.messages.SubnetworksExpandIpCidrRangeRequest(
        ipCidrRange=new_ip_cidr_range)
    return client.messages.ComputeSubnetworksExpandIpCidrRangeRequest(
        subnetwork=subnetwork_ref.Name(),
        subnetworksExpandIpCidrRangeRequest=request_body,
        project=subnetwork_ref.project,
        region=subnetwork_ref.region)

  def _GetSubnetwork(self, client, subnetwork_ref):
    get_request = (
        client.apitools_client.subnetworks,
        'Get',
        client.messages.ComputeSubnetworksGetRequest(
            project=subnetwork_ref.project,
            region=subnetwork_ref.region,
            subnetwork=subnetwork_ref.Name()))

    objects = client.MakeRequests([get_request])

    return objects[0] if objects else None


ExpandIpRange.detailed_help = {
    'brief': 'Expand the IP range of a Compute Engine subnetwork',
    'DESCRIPTION': """
*{command}* expands the IP range of a VPC subnetwork.

For more information about expanding a subnet, see [Expanding a primary IP
range](https://cloud.google.com/vpc/docs/using-vpc#expand-subnet).

This command doesn't work for secondary subnets or for subnets that are used
exclusively for load balancer proxies. For more information, see [Proxy-only
subnets for load balancers](https://cloud.google.com/load-balancing/docs/l7-internal/proxy-only-subnets).
""",
    'EXAMPLES': """
To expand the IP range of ``SUBNET'' to /16, run:

  $ {command} SUBNET --region=us-central1 --prefix-length=16
""",
}

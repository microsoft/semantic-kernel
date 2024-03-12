# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""'vmware external-access-rules update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.externalaccessrules import ExternalAccessRulesClient
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware.network_policies import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Update a VMware Engine external access firewall rule.
        """,
    'EXAMPLES':
        """
          To update an external access firewall rule named `my-external-access-rule` so that it denies the traffic for that rule, run:

            $ {command} my-external-access-rule --network-policy=my-network-policy --action=DENY --location=us-west2 --project=my-project

          Or:

            $ {command} my-external-access-rule --network-policy=my-network-policy --action=DENY

          In the second example, the project and the location are taken from gcloud properties core/project and compute/regions respectively.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a VMware Engine network policy."""
  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddExternalAccessRuleToParser(parser, positional=True)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--description',
        help="""\
        User-provided description of the external access rule.
        """)
    parser.add_argument(
        '--priority',
        type=arg_parsers.BoundedInt(100, 4096),
        help="""\
        Priority of this external access rule. Valid values are numbers between 100 and 4096, with 100 being the highest priority. Firewall rules are processed from highest to lowest priority.
        """)
    parser.add_argument(
        '--ip-protocol',
        choices=['TCP', 'UDP', 'ICMP'],
        help="""\
        Internet protocol covered by the rule. Valid values are TCP, UDP, and ICMP.
        """)
    parser.add_argument(
        '--source-ranges',
        type=arg_parsers.ArgList(min_length=1),
        metavar='SOURCE_IP_RANGES',
        help="""\
        A list of source IP addresses that the rule applies to. Each entry in the list can be a CIDR notation or a single IP address. When the value is set to `0.0.0.0/0`, all IP addresses are allowed.
        """)
    parser.add_argument(
        '--destination-ranges',
        type=arg_parsers.ArgList(min_length=1),
        metavar='DESTINATION_IP_RANGES',
        help="""\
        A list of destination IP addresses that the rule applies to. Each entry in the list be an ExternalAddress resource name or `0.0.0.0/0`. When the value is set to `0.0.0.0/0`, all IP addresses are allowed.
        """)
    parser.add_argument(
        '--source-ports',
        type=arg_parsers.ArgList(min_length=1),
        metavar='SOURCE_PORTS',
        help="""\
        List of allowed source ports. Each entry must be either an integer or a range.
        """)
    parser.add_argument(
        '--destination-ports',
        type=arg_parsers.ArgList(min_length=1),
        metavar='DESTINATION_PORTS',
        help="""\
        List of allowed destination ports. Each entry must be either an integer or a range.
        """)
    parser.add_argument(
        '--action',
        choices=['ALLOW', 'DENY'],
        help="""\
        Whether the firewall rule allows or denies traffic based on a successful rule match.
        """)

  def Run(self, args):
    external_access_rule = args.CONCEPTS.external_access_rule.Parse()
    client = ExternalAccessRulesClient()
    is_async = args.async_
    operation = client.Update(external_access_rule, args.priority,
                              args.ip_protocol, args.source_ranges,
                              args.destination_ranges, args.source_ports,
                              args.destination_ports, args.description,
                              args.action)
    if is_async:
      log.UpdatedResource(
          operation.name,
          kind='VMware Engine external access rule',
          is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for external access rule [{}] to be updated'.format(
            external_access_rule.RelativeName()),
        has_result=True)
    log.UpdatedResource(
        external_access_rule.RelativeName(),
        kind='VMware Engine external access rule',
    )
    return resource

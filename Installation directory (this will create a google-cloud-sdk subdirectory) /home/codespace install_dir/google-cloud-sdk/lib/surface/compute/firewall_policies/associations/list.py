# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command for listing the associations of an organization or folder resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.firewall_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.firewall_policies import flags
import six

# TODO(b/175792396): change displayName to shortName once API is rolled out
DEFAULT_LIST_FORMAT = """\
  table(
    name,
    displayName,
    firewallPolicyId
  )"""


class List(base.DescribeCommand, base.ListCommand):
  """List the associations of an organization or folder resource.

  *{command}* is used to list the associations of an organization or folder
   resource.
  """

  @classmethod
  def Args(cls, parser):
    flags.AddArgsListAssociation(parser)
    parser.display_info.AddFormat(DEFAULT_LIST_FORMAT)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    org_firewall_policy = client.OrgFirewallPolicy(
        compute_client=holder.client,
        resources=holder.resources,
        version=six.text_type(self.ReleaseTrack()).lower())

    target_resource = None

    if args.IsSpecified('organization'):
      target_resource = 'organizations/' + args.organization

    elif args.IsSpecified('folder'):
      target_resource = 'folders/' + args.folder
    res = org_firewall_policy.ListAssociations(
        target_resource=target_resource, only_generate_request=False)
    if not res:
      return None
    return res[0].associations


List.detailed_help = {
    'EXAMPLES':
        """\
    To list the associations of the folder with ID ``987654321", run:

      $ {command} --folder=987654321
    """,
}

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
"""List-custom-constraint command for the Org Policy CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.orgpolicy import service as org_policy_service
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.org_policies import arguments
from googlecloudsdk.command_lib.org_policies import utils

DETAILED_HELP = {
    'DESCRIPTION':
        """\
      Lists the custom constraints set on an organization.
      """,
    'EXAMPLES':
        """\
      To list the custom constraints set on the Organization '1234', run:

      $ {command} --organization=1234
      """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListCustomConstraints(base.ListCommand):
  """Lists the custom constraints set on an organization."""

  @staticmethod
  def Args(parser):
    arguments.AddOrganizationResourceFlagsToParser(parser)

    parser.display_info.AddFormat("""
        table(
        name.split('/').slice(-1).join():label=CUSTOM_CONSTRAINT,
        actionType:label=ACTION_TYPE,
        method_types.list():label=METHOD_TYPES,
        resource_types.list():label=RESOURCE_TYPES,
        display_name:label=DISPLAY_NAME)
     """)

  def Run(self, args):
    org_policy_client = org_policy_service.OrgPolicyClient(self.ReleaseTrack())
    messages = org_policy_service.OrgPolicyMessages(self.ReleaseTrack())
    parent = utils.GetResourceFromArgs(args)
    request = messages.OrgpolicyOrganizationsCustomConstraintsListRequest(
        parent=parent)

    return list_pager.YieldFromList(
        org_policy_client.organizations_customConstraints,
        request,
        field='customConstraints',
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.page_size)


ListCustomConstraints.detailed_help = DETAILED_HELP

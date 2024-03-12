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

"""Command for describing a role."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import flags
from googlecloudsdk.command_lib.iam import iam_util


class Describe(base.DescribeCommand):
  """Show metadata for a role.

  This command shows metadata for a role.

  This command can fail for the following reasons:
  * The role specified does not exist.
  * The active user does not have permission to access the given role.

  ## EXAMPLES

  To print metadata for the role ``spanner.databaseAdmin'' of the organization
  ``1234567'', run:

    $ {command} roles/spanner.databaseAdmin --organization=1234567

  To print metadata for the role ``spanner.databaseAdmin'' of the project
  ``myproject'', run:

    $ {command} roles/spanner.databaseAdmin --project=myproject

  To print metadata for a predefined role, ``spanner.databaseAdmin'', run:

    $ {command} roles/spanner.databaseAdmin
  """

  @staticmethod
  def Args(parser):
    flags.AddParentFlags(parser, 'describe', required=False)
    flags.GetRoleFlag('describe').AddToParser(parser)

  def Run(self, args):
    role_name = iam_util.GetRoleName(args.organization, args.project, args.role)
    client, messages = util.GetClientAndMessages()
    res = client.organizations_roles.Get(
        messages.IamOrganizationsRolesGetRequest(name=role_name))
    iam_util.SetRoleStageIfAlpha(res)
    return res

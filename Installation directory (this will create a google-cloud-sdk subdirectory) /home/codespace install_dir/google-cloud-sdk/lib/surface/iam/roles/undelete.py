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

"""Command for undeleting a role."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.iam import flags
from googlecloudsdk.command_lib.iam import iam_util


class Undelete(base.DescribeCommand):
  """Undelete a custom role from an organization or a project.

  This command undeletes a role. Roles that have been deleted for certain long
  time can't be undeleted.

  This command can fail for the following reasons:
  * The role specified does not exist.
  * The active user does not have permission to access the given role.

  ## EXAMPLES

  To undelete the role ``ProjectUpdater'' of the organization ``1234567'', run:

    $ {command} roles/ProjectUpdater --organization=1234567

  To undelete the role ``ProjectUpdater'' of the project ``myproject'',
  run:

    $ {command} roles/ProjectUpdater --project=myproject
  """

  @staticmethod
  def Args(parser):
    flags.AddParentFlags(parser, 'undelete')
    flags.GetCustomRoleFlag('undelete').AddToParser(parser)

  def Run(self, args):
    client, messages = util.GetClientAndMessages()
    role_name = iam_util.GetRoleName(args.organization, args.project, args.role)
    if args.organization is None and args.project is None:
      raise exceptions.InvalidArgumentException(
          'ROLE_ID',
          'You can not undelete a curated/predefined role.')
    return client.organizations_roles.Undelete(
        messages.IamOrganizationsRolesUndeleteRequest(name=role_name))

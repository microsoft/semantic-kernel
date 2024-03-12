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

"""Command to create a custom role for a project or an organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import flags
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log


DETAILED_HELP = {
    'EXAMPLES':
        """\
          To create a custom role ``ProjectUpdater'' from a YAML file, run:

            $ {command} ProjectUpdater --organization=12345 --file=role_file_path

          To create a custom role ``ProjectUpdater'' with flags, run:

            $ {command} ProjectUpdater --project=myproject --title=ProjectUpdater --description="Have access to get and update the project" --permissions=resourcemanager.projects.get,resourcemanager.projects.update
        """
}


class Create(base.Command):
  r"""Create a custom role for a project or an organization.

  This command creates a custom role with the provided information.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    roles_group = parser.add_group(mutex=True)
    settings_flags_group = roles_group.add_group('Roles Settings')
    settings_flags_group.add_argument(
        '--title', help='The title of the role you want to create.')
    settings_flags_group.add_argument(
        '--description', help='The description of the role you want to create.')
    settings_flags_group.add_argument(
        '--stage', help='The state of the role you want to create. '
        'This represents a role\'s lifecycle phase: `ALPHA`, `BETA`, `GA`, '
        '`DEPRECATED`, `DISABLED`, `EAP`.')
    settings_flags_group.add_argument(
        '--permissions',
        help='The permissions of the role you want to create. '
        'Use commas to separate them.')
    roles_group.add_argument(
        '--file',
        help='The JSON or YAML file with the IAM Role to create. See '
             'https://cloud.google.com/iam/reference/rest/v1/projects.roles.')
    flags.AddParentFlags(parser, 'create')
    flags.GetCustomRoleFlag('create').AddToParser(parser)

  def Run(self, args):
    client, messages = util.GetClientAndMessages()
    parent_name = iam_util.GetParentName(args.organization, args.project)
    if args.file:
      role = iam_util.ParseYamlToRole(args.file, messages.Role)
      role.name = None
      role.etag = None
    else:
      role = messages.Role(title=args.title, description=args.description)
      if args.permissions:
        role.includedPermissions = args.permissions.split(',')
      if args.stage:
        role.stage = iam_util.StageTypeFromString(args.stage)

    if not role.title:
      role.title = args.role

    if not args.quiet:
      permissions_helper = util.PermissionsHelper(client, messages,
                                                  iam_util.GetResourceReference(
                                                      args.project,
                                                      args.organization),
                                                  role.includedPermissions)
      api_diabled_permissions = permissions_helper.GetApiDisabledPermissons()
      iam_util.ApiDisabledPermissionsWarning(api_diabled_permissions)
      testing_permissions = permissions_helper.GetTestingPermissions()
      iam_util.TestingPermissionsWarning(testing_permissions)

    result = client.organizations_roles.Create(
        messages.IamOrganizationsRolesCreateRequest(
            createRoleRequest=messages.CreateRoleRequest(
                role=role, roleId=args.role),
            parent=parent_name))
    log.CreatedResource(args.role, kind='role')
    iam_util.SetRoleStageIfAlpha(result)
    return result

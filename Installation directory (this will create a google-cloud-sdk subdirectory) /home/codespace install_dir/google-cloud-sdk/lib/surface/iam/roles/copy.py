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

"""Command for creating a role from an existing role."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.exceptions import RequiredArgumentException
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log


DETAILED_HELP = {
    'EXAMPLES':
        """\
          To create a copy of an existing role ``spanner.databaseAdmin'' into an organization
          with ``1234567'', run:

            $ {command} --source="roles/spanner.databaseAdmin" --destination=CustomViewer --dest-organization=1234567

          To create a copy of an existing role ``spanner.databaseAdmin'' into a project with
          ``PROJECT_ID'', run:

            $ {command} --source="roles/spanner.databaseAdmin" --destination=CustomSpannerDbAdmin --dest-project=PROJECT_ID

          To modify the newly created role see the roles update command.
        """
}


class Copy(base.Command):
  r"""Create a role from an existing role.

  This command creates a role from an existing role.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--source',
        help='The source role ID. '
        'For predefined roles, for example: roles/viewer. '
        'For custom roles, for example: myCompanyAdmin.')
    parser.add_argument(
        '--destination',
        help='The destination role ID for the new custom '
        'role. For example: viewer.')
    parser.add_argument(
        '--source-organization',
        help='The organization of the source role '
        'if it is an custom role.')
    parser.add_argument(
        '--dest-organization', help='The organization of the destination role.')
    parser.add_argument(
        '--source-project',
        help='The project of the source role '
        'if it is an custom role.')
    parser.add_argument(
        '--dest-project', help='The project of the destination role.')

  def Run(self, args):
    client, messages = util.GetClientAndMessages()
    if args.source is None:
      raise RequiredArgumentException('source', 'the source role is required.')
    if args.destination is None:
      raise RequiredArgumentException('destination',
                                      'the destination role is required.')
    source_role_name = iam_util.GetRoleName(
        args.source_organization,
        args.source_project,
        args.source,
        attribute='the source custom role',
        parameter_name='source')
    dest_parent = iam_util.GetParentName(
        args.dest_organization,
        args.dest_project,
        attribute='the destination custom role')

    source_role = client.organizations_roles.Get(
        messages.IamOrganizationsRolesGetRequest(name=source_role_name))

    new_role = messages.Role(
        title=source_role.title,
        description=source_role.description)

    permissions_helper = util.PermissionsHelper(client, messages,
                                                iam_util.GetResourceReference(
                                                    args.dest_project,
                                                    args.dest_organization),
                                                source_role.includedPermissions)
    not_supported_permissions = permissions_helper.GetNotSupportedPermissions()
    if not_supported_permissions:
      log.warning(
          'Permissions don\'t support custom roles and won\'t be added: ['
          + ', '.join(not_supported_permissions) + '] \n')
    not_applicable_permissions = permissions_helper.GetNotApplicablePermissions(
    )
    if not_applicable_permissions:
      log.warning(
          'Permissions not applicable to the current resource and won\'t'
          ' be added: [' + ', '.join(not_applicable_permissions) + '] \n')
    api_diabled_permissions = permissions_helper.GetApiDisabledPermissons()
    iam_util.ApiDisabledPermissionsWarning(api_diabled_permissions)
    testing_permissions = permissions_helper.GetTestingPermissions()
    iam_util.TestingPermissionsWarning(testing_permissions)
    valid_permissions = permissions_helper.GetValidPermissions()
    new_role.includedPermissions = valid_permissions

    result = client.organizations_roles.Create(
        messages.IamOrganizationsRolesCreateRequest(
            createRoleRequest=messages.CreateRoleRequest(
                role=new_role, roleId=args.destination),
            parent=dest_parent))
    iam_util.SetRoleStageIfAlpha(result)
    return result

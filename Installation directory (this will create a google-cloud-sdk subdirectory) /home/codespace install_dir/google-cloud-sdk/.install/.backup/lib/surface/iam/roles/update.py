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

"""Command for updating a custom role."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.api_lib.util import http_retry
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.iam import flags
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core.console import console_io

import six.moves.http_client


DETAILED_HELP = {
    'EXAMPLES':
        """\
          To update the role ``ProjectUpdater'' from a YAML file, run:

            $ {command} roles/ProjectUpdater --organization=123 --file=role_file_path

          To update the role ``ProjectUpdater'' with flags, run:

            $ {command} roles/ProjectUpdater --project=myproject --permissions=permission1,permission2
        """
}


class Update(base.Command):
  """Update an IAM custom role.

  This command updates an IAM custom role.

  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    updated = parser.add_argument_group(
        'The following flags determine the fields need to be updated. '
        'You can update a role by specifying the following flags, or '
        'you can update a role from a YAML file by specifying the file flag.')
    updated.add_argument(
        '--title', help='The title of the role you want to update.')
    updated.add_argument(
        '--description', help='The description of the role you want to update.')
    updated.add_argument(
        '--stage', help='The state of the role you want to update.')
    updated.add_argument(
        '--permissions',
        help='The permissions of the role you want to set. '
        'Use commas to separate them.')
    updated.add_argument(
        '--add-permissions',
        help='The permissions you want to add to the role. '
        'Use commas to separate them.')
    updated.add_argument(
        '--remove-permissions',
        help='The permissions you want to remove from the '
        'role. Use commas to separate them.')
    parser.add_argument(
        '--file',
        help='The YAML file you want to use to update a role. '
        'Can not be specified with other flags except role-id.')
    flags.AddParentFlags(parser, 'update')
    flags.GetCustomRoleFlag('update').AddToParser(parser)

  def Run(self, args):
    client, messages = util.GetClientAndMessages()
    role_name = iam_util.GetRoleName(args.organization, args.project, args.role)
    role = messages.Role()
    if args.file:
      if (args.title or args.description or args.stage or args.permissions or
          args.add_permissions or args.remove_permissions):
        raise exceptions.ConflictingArgumentsException('file', 'others')
      role = iam_util.ParseYamlToRole(args.file, messages.Role)
      if not role.etag:
        msg = ('The specified role does not contain an "etag" field '
               'identifying a specific version to replace. Updating a '
               'role without an "etag" can overwrite concurrent role '
               'changes.')
        console_io.PromptContinue(
            message=msg,
            prompt_string='Replace existing role',
            cancel_on_no=True)
      if not args.quiet:
        self.WarnPermissions(client, messages, role.includedPermissions,
                             args.project, args.organization)
      try:
        res = client.organizations_roles.Patch(
            messages.IamOrganizationsRolesPatchRequest(
                name=role_name, role=role))
        iam_util.SetRoleStageIfAlpha(res)
        return res
      except apitools_exceptions.HttpConflictError as e:
        raise exceptions.HttpException(
            e, error_format=('Stale "etag": '
                             'Please use the etag from your latest describe '
                             'response. Or new changes have been made since '
                             'your latest describe operation. Please retry '
                             'the whole describe-update process. Or you can '
                             'leave the etag blank to overwrite concurrent '
                             'role changes.'))
      except apitools_exceptions.HttpError as e:
        raise exceptions.HttpException(e)

    res = self.UpdateWithFlags(args, role_name, role, client, messages)
    iam_util.SetRoleStageIfAlpha(res)
    return res

  @http_retry.RetryOnHttpStatus(six.moves.http_client.CONFLICT)
  def UpdateWithFlags(self, args, role_name, role, iam_client, messages):
    role, changed_fields = self.GetUpdatedRole(args, role_name, role,
                                               iam_client, messages)
    return iam_client.organizations_roles.Patch(
        messages.IamOrganizationsRolesPatchRequest(
            name=role_name, role=role, updateMask=','.join(changed_fields)))

  def GetUpdatedRole(self, args, role_name, role, iam_client, messages):
    """Gets the updated role from flags."""
    changed_fields = []
    if args.description is not None:
      changed_fields.append('description')
      role.description = args.description
    if args.title is not None:
      changed_fields.append('title')
      role.title = args.title
    if args.stage:
      changed_fields.append('stage')
      role.stage = iam_util.StageTypeFromString(args.stage)
    if args.permissions is not None and (args.add_permissions or
                                         args.remove_permissions):
      raise exceptions.ConflictingArgumentsException(
          '--permissions', '-add-permissions or --remove-permissions')
    if args.permissions is not None:
      changed_fields.append('includedPermissions')
      role.includedPermissions = args.permissions.split(',')
      if not args.permissions:
        role.includedPermissions = []
      if not args.quiet:
        self.WarnPermissions(iam_client, messages, role.includedPermissions,
                             args.project, args.organization)
    origin_role = iam_client.organizations_roles.Get(
        messages.IamOrganizationsRolesGetRequest(name=role_name))
    if args.add_permissions or args.remove_permissions:
      permissions = set(origin_role.includedPermissions)
      changed = False
      newly_added_permissions = set()
      if args.add_permissions:
        for permission in args.add_permissions.split(','):
          if permission not in permissions:
            permissions.add(permission)
            newly_added_permissions.add(permission)
            changed = True
      if args.remove_permissions:
        for permission in args.remove_permissions.split(','):
          if permission in permissions:
            permissions.remove(permission)
            changed = True
          if permission in newly_added_permissions:
            newly_added_permissions.remove(permission)
      if changed:
        changed_fields.append('includedPermissions')
      role.includedPermissions = list(sorted(permissions))
      if not args.quiet:
        self.WarnPermissions(iam_client, messages,
                             list(newly_added_permissions), args.project,
                             args.organization)
    role.etag = origin_role.etag
    return role, changed_fields

  def WarnPermissions(self, iam_client, messages, permissions, project,
                      organization):
    permissions_helper = util.PermissionsHelper(iam_client, messages,
                                                iam_util.GetResourceReference(
                                                    project, organization),
                                                permissions)
    api_disabled_permissions = permissions_helper.GetApiDisabledPermissons()
    iam_util.ApiDisabledPermissionsWarning(api_disabled_permissions)
    testing_permissions = permissions_helper.GetTestingPermissions()
    iam_util.TestingPermissionsWarning(testing_permissions)

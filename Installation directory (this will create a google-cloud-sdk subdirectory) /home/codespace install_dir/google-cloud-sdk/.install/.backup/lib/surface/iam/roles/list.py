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

"""Command for to list all the roles of a parent organization or a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.iam import flags
from googlecloudsdk.command_lib.iam import iam_util


class List(base.ListCommand):
  """List predefined roles, or the custom roles for an organization or project.

  When an organization or project is specified, this command lists the custom
  roles that are defined for that organization or project.

  Otherwise, this command lists IAM's predefined roles.

  ## EXAMPLES

  To list custom roles for the organization ``12345'', run:

    $ {command} --organization=12345

  To list custom roles for the project ``myproject'', run:

    $ {command} --project=myproject

  To list all predefined roles, run:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--show-deleted',
        action='store_true',
        help='Show deleted roles by specifying this flag.')
    flags.AddParentFlags(parser, 'list', required=False)
    base.ASYNC_FLAG.RemoveFromParser(parser)
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    client, messages = util.GetClientAndMessages()
    if args.project is None and args.organization is None:
      return list_pager.YieldFromList(
          client.roles,
          messages.IamRolesListRequest(showDeleted=args.show_deleted),
          field='roles',
          limit=args.limit,
          batch_size_attribute='pageSize')

    parent_name = iam_util.GetParentName(args.organization, args.project)
    if args.limit is not None and (args.limit < 1):
      raise exceptions.InvalidArgumentException('Limit size must be >=1')

    return list_pager.YieldFromList(
        client.organizations_roles,
        messages.IamOrganizationsRolesListRequest(
            parent=parent_name, showDeleted=args.show_deleted),
        field='roles',
        limit=args.limit,
        batch_size_attribute='pageSize')

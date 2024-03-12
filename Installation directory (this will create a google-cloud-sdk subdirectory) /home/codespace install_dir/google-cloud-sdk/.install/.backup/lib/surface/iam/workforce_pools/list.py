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
"""Command to list all of the workforce pools under a parent organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from apitools.base.py import list_pager
from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.iam.workforce_pools import flags


class List(base.ListCommand):
  """List the workforce pools for an organization.

  Lists all of the workforce pools for an organization given a valid
  organization ID.

  This command can fail for the following reasons:
  * The organization specified does not exist.
  * The active account does not have permission to access the organization.

  ## EXAMPLES

  The following command lists the workforce pools for an organization with the
  ID ``12345'', including soft-deleted pools:

    $ {command} --organization=12345 --location=global --show-deleted
  """

  @staticmethod
  def Args(parser):
    flags.AddParentFlags(parser, 'list')
    flags.AddLocationFlag(parser, 'list')
    parser.add_argument(
        '--show-deleted',
        action='store_true',
        help='Show soft-deleted workforce pools by specifying this flag.')
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    if args.limit is not None and (args.limit < 1):
      raise gcloud_exceptions.InvalidArgumentException('Limit size must be >=1')

    client, messages = util.GetClientAndMessages()
    if not args.organization:
      raise gcloud_exceptions.RequiredArgumentException(
          '--organization',
          'Should specify the organization for workforce pools.')
    parent_name = iam_util.GetParentName(args.organization, None,
                                         'workforce pools')
    return list_pager.YieldFromList(
        client.locations_workforcePools,
        messages.IamLocationsWorkforcePoolsListRequest(
            parent=parent_name,
            showDeleted=args.show_deleted,
            location=flags.ParseLocation(args)),
        field='workforcePools',
        limit=args.limit,
        batch_size=args.page_size,
        batch_size_attribute='pageSize')

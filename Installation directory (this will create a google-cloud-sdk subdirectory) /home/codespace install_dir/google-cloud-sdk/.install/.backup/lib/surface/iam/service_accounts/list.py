# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Command for to list all of a project's service accounts."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.iam import exceptions
from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List all of a project's service accounts."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""
          To list all service accounts in the current project, run:

            $ {command}
      """),
  }

  @staticmethod
  def Args(parser):
    base.ASYNC_FLAG.RemoveFromParser(parser)
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(iam_util.SERVICE_ACCOUNT_FORMAT)
    parser.display_info.AddUriFunc(iam_util.ServiceAccountsUriFunc)

  def Run(self, args):
    if args.limit is not None:
      if args.limit < 1:
        raise exceptions.InvalidArgumentException('Limit size must be >=1')

    project = properties.VALUES.core.project.Get(required=True)
    client, messages = util.GetClientAndMessages()
    for item in list_pager.YieldFromList(
        client.projects_serviceAccounts,
        messages.IamProjectsServiceAccountsListRequest(
            name=iam_util.ProjectToProjectResourceName(project)),
        field='accounts',
        limit=args.limit,
        batch_size_attribute='pageSize'):
      item.disabled = bool(item.disabled)
      yield item

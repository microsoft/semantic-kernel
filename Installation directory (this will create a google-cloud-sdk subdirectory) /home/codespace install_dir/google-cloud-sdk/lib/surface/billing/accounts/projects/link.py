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
"""Command to update a new project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.billing import billing_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.billing import flags
from googlecloudsdk.command_lib.billing import utils


class Link(base.Command):
  """Link a project with a billing account."""

  detailed_help = {
      'DESCRIPTION': """\
          This command links a billing account to a project.

          If the specified billing account is open, this enables billing on the
          project.
          """,
      'EXAMPLES': """\
          To link a billing account `0X0X0X-0X0X0X-0X0X0X` with a project
          `my-project`, run:

            $ {command} my-project --billing-account=0X0X0X-0X0X0X-0X0X0X
          """
  }

  @staticmethod
  def Args(parser):
    account_args_group = parser.add_mutually_exclusive_group(required=True)
    flags.GetOldAccountIdArgument(positional=False).AddToParser(
        account_args_group)
    flags.GetAccountIdArgument(positional=False).AddToParser(account_args_group)

    flags.GetProjectIdArgument().AddToParser(parser)

  def Run(self, args):
    client = billing_client.ProjectsClient()
    project_ref = utils.ParseProject(args.project_id)
    account_ref = utils.ParseAccount(args.billing_account)
    return client.Link(project_ref, account_ref)

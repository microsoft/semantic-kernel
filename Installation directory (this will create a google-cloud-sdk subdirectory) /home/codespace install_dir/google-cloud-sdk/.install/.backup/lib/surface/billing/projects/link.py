# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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


_DETAILED_HELP = {
    'DESCRIPTION': """\
          This command sets or updates the billing account associated with a
          project.

          Billing is enabled on a project when the project is linked to a valid,
          active Cloud Billing account. The billing account accrues charges
          for the usage of resources in all of the linked projects. If the
          project is already linked to a billing account, this command moves
          the project to the billing account you specify, updating the billing
          account that is linked to the project.

          Note that associating a project with a closed billing account has the
          same effect as disabling billing on the project: any paid resources
          in use by the project are shut down, and your application stops
          functioning. Unless you want to disable billing, you should always
          specify a valid, active Cloud Billing account when you run this
          command. Learn how to confirm the status of a Cloud Billing account at
          https://cloud.google.com/billing/docs/how-to/verify-billing-enabled#billing_account_status
          """,
    'EXAMPLES': """\
          To link a billing account `0X0X0X-0X0X0X-0X0X0X` with a project
          `my-project`, run:

            $ {command} my-project --billing-account=0X0X0X-0X0X0X-0X0X0X
          """,
    'API REFERENCE': """\
          This command uses the *cloudbilling/v1* API. The full documentation
          for this API can be found at:
          https://cloud.google.com/billing/v1/getting-started
          """
}


def _RunLink(args):
  client = billing_client.ProjectsClient()
  project_ref = utils.ParseProject(args.project_id)
  account_ref = utils.ParseAccount(args.billing_account)
  return client.Link(project_ref, account_ref)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class LinkAlpha(base.Command):
  """Link a project with a billing account."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    account_args_group = parser.add_mutually_exclusive_group(required=True)
    flags.GetOldAccountIdArgument(positional=False).AddToParser(
        account_args_group)
    flags.GetAccountIdArgument(positional=False).AddToParser(account_args_group)

    flags.GetProjectIdArgument().AddToParser(parser)

  def Run(self, args):
    return _RunLink(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Link(base.Command):
  """Link a project with a billing account."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.GetAccountIdArgument(positional=False,
                               required=True).AddToParser(parser)
    flags.GetProjectIdArgument().AddToParser(parser)

  def Run(self, args):
    return _RunLink(args)

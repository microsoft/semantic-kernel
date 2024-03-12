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
"""Command to disable billing."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.billing import billing_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.billing import flags
from googlecloudsdk.command_lib.billing import utils


class Unlink(base.Command):
  """Unlink the account (if any) linked with a project."""
  detailed_help = {
      'DESCRIPTION': """\
          This command unlinks a project from its associated billing account.
          This action disables billing on the project. Any billable resources
          and services in use in your project are stopped, and your application
          stops functioning. Any costs accrued prior to disabling billing on
          the project are charged to the previously associated billing account.

          Note: To link a project to a different billing account, use the
          `billing projects link` command. You do not need to unlink the
          project first.
          """,
      'EXAMPLES': """\
          To unlink the project `my-project` from its linked billing account,
          run:

            $ {command} my-project
          """,
      'API REFERENCE': """\
          This command uses the *cloudbilling/v1* API. The full documentation
          for this API can be found at:
          https://cloud.google.com/billing/v1/getting-started
          """
  }

  @staticmethod
  def Args(parser):
    flags.GetProjectIdArgument().AddToParser(parser)

  def Run(self, args):
    client = billing_client.ProjectsClient()
    project_ref = utils.ParseProject(args.project_id)
    return client.Link(project_ref, None)

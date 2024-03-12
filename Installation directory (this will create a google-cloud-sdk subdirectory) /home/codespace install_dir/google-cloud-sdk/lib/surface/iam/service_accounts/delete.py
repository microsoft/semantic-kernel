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

"""Command for deleting service accounts."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.api_lib.smart_guardrails import smart_guardrails
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a service account from a project.

  If the service account does not exist, this command returns a
  `PERMISSION_DENIED` error.
  """

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""
          To delete an service account from your project, run:

            $ {command} my-iam-account@my-project.iam.gserviceaccount.com
          """),
  }

  @classmethod
  def Args(cls, parser):
    iam_util.AddServiceAccountNameArg(
        parser, action='to delete')
    if cls.ReleaseTrack() != base.ReleaseTrack.GA:
      iam_util.AddServiceAccountRecommendArg(parser, action='deletion')

  def Run(self, args):
    prompt_message = 'You are about to delete service account [{0}]'.format(
        args.service_account
    )
    client, messages = util.GetClientAndMessages()
    sa_resource_name = iam_util.EmailToAccountResourceName(args.service_account)
    if self.ReleaseTrack() != base.ReleaseTrack.GA and args.recommend:
      # Add deletion risk message to the prompt.
      service_account = client.projects_serviceAccounts.Get(
          messages.IamProjectsServiceAccountsGetRequest(name=sa_resource_name)
      )
      # Parent command group explicitly disables user project quota.
      # Call with user project quota enabled, so that
      # default project can be used as quota project.
      base.EnableUserProjectQuota()
      risk = smart_guardrails.GetServiceAccountDeletionRisk(
          self.ReleaseTrack(),
          service_account.projectId,
          args.service_account,
      )
      base.DisableUserProjectQuota()
      if risk:
        prompt_message += '\n\n{0}'.format(risk)
    console_io.PromptContinue(message=prompt_message, cancel_on_no=True)
    client.projects_serviceAccounts.Delete(
        messages.IamProjectsServiceAccountsDeleteRequest(name=sa_resource_name)
    )

    log.status.Print('deleted service account [{0}]'.format(
        args.service_account))

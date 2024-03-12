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

"""Command for getting IAM policies for service accounts."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util


class GetIamPolicy(base.ListCommand):
  """Get the IAM policy for a service account.

  This command gets the IAM policy for a service account. If formatted as
  JSON, the output can be edited and used as a policy file for
  set-iam-policy. The output includes an "etag" field identifying the version
  emitted and allowing detection of concurrent policy updates; see
  $ gcloud iam service-accounts set-iam-policy for additional details.

  If the service account does not exist, this command returns a
  `PERMISSION_DENIED` error.
  """

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""
          To print the IAM policy for a given service account, run:

            $ {command} my-iam-account@my-project.iam.gserviceaccount.com
          """),
      'DESCRIPTION': '\n\n'.join([
          '{description}',
          iam_util.GetHintForServiceAccountResource('get the iam policy of')])
  }

  @staticmethod
  def Args(parser):
    iam_util.AddServiceAccountNameArg(
        parser,
        action='whose policy to get')
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    client, messages = util.GetClientAndMessages()
    return client.projects_serviceAccounts.GetIamPolicy(
        messages.IamProjectsServiceAccountsGetIamPolicyRequest(
            resource=iam_util.EmailToAccountResourceName(args.service_account),
            options_requestedPolicyVersion=
            iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION))

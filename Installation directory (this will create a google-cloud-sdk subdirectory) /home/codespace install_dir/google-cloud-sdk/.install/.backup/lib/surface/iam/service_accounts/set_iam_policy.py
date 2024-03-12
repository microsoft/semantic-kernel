# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Command for setting IAM policies for service accounts."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util


class SetIamPolicy(base.Command):
  """Set the IAM policy for a service account.

  This command replaces the existing IAM policy for a service account, given
  an IAM_ACCOUNT and a file encoded in JSON or YAML that contains the IAM
  policy. If the given policy file specifies an "etag" value, then the
  replacement will succeed only if the policy already in place matches that
  etag. (An etag obtained via $ gcloud iam service-accounts get-iam-policy will
  prevent the replacement if the policy for the service account has been
  subsequently updated.) A policy file that does not contain an etag value will
  replace any existing policy for the service account.

  If the service account does not exist, this command returns a
  `PERMISSION_DENIED` error.
  """

  detailed_help = iam_util.GetDetailedHelpForSetIamPolicy(
      'service account', 'my-iam-account@my-project.iam.gserviceaccount.com')
  detailed_help['DESCRIPTION'] += '\n\n' + (
      iam_util.GetHintForServiceAccountResource(
          'set the iam policy of'))

  @staticmethod
  def Args(parser):
    iam_util.AddServiceAccountNameArg(
        parser,
        action='whose policy to set')
    parser.add_argument(
        'policy_file',
        metavar='POLICY_FILE',
        help='Path to a local JSON or YAML formatted file '
        'containing a valid policy.')

  def Run(self, args):
    client, messages = util.GetClientAndMessages()
    policy = iam_util.ParsePolicyFile(args.policy_file, messages.Policy)
    policy.version = iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION

    result = client.projects_serviceAccounts.SetIamPolicy(
        messages.IamProjectsServiceAccountsSetIamPolicyRequest(
            resource=iam_util.EmailToAccountResourceName(args.service_account),
            setIamPolicyRequest=messages.SetIamPolicyRequest(
                policy=policy)))
    iam_util.LogSetIamPolicy(args.service_account, 'service account')
    return result

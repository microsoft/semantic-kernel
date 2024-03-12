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

"""Command to create a service account for a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a service account for a project.

  This command creates a service account with the provided name. For
  subsequent commands regarding service accounts, this service account should
  be referred to by the email account in the response.
  """

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""
          To create a service account for your project, run:

            $ {command} some-account-name --display-name="My Service Account"

          To work with this service account in subsequent IAM commands, use the
          email resulting from this call as the IAM_ACCOUNT argument.
          """),
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--display-name', help='A textual name to display for the account.')

    parser.add_argument(
        '--description', help='A textual description for the account.')

    parser.add_argument(
        'name',
        metavar='NAME',
        help='The internal name of the new service account. '
        'Used to generate an IAM_ACCOUNT (an IAM internal '
        'email address used as an identifier of service '
        'account), which must be passed to subsequent '
        'commands.')

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    client, messages = util.GetClientAndMessages()

    result = client.projects_serviceAccounts.Create(
        messages.IamProjectsServiceAccountsCreateRequest(
            name=iam_util.ProjectToProjectResourceName(project),
            createServiceAccountRequest=messages.CreateServiceAccountRequest(
                accountId=args.name,
                serviceAccount=messages.ServiceAccount(
                    displayName=args.display_name,
                    description=args.description))))
    log.CreatedResource(args.name, kind='service account')
    return result

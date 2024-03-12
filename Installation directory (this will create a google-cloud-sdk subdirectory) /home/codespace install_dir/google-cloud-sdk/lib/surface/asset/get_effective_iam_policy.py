# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to call batch get Effective IAM Policies API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base

# pylint: disable=line-too-long
DETAILED_HELP = {
    'DESCRIPTION':
        """\
    Batch get effective IAM policies that match a request.
    """,
    'EXAMPLES':
        """\
    To list effective IAM policies of 1 resource in an organization, run:

      $ {command} --scope=organizations/YOUR_ORG_ID --names=RESOURCE_NAME1

    To list effective IAM policies of 2 resources in a folder, run:

      $ {command} --scope=folders/YOUR_FOLDER_ID --names=RESOURCE_NAME1,RESOURCE_NAME2

    To list effective IAM policies of 3 resources in a project using project ID, run:

      $ {command} --scope=projects/YOUR_PROJECT_ID --names=RESOURCE_NAME1,RESOURCE_NAME2,RESOURCE_NAME3

    To list effective IAM policies of 2 resources in a project using project number, run:

      $ {command} --scope=projects/YOUR_PROJECT_NUMBER --names=RESOURCE_NAME1,RESOURCE_NAME2
    """
}


def AddScopeArgument(parser):
  parser.add_argument(
      '--scope',
      metavar='SCOPE',
      required=True,
      help=("""\
        Scope can be a project, a folder, or an organization. The search is
        limited to the IAM policies within this scope. The caller must be
        granted the ``cloudasset.assets.analyzeIamPolicy'',
        ``cloudasset.assets.searchAllResources'',
        ``cloudasset.assets.searchAllIamPolicies'' permissions
        on the desired scope.

        The allowed values are:

          * ```projects/{PROJECT_ID}``` (e.g. ``projects/foo-bar'')
          * ```projects/{PROJECT_NUMBER}``` (e.g. ``projects/12345678'')
          * ```folders/{FOLDER_NUMBER}``` (e.g. ``folders/1234567'')
          * ```organizations/{ORGANIZATION_NUMBER}``` (e.g. ``organizations/123456'')
        """))


def AddNamesArgument(parser):
  parser.add_argument(
      '--names',
      metavar='NAMES',
      type=arg_parsers.ArgList(min_length=1, max_length=20),
      required=True,
      help=("""\
        Names refer to a list of
        [full resource names](https://cloud.google.com/asset-inventory/docs/resource-name-format)
        of [searchable asset types](https://cloud.google.com/asset-inventory/docs/supported-asset-types).
        For each batch call, total number of names provided is between 1 and 20.

        The example value is:

          * ```//cloudsql.googleapis.com/projects/{PROJECT_ID}/instances/{INSTANCE}```
          (e.g. ``//cloudsql.googleapis.com/projects/probe-per-rt-project/instances/instance1'')
        """))


# pylint: enable=line-too-long


@base.ReleaseTracks(base.ReleaseTrack.GA)
class EffectiveIAMPolicyGA(base.Command):
  """Get effective IAM policies for a specified list of resources within accessible scope, such as a project, folder or organization."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    AddNamesArgument(parser)
    AddScopeArgument(parser)

  def Run(self, args):
    client = client_util.EffectiveIAMPolicyClient()
    return client.BatchGetEffectiveIAMPolicies(args)

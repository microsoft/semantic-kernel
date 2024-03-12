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
"""Command to analyze IAM policy in the specified root asset."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.asset import flags


# pylint: disable=line-too-long
DETAILED_HELP = {
    'DESCRIPTION': """\
      Analyzes IAM policies that match a request.
      """,
    'EXAMPLES': """\
      To find out which users have been granted the
      iam.serviceAccounts.actAs permission on a service account, run:

        $ {command} --organization=YOUR_ORG_ID --full-resource-name=YOUR_SERVICE_ACCOUNT_FULL_RESOURCE_NAME --permissions='iam.serviceAccounts.actAs'

      To find out which resources a user can access, run:

        $ {command} --organization=YOUR_ORG_ID --identity='user:u1@foo.com'

      To find out which roles or permissions a user has been granted on a
      project, run:

        $ {command} --organization=YOUR_ORG_ID --full-resource-name=YOUR_PROJECT_FULL_RESOURCE_NAME --identity='user:u1@foo.com'

      To find out which users have been granted the
      iam.serviceAccounts.actAs permission on any applicable resources, run:

        $ {command} --organization=YOUR_ORG_ID --permissions='iam.serviceAccounts.actAs'
      """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AnalyzeIamPolicyGA(base.Command):
  """Analyzes IAM policies that match a request."""

  detailed_help = DETAILED_HELP

  _API_VERSION = client_util.DEFAULT_API_VERSION

  @classmethod
  def Args(cls, parser):
    flags.AddAnalyzerParentArgs(parser)
    flags.AddAnalyzerSelectorsGroup(parser)
    flags.AddAnalyzerOptionsGroup(parser, True)
    flags.AddAnalyzerConditionContextGroup(parser)
    flags.AddAnalyzerSavedAnalysisQueryArgs(parser)

  def Run(self, args):
    client = client_util.AnalyzeIamPolicyClient(self._API_VERSION)
    return client.Analyze(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class AnalyzeIamPolicyBETA(AnalyzeIamPolicyGA):
  """BETA version, Analyzes IAM policies that match a request."""

  @classmethod
  def Args(cls, parser):
    AnalyzeIamPolicyGA.Args(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AnalyzeIamPolicyALPHA(AnalyzeIamPolicyBETA):
  """ALPHA version, Analyzes IAM policies that match a request."""

  @classmethod
  def Args(cls, parser):
    AnalyzeIamPolicyBETA.Args(parser)
    # TODO(b/304841991): Move versioned field to common parsing function after
    # version label is removed.
    options_group = flags.GetOrAddOptionGroup(parser)
    flags.AddAnalyzerIncludeDenyPolicyAnalysisArgs(options_group)

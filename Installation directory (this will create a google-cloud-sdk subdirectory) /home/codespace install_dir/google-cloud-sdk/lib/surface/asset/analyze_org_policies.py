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
"""Command AnalyzeOrgPolicies API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.asset import client_util
from googlecloudsdk.calliope import base


# pylint: disable=line-too-long
DETAILED_HELP = {
    'DESCRIPTION':
        """\
    Analyze organization policies under a scope.
    """,
    'EXAMPLES':
        """\
    To list 10 organization policies of a constraint in an organization, run:

      $ {command} --scope=organizations/YOUR_ORG_ID --constraint=YOUR_CONSTRAINT_NAME --limit=10
    """
}


def AddScopeArgument(parser):
  parser.add_argument(
      '--scope',
      metavar='SCOPE',
      required=True,
      help=("""\
        Scope can only be an organization. The analysis is
        limited to the Cloud organization policies within this scope. The caller must be
        granted the `cloudasset.assets.searchAllResources` permission on
        the desired scope.

        The allowed values are:

          * ```organizations/{ORGANIZATION_NUMBER}``` (e.g. ``organizations/123456'')
        """))


def AddConstraintArgument(parser):
  parser.add_argument(
      '--constraint',
      metavar='CONSTRAINT',
      required=True,
      help=("""\
        The name of the constraint to analyze organization policies for. The
        response only contains analyzed organization policies for the provided
        constraint.

        Example:

        * organizations/{ORGANIZATION_NUMBER}/customConstraints/{CUSTOM_CONSTRAINT_NAME}
          for a user-defined custom constraint.
        """))


# pylint: enable=line-too-long


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AnalyzeOrgPolicies(base.ListCommand):
  """Analyze organization policies under a scope."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    AddScopeArgument(parser)
    AddConstraintArgument(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    client = client_util.OrgPolicyAnalyzerClient()
    return client.AnalyzeOrgPolicies(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class AnalyzeOrgPoliciesBeta(AnalyzeOrgPolicies):
  """Analyze organization policies under a scope."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    AddScopeArgument(parser)
    AddConstraintArgument(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    client = client_util.OrgPolicyAnalyzerClient()
    return client.AnalyzeOrgPolicies(args)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AnalyzeOrgPoliciesGA(AnalyzeOrgPolicies):
  """Analyze organization policies under a scope."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    AddScopeArgument(parser)
    AddConstraintArgument(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    client = client_util.OrgPolicyAnalyzerClient()
    return client.AnalyzeOrgPolicies(args)

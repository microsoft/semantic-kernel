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
"""Command for listing security policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List security policies.

  ## EXAMPLES

  To list security policies run this:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
        table(
          name,
          region.basename()
        )""")
    lister.AddMultiScopeListerFlags(parser, regional=True, global_=True)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)

    list_implementation = lister.MultiScopeLister(
        client,
        regional_service=client.apitools_client.regionSecurityPolicies,
        global_service=client.apitools_client.securityPolicies,
        aggregation_service=client.apitools_client.securityPolicies)

    return lister.Invoke(request_data, list_implementation)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(base.ListCommand):
  """List security policies.

  ## EXAMPLES

  To list security policies in all scopes run this:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
        table(
          name,
          region.basename()
        )""")
    lister.AddMultiScopeListerFlags(parser, regional=True, global_=True)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)

    list_implementation = lister.MultiScopeLister(
        client,
        regional_service=client.apitools_client.regionSecurityPolicies,
        global_service=client.apitools_client.securityPolicies,
        aggregation_service=client.apitools_client.securityPolicies)

    return lister.Invoke(request_data, list_implementation)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(base.ListCommand):
  """List security policies.

  ## EXAMPLES

  To list security policies in all scopes run this:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
        table(
          name,
          region.basename()
        )""")
    lister.AddMultiScopeListerFlags(parser, regional=True, global_=True)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)

    list_implementation = lister.MultiScopeLister(
        client,
        regional_service=client.apitools_client.regionSecurityPolicies,
        global_service=client.apitools_client.securityPolicies,
        aggregation_service=client.apitools_client.securityPolicies)

    return lister.Invoke(request_data, list_implementation)


List.detailed_help = base_classes.GetGlobalListerHelp('security policies')
ListAlpha.detailed_help = base_classes.GetGlobalRegionalListerHelp(
    'security policies')

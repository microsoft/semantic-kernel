# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for listing forwarding rules."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.forwarding_rules import flags


def _Args(parser):
  """Add flags to list forwarding rules to the parser."""

  parser.display_info.AddFormat("""\
      table(
        name,
        region.basename(),
        IPAddress,
        IPProtocol,
        firstof(
            target,
            backendService).scope():label=TARGET
      )
      """)
  lister.AddMultiScopeListerFlags(parser, regional=True, global_=True)
  parser.display_info.AddCacheUpdater(flags.ForwardingRulesCompleter)


def _Run(args, holder):
  """Issues request necessary to list forwarding rules."""
  client = holder.client

  request_data = lister.ParseMultiScopeFlags(args, holder.resources)

  list_implementation = lister.MultiScopeLister(
      client,
      regional_service=client.apitools_client.forwardingRules,
      global_service=client.apitools_client.globalForwardingRules,
      aggregation_service=client.apitools_client.forwardingRules)

  return lister.Invoke(request_data, list_implementation)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA,
                    base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List forwarding rules."""

  @staticmethod
  def Args(parser):
    _Args(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder)


List.detailed_help = (
    base_classes.GetGlobalRegionalListerHelp('forwarding rules'))

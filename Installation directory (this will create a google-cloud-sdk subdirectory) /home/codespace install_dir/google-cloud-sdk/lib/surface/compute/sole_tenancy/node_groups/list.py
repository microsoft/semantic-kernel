# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""List node groups command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.sole_tenancy.node_groups import flags


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List Compute Engine node groups."""

  @staticmethod
  def Args(parser):
    flags.AddListingShareSettingsArgToParser(parser)

  def Run(self, args):
    if args.share_settings:
      args.GetDisplayInfo().AddTransforms({
          'description': _TransformShareSettings,
      })

      args.GetDisplayInfo().AddFormat("""\
          table(
            name,
            zone.basename(),
            description,
            nodeTemplate.basename(),
            size:label=NODES,
            shareSettings.description()
          )""")
    else:
      args.GetDisplayInfo().AddTransforms({
          'description': _IsShared,
      })

      args.GetDisplayInfo().AddFormat("""\
          table(
            name,
            zone.basename(),
            description,
            nodeTemplate.basename(),
            size:label=NODES,
            shareSettings.description():label=SHARED
          )""")
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    request_data = lister.ParseMultiScopeFlags(args, holder.resources)
    list_implementation = lister.MultiScopeLister(
        client, aggregation_service=client.apitools_client.nodeGroups)

    return lister.Invoke(request_data, list_implementation)


def _IsShared(share_setting):
  """"Transforms share settings to simple share settings information."""
  if share_setting and share_setting['shareType'] != 'LOCAL':
    return 'true'
  return 'false'


def _TransformShareSettings(share_setting):
  """"Transforms share settings to detailed share settings information."""
  if not share_setting or share_setting['shareType'] == 'LOCAL':
    return 'local'
  elif share_setting['shareType'] == 'SPECIFIC_PROJECTS':
    projects = share_setting[
        'projectMap'] if 'projectMap' in share_setting else []
    return 'specific_project:' + ','.join(sorted(projects))
  elif share_setting['shareType'] == 'ORGANIZATION':
    return 'org'
  return ''


List.detailed_help = base_classes.GetRegionalListerHelp('node groups')

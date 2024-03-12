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
"""List PipelineRuns and TaskRuns."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.cloudbuild.v2 import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import run_flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _GetResultURI(resource):
  result = resources.REGISTRY.ParseRelativeName(
      resource.name,
      collection='cloudbuild.projects.locations.results',
      api_version=client_util.GA_API_VERSION)
  return result.SelfLink()


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List all Cloud Build runs in a Google Cloud project."""

  @staticmethod
  def Args(parser):
    parser.display_info.AddUriFunc(_GetResultURI)
    run_flags.AddsRegionResourceArg(parser, False)  # Not required.
    base.LIMIT_FLAG.SetDefault(parser, 50)
    parser.display_info.AddFormat(
        """
        table(
            recordSummaries[0].recordData.name.segment(5).yesno(no="-"):label=ID,
            name.segment(3):label=REGION,
            recordSummaries[0].createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
            result_duration(undefined='-').slice(2:).join("").yesno(no="-"):label=DURATION,
            recordSummaries[0].recordData.workflow.segment(5).yesno(no="-"):label=WORKFLOW,
            result_status():label=STATUS
        )
    """
    )

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    client = client_util.GetClientInstance()
    messages = client_util.GetMessagesModule()

    region_ref = args.CONCEPTS.region.Parse()
    if region_ref:
      parents = [region_ref.RelativeName()]
    else:
      # If no region is specified, list runs from all regions.
      project = args.project or properties.VALUES.core.project.GetOrFail()
      response = client_util.ListLocations(project)
      parents = sorted([location.name for location in response.locations])

    # Manually manage the limit since we'll be making repeated list requests.
    total_limit = args.limit
    parent_errors = []
    # Note: if this serial approach is too slow, we could consider making
    # requests in parallel (similar to http://shortn/_NWVYZQrCtp) although it
    # will be more complicated and harder to do per-parent error reporting.
    for p in parents:
      try:
        results = list_pager.YieldFromList(
            client.projects_locations_results,
            messages.CloudbuildProjectsLocationsResultsListRequest(
                parent=p, filter=args.filter),
            field='results',
            batch_size=args.page_size,
            batch_size_attribute='pageSize',
            limit=total_limit)
        for r in results:
          yield r
          if total_limit is not None:
            total_limit -= 1
      except exceptions.HttpError:
        parent_errors.append(p)

    if parent_errors:
      raise exceptions.Error(
          'Unable to fetch data from: {}'.format(parent_errors))

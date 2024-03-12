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
"""List Workflows."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.cloudbuild.v2 import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import run_flags
from googlecloudsdk.core import properties


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List all Cloud Build runs in a Google Cloud project."""

  @staticmethod
  def Args(parser):
    run_flags.AddsRegionResourceArg(parser, False)  # Not required.
    parser.display_info.AddFormat("""
        table(
            name.segment(5):label=ID,
            name.segment(3):label=REGION,
            createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-')
        )
    """)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    client = client_util.GetClientInstance()
    messages = client_util.GetMessagesModule()

    region_ref = args.CONCEPTS.region.Parse()
    if region_ref:
      parent = region_ref.RelativeName()
    else:
      project = args.project or properties.VALUES.core.project.GetOrFail()
      parent = 'projects/{}/locations/-'.format(project)

    return list_pager.YieldFromList(
        client.projects_locations_workflows,
        messages.CloudbuildProjectsLocationsWorkflowsListRequest(
            parent=parent, filter=args.filter),
        field='workflows',
        batch_size=args.page_size,
        batch_size_attribute='pageSize',
        limit=args.limit)

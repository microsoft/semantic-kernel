# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""List Secure Source Manager repositories command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from googlecloudsdk.api_lib.securesourcemanager import instances
from googlecloudsdk.api_lib.securesourcemanager import repositories
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.source_manager import flags
from googlecloudsdk.command_lib.source_manager import resource_args

DETAILED_HELP = {
    "DESCRIPTION": """
          List Secure Source Manager repositories.
        """,
    "EXAMPLES": """
            To list repositories in location `us-central1` under instance `my-instance`, run:
            $ {command} --region=us-central1 --instance=my-instance
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List all repositories under a Secure Source Manager instance."""

  @staticmethod
  def Args(parser):
    resource_args.AddRegionResourceArg(parser, "to list")
    flags.AddInstance(parser)
    flags.AddPageToken(parser)
    base.FILTER_FLAG.RemoveFromParser(parser)
    base.LIMIT_FLAG.RemoveFromParser(parser)
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

    parser.display_info.AddFormat("""
          table(
            name.basename():label=REPOSITORY_ID:sort=1,
            name.segment(3):label=LOCATION,
            instance.basename():label=INSTANCE_ID,
            createTime.date(),
            uris.html:label=HTML_HOST
          )
        """)

  def Run(self, args):
    # Get resource args to contruct base url
    location_ref = args.CONCEPTS.region.Parse()

    instance_client = instances.InstancesClient()
    api_base_url = instance_client.GetApiBaseUrl(location_ref, args.instance)

    with repositories.OverrideApiEndpointOverrides(api_base_url):
      # List repositories
      client = repositories.RepositoriesClient()
      list_response = client.List(location_ref, args.page_size, args.page_token)
      return list_response.repositories


List.detailed_help = DETAILED_HELP

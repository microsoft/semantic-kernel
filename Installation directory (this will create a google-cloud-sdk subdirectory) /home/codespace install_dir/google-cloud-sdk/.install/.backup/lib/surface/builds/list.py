# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""List builds command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.cloudbuild import filter_rewrite
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.builds import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.resource import resource_projection_spec


class List(base.ListCommand):
  """List builds."""

  detailed_help = {
      'DESCRIPTION': 'List builds.',
      'EXAMPLES': ("""
            To list all completed builds in the current project:

                $ {command}

            To list all builds in the current project in
            QUEUED or WORKING status.:

                $ {command} --ongoing
            """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    flags.AddRegionFlag(parser)
    parser.add_argument(
        '--ongoing',
        help='Only list builds that are currently QUEUED or WORKING.',
        action='store_true')
    base.LIMIT_FLAG.SetDefault(parser, 50)
    base.PAGE_SIZE_FLAG.SetDefault(parser, 20)

    # Default help for base.FILTER_FLAG is inaccurate because GCB does some
    # server-side filtering.
    base.FILTER_FLAG.RemoveFromParser(parser)
    base.Argument(
        '--filter',
        metavar='EXPRESSION',
        require_coverage_in_tests=False,
        category=base.LIST_COMMAND_FLAGS,
        help="""\
        Apply a Boolean filter EXPRESSION to each resource item to be listed.
        If the expression evaluates True, then that item is listed. For more
        details and examples of filter expressions, run $ gcloud topic filters.
        This flag interacts with other flags that are applied in this order:
        --flatten, --sort-by, --filter, --limit.""").AddToParser(parser)

    parser.display_info.AddFormat("""
        table(
            id,
            createTime.date('%Y-%m-%dT%H:%M:%S%Oz', undefined='-'),
            duration(start=startTime,end=finishTime,precision=0,calendar=false,undefined="  -").slice(2:).join(""):label=DURATION,
            build_source(undefined="-"):label=SOURCE,
            build_images(undefined="-"):label=IMAGES,
            status
        )
    """)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    build_region = args.region or cloudbuild_util.DEFAULT_REGION

    client = cloudbuild_util.GetClientInstance()
    messages = cloudbuild_util.GetMessagesModule()

    project_id = properties.VALUES.core.project.GetOrFail()
    parent_resource = resources.REGISTRY.Create(
        collection='cloudbuild.projects.locations',
        projectsId=project_id,
        locationsId=build_region)

    display_info = args.GetDisplayInfo()
    defaults = resource_projection_spec.ProjectionSpec(
        symbols=display_info.transforms, aliases=display_info.aliases)
    args.filter, server_filter = filter_rewrite.Backend(args.ongoing).Rewrite(
        args.filter, defaults=defaults)

    return list_pager.YieldFromList(
        client.projects_locations_builds,
        messages.CloudbuildProjectsLocationsBuildsListRequest(
            parent=parent_resource.RelativeName(),
            pageSize=args.page_size,
            filter=server_filter),
        field='builds',
        batch_size=args.page_size,
        batch_size_attribute='pageSize')

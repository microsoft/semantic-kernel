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
"""Describe a Secure Source Manager repository command."""

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
          Describe a Secure Source Manager repository.
        """,
    "EXAMPLES": """
            To describe a repository called `my-repo` in location `us-central1` inside instance `my-instance`, run:

            $ {command} my-repo --region=us-central1 --instance=my-instance
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Get metadata for a Secure Source Manager repository."""

  @staticmethod
  def Args(parser):
    resource_args.AddRepositoryResourceArg(parser, "to get")
    flags.AddInstance(parser)

  def Run(self, args):
    # Get resource args to contruct base url
    repository_ref = args.CONCEPTS.repository.Parse()

    instance_client = instances.InstancesClient()
    api_base_url = instance_client.GetApiBaseUrl(
        repository_ref.Parent(), args.instance
    )

    with repositories.OverrideApiEndpointOverrides(api_base_url):
      # Create a repository
      client = repositories.RepositoriesClient()
      describe_response = client.Describe(repository_ref)

    return describe_response


Describe.detailed_help = DETAILED_HELP

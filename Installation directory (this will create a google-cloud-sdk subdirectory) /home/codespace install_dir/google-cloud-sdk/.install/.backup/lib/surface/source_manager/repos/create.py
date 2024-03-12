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
"""Create Secure Source Manager repository command."""

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
          Create a Secure Source Manager repository.
        """,
    "EXAMPLES": """
            To create a repository called 'my-repo' in location 'us-central1' in instance 'my-instance', run:

            $ {command} my-repo --region=us-central1 --instance=my-instance
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a Secure Source Manager repository."""

  @staticmethod
  def Args(parser):
    resource_args.AddRepositoryResourceArg(parser, "to create")
    flags.AddInstance(parser)
    flags.AddDescription(parser)
    flags.AddInitialConfigGroup(parser)

  def Run(self, args):
    # Get --instance flag
    instance_id = args.instance

    # Get resource args to contruct base url
    repository_ref = args.CONCEPTS.repository.Parse()

    instance_client = instances.InstancesClient()
    api_base_url = instance_client.GetApiBaseUrl(
        repository_ref.Parent(), instance_id
    )

    with repositories.OverrideApiEndpointOverrides(api_base_url):
      # Create a repository
      client = repositories.RepositoriesClient()
      # this is a shortcut LRO, it completes immediately and is marked as done
      # there is no need to wait
      create_operation = client.Create(
          repository_ref,
          args.description,
          args.default_branch,
          args.gitignores,
          args.license,
          args.readme,
      )
      if not args.IsSpecified("format"):
        args.format = "default"
      return create_operation


Create.detailed_help = DETAILED_HELP

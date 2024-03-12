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
"""List policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import platform_policy
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import flags


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Binary Authorization platform policies.

  ## EXAMPLES

  To list the policies for GKE in the current project:

      $ {command} gke

  To list the policies for GKE in a specific project:

      $ {command} gke --project=my-project-id

  or

      $ {command} projects/my-project-id/gke
  """

  @staticmethod
  def Args(parser):
    flags.AddPlatformResourceArg(parser, 'to list')
    parser.display_info.AddFormat('list(name,description)')

  def Run(self, args):
    platform_ref = args.CONCEPTS.platform_resource_name.Parse().RelativeName()
    # The API is only available in v1.
    return platform_policy.Client('v1').List(
        platform_ref, page_size=args.page_size, limit=args.limit)

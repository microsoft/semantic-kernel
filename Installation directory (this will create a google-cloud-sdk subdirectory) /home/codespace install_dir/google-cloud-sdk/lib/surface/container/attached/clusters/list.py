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
"""Command to list Attached clusters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import attached as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.attached import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util

_EXAMPLES = """
To lists all clusters managed in location ``us-west1'', run:

$ {command} --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Describe(base.ListCommand):
  """List Attached clusters."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser, 'to list')
    parser.display_info.AddFormat(constants.ATTACHED_CLUSTERS_FORMAT)

  def Run(self, args):
    """Runs the list command."""
    location_ref = args.CONCEPTS.location.Parse()
    with endpoint_util.GkemulticloudEndpointOverride(location_ref.locationsId):
      cluster_client = api_util.ClustersClient()
      items, _ = cluster_client.List(location_ref, args.page_size, args.limit)
      return items

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
"""Commmand to list operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import operations as op_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.attached import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import operations

_EXAMPLES = """
To list all operations in location ``us-west1'', run:

$ {command} --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List operations."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    resource_args.AddLocationResourceArg(parser, 'to list operations')
    operations.AddFormat(parser)

  def Run(self, args):
    """Runs the describe command."""
    release_track = self.ReleaseTrack()
    location_ref = args.CONCEPTS.location.Parse()
    with endpoint_util.GkemulticloudEndpointOverride(
        location_ref.locationsId, release_track
    ):
      op_client = op_api_util.OperationsClient()
      items, empty = op_client.List(
          location_ref, args.page_size, args.limit, parent_field='name'
      )
      if not empty:
        # ListOperations returns AWS, Azure, and attached operations.
        # Add a filter for attached operations.
        operations.AddFilter(args, 'attached')
      return items

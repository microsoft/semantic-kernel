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
"""Command to list Storage Insights operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import insights_api
from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List insights operations."""

  detailed_help = {
      'DESCRIPTION': """\
      List storage operations.
      """,
      'EXAMPLES': """\
      To list all operations in "us-central1" for the project "my-project", run:

        $ {command} projects/my-project/locations/us-central1

      To list operations in JSON format, run:

        $ {command} projects/my-project/locations/us-central1 --format=json
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'parent_resource_name',
        help=(
            'The operation parent resource in the format'
            ' ""projects/PROJECT/locations/LOCATION".'
        ),
    )

  def Run(self, args):
    return insights_api.InsightsApi().list_operations(args.parent_resource_name)

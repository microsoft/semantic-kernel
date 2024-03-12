# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""The gcloud firestore operations wait command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import operations
from googlecloudsdk.calliope import base


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA
)
class Wait(base.Command):
  """Waits a Cloud Firestore admin operation to complete."""

  detailed_help = {
      'EXAMPLES':
          """\
          To wait a Cloud Firestore admin operation `exampleOperationId` to
          complete, run:

            $ {command} exampleOperationId
      """
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'name',
        type=str,
        default=None,
        help="""
        The unique name of the Operation to retrieve, formatted as full resource
        path:

          projects/my-app-id/databases/(default)/operations/foo
        """)

  def Run(self, args):
    return operations.WaitForOperationWithName(args.name)

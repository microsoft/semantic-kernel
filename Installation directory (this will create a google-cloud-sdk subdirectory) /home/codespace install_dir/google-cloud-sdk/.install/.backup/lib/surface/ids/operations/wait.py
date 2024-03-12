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
"""'ids operations wait' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
from googlecloudsdk.api_lib.ids import ids_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ids import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Wait for a Cloud IDS operation to complete.
        """,
    'EXAMPLES':
        """
          To get a description of an operation called `my-operation` in
          project `my-project` and zone `us-central1-a`, run:

          $ {command} my-operation --project=my-project --zone=us-central1-a

          OR

          $ {command} projects/myproject/locations/us-central1-a/operations/my-operation
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Wait(base.Command):
  """Wait for a Cloud IDS operation to complete."""

  @staticmethod
  def Args(parser):
    flags.AddOperationResource(parser)
    flags.AddMaxWait(parser, '60m')  # default to 60 minutes wait.

  def Run(self, args):
    operation = args.CONCEPTS.operation.Parse()
    max_wait = datetime.timedelta(seconds=args.max_wait)

    client = ids_api.Client(self.ReleaseTrack())
    return client.WaitForOperation(
        operation_ref=operation,
        message='Waiting for operation to complete',
        has_result=False,
        max_wait=max_wait)


Wait.detailed_help = DETAILED_HELP

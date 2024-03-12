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
"""Command to cancel an insights operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage import insights_api
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Cancel(base.Command):
  """Cancel an insights operation."""

  detailed_help = {
      'DESCRIPTION': """\
      Cancel an insights operation. Since operations are asynchronous, this
      request is best effort and may fail in cases such as when the operation
      is already complete.
      """,
      'EXAMPLES': """\
      To cancel the operation "12345" in "us-central1" for the project
      "my-project", run:

        $ {command} projects/my-project/locations/us-central1/operations/12345
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'operation_name',
        help=(
            'The operation name in the format'
            ' "projects/PROJECT/locations/LOCATION/operations/OPERATION_ID".'
        ),
    )

  def Run(self, args):
    insights_api.InsightsApi().cancel_operation(args.operation_name)
    log.status.Print('Sent cancel request for {}'.format(args.operation_name))

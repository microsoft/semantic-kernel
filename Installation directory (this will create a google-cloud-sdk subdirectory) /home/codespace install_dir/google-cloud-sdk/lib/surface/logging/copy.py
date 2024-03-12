# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""'logging copy' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Copy(base.Command):
  """Copy log entries."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'bucket_id',
        help='Id of the log bucket to copy logs from. Example: my-bucket',
    )
    parser.add_argument(
        'destination',
        help=(
            'Destination to copy logs to. Example: Cloud Storage bucket:'
            ' storage.googleapis.com/my-cloud-storage-bucket'
        ),
    )
    parser.add_argument(
        '--location', required=True, help='Location of the log bucket.'
    )
    parser.add_argument(
        '--log-filter',
        required=False,
        help=(
            'A filter specifying which log entries to copy. '
            'The filter must be no more than 20k characters. '
            'An empty filter matches all log entries.'
        ),
    )

    util.AddParentArgs(parser, 'log entries to copy')

  def _Run(self, args):
    if not args.log_filter:
      console_io.PromptContinue(
          'An empty filter matches all log entries.', cancel_on_no=True)

    parent_name = util.CreateResourceName(
        util.CreateResourceName(
            util.GetParentFromArgs(args), 'locations', args.location),
        'buckets', args.bucket_id)
    request = util.GetMessages().CopyLogEntriesRequest(
        destination=args.destination, filter=args.log_filter, name=parent_name)

    return util.GetClient().entries.Copy(request)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A copy_log_entries operation.

    """
    return self._Run(args)

Copy.detailed_help = {
    'DESCRIPTION':
        """\
        {command} starts the process to copy log entries from a log bucket to a destination.
    """,
    'EXAMPLES':
        """\
        To start a copy log entries operation, run:

          $ {command} BUCKET_ID DESTINATION --location=LOCATION

        To copy log entries in a specific time window, run:

          $ {command} BUCKET_ID DESTINATION --location=LOCATION --log-filter='timestamp<="2021-05-31T23:59:59Z" AND timestamp>="2021-05-31T00:00:00Z"'
    """,
}

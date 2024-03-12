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
"""'logging redact' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
class Redact(base.Command):
  """Redact log entries."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'bucket_id',
        help='Log bucket from which to redact log entries.',
    )
    parser.add_argument(
        '--location', required=True, help='Location of the bucket.'
    )
    parser.add_argument(
        '--log-filter',
        required=False,
        help=(
            'A filter specifying which log entries to Redact. '
            'The filter must be no more than 20k characters. '
            'An empty filter matches all log entries.'
        ),
    )
    parser.add_argument(
        '--reason',
        required=True,
        help=(
            'The reason for the redaction. This field will be recorded in'
            ' redacted log entries and should omit sensitive information.'
            ' Required to be less than 1024 characters.'
        ),
    )

    util.AddParentArgs(parser, 'log entries to redact')

  def _Run(self, args):
    if not args.log_filter:
      console_io.PromptContinue(
          'An empty filter matches all log entries.', cancel_on_no=True
      )

    bucket_name = util.CreateResourceName(
        util.CreateResourceName(
            util.GetParentFromArgs(args), 'locations', args.location
        ),
        'buckets',
        args.bucket_id,
    )

    request = util.GetMessages().RedactLogEntriesRequest(
        filter=args.log_filter, name=bucket_name, reason=args.reason
    )

    return util.GetClient().entries.Redact(request)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: An argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A redact_log_entries operation.
    """
    return self._Run(args)


Redact.detailed_help = {
    'DESCRIPTION': """\
        {command} starts the process to redact log entries from a log bucket.
    """,
    'EXAMPLES': """\
        To start a redact log entries operation, run:

          $ {command} "BUCKET_ID --location=LOCATION --reason='redacting logs'"

        To redact log entries in a specific time window, run:

          $ {command} "BUCKET_ID  --location=LOCATION --reason='redacting logs within a window' --log-filter='timestamp<="2021-05-31T23:59:59Z" AND timestamp>="2021-05-31T00:00:00Z"'"
    """,
}

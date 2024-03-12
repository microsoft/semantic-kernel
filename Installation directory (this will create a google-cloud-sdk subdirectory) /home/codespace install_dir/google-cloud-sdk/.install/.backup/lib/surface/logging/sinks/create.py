# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""'logging sinks create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(
    base.ReleaseTrack.GA, base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA
)
class Create(base.CreateCommand):
  # pylint: disable=line-too-long
  """Create a log sink.

  Create a log sink used to route log entries to a destination. The sink routes
  all log entries that match its *--log-filter* flag.

  An empty filter matches all logs.

  Detailed information about filters can be found at:
  [](https://cloud.google.com/logging/docs/view/logging-query-language)

  The sink's destination can be a Cloud Logging log bucket, a Cloud Storage
  bucket, a BigQuery dataset, a Cloud Pub/Sub topic, or a Google Cloud project.

  The destination must already exist.

  If creating a log sink to route logs to a destination outside of Cloud Logging
  or to a Cloud Logging log bucket in another project, the log sink's service
  account must be granted permission to write to the destination.

  For more information about destination permissions, see:
  https://cloud.google.com/logging/docs/export/configure_export_v2#dest-auth

  Matching log entries are routed to the destination after the sink is created.

  ## EXAMPLES

  To route all Google Compute Engine logs to BigQuery, run:

    $ {command} my-bq-sink
    bigquery.googleapis.com/projects/my-project/datasets/my_dataset --log-filter='resource.type="gce_instance"'

  To route "syslog" from App Engine Flexible to a Cloud Storage bucket, run:

    $ {command} my-gcs-sink storage.googleapis.com/my-bucket --log-filter='logName="projects/my-project/appengine.googleapis.com%2Fsyslog"'

  To route Google App Engine logs with ERROR severity, run:

    $ {command} my-error-logs
    bigquery.googleapis.com/projects/my-project/datasets/my_dataset --log-filter='resource.type="gae_app" AND severity=ERROR'

  To route all logs to a log bucket in a different project, run:

    $ {command} my-sink
    logging.googleapis.com/projects/my-central-project/locations/global/buckets/my-central-bucket

  To route all logs to another project, run:

    $ {command} my-sink
    logging.googleapis.com/projects/my-destination-project
  """
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('sink_name', help='The name for the sink.')
    parser.add_argument('destination', help='The destination for the sink.')
    parser.add_argument(
        '--log-filter',
        required=False,
        help=('A filter expression for the sink. If present, the filter '
              'specifies which log entries to export.'))
    parser.add_argument(
        '--include-children',
        required=False,
        action='store_true',
        help=('Whether to export logs from all child projects and folders. '
              'Only applies to sinks for organizations and folders.'))
    parser.add_argument(
        '--custom-writer-identity',
        metavar='SERVICE_ACCOUNT_EMAIL',
        help=(
            'Writer identity for the sink. This flag can only be used if the '
            'destination is a log bucket in a different project. The writer '
            'identity is automatically generated when it is not provided for '
            'a sink.'
        ))
    bigquery_group = parser.add_argument_group(
        help='Settings for sink exporting data to BigQuery.')
    bigquery_group.add_argument(
        '--use-partitioned-tables',
        required=False,
        action='store_true',
        help=('If specified, use BigQuery\'s partitioned tables. By default, '
              'Logging creates dated tables based on the log entries\' '
              'timestamps, e.g. \'syslog_20170523\'. Partitioned tables remove '
              'the suffix and special query syntax '
              '(https://cloud.google.com/bigquery/docs/'
              'querying-partitioned-tables) must be used.'))
    parser.add_argument(
        '--exclusion',
        action='append',
        type=arg_parsers.ArgDict(
            spec={
                'name': str,
                'description': str,
                'filter': str,
                'disabled': bool
            },
            required_keys=['name', 'filter']),
        help=('Specify an exclusion filter for a log entry that is not to be '
              'exported. This flag can be repeated.\n\n'
              'The ``name\'\' and ``filter\'\' attributes are required. The '
              'following keys are accepted:\n\n'
              '*name*::: An identifier, such as ``load-balancer-exclusion\'\'. '
              'Identifiers are limited to 100 characters and can include only '
              'letters, digits, underscores, hyphens, and periods.\n\n'
              '*description*::: A description of this exclusion.\n\n'
              '*filter*::: An advanced log filter that matches the log entries '
              'to be excluded.\n\n'
              '*disabled*::: If this exclusion should be disabled and not '
              'exclude the log entries.'))

    parser.add_argument('--description', help='Description of the sink.')

    parser.add_argument(
        '--disabled',
        action='store_true',
        help=('Sink will be disabled. Disabled sinks do not export logs.'))

    util.AddParentArgs(parser, 'sink to create')
    parser.display_info.AddCacheUpdater(None)

  def CreateSink(self, parent, sink_data, custom_writer_identity):
    """Creates a v2 sink specified by the arguments."""
    messages = util.GetMessages()
    return util.GetClient().projects_sinks.Create(
        messages.LoggingProjectsSinksCreateRequest(
            parent=parent,
            logSink=messages.LogSink(**sink_data),
            uniqueWriterIdentity=True,
            customWriterIdentity=custom_writer_identity))

  def _Run(self, args):
    if not args.log_filter:
      # Attempt to create a sink with an empty filter.
      console_io.PromptContinue(
          'Sink with empty filter matches all entries.', cancel_on_no=True)

    if args.include_children and not (args.organization or args.folder):
      log.warning('include-children only has an effect for sinks at the folder '
                  'or organization level')

    sink_ref = util.GetSinkReference(args.sink_name, args)

    sink_data = {
        'name': sink_ref.sinksId,
        'destination': args.destination,
        'filter': args.log_filter,
        'includeChildren': args.include_children
    }

    if args.IsSpecified('use_partitioned_tables'):
      bigquery_options = {}
      bigquery_options['usePartitionedTables'] = args.use_partitioned_tables
      sink_data['bigqueryOptions'] = bigquery_options

    if args.IsSpecified('exclusion'):
      sink_data['exclusions'] = args.exclusion

    if args.IsSpecified('description'):
      sink_data['description'] = args.description

    if args.IsSpecified('disabled'):
      sink_data['disabled'] = args.disabled

    custom_writer_identity = None
    if args.IsSpecified('custom_writer_identity'):
      custom_writer_identity = args.custom_writer_identity
    result = self.CreateSink(
        util.GetParentFromArgs(args), sink_data, custom_writer_identity)

    log.CreatedResource(sink_ref)
    self._epilog_result_destination = result.destination
    self._epilog_writer_identity = result.writerIdentity
    return result

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The created sink with its destination.
    """
    return self._Run(args)

  def Epilog(self, unused_resources_were_displayed):
    util.PrintPermissionInstructions(self._epilog_result_destination,
                                     self._epilog_writer_identity)

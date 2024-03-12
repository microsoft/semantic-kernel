# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""'logging metrics update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """\
          Update the description or the filter expression of an existing
          logs-based metric.
      """,
    'EXAMPLES':
        """\
          To update the description of a metric called high_severity_count, run:

            $ {command} high_severity_count --description="Count of high-severity log entries."

          To update the filter expression of the metric, run:

            $ {command} high_severity_count --log-filter="severity >= WARNING"

          Detailed information about filters can be found at:
          [](https://cloud.google.com/logging/docs/view/logging-query-language)

          For advanced features such as user-defined labels and distribution
          metrics, update using a config file:

            $ {command} high_severity_count --config-from-file=$PATH_TO_FILE

          The config file should be in YAML format. Detailed information about
          how to configure metrics can be found at: [](https://cloud.google.com/logging/docs/reference/v2/rest/v2/projects.metrics#LogMetric).
          Any top-level fields in the LogMetric definition that aren't specified
          in the config file will not be updated in the metric.

          To update the bucket associated with a bucket log-based metric, run:

            $ {command} my-bucket-metric --bucket-name="NEW_BUCKET_NAME"
      """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update the definition of a logs-based metric."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument(
        'metric_name', help='The name of the log-based metric to update.')

    config_group = parser.add_argument_group(
        help='Data about the metric to update.', mutex=True, required=True)
    legacy_mode_group = config_group.add_argument_group(
        help=('Arguments to specify information about simple counter logs-'
              'based metrics.'))
    legacy_mode_group.add_argument(
        '--description',
        required=False,
        help=('A new description for the metric. '
              'If omitted, the description is not changed.'))
    legacy_mode_group.add_argument(
        '--log-filter',
        required=False,
        help=('A new filter string for the metric. '
              'If omitted, the filter is not changed.'))
    config_group.add_argument(
        '--config-from-file',
        help=('A path to a YAML file specifying the '
              'updates to be made to the logs-based '
              'metric.'),
        type=arg_parsers.FileContents())

    legacy_mode_group.add_argument(
        '--bucket-name',
        help='The Log Bucket name which owns the log-based metric.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated metric.
    """

    # Calling the API's Update method on a non-existing metric creates it.
    # Make sure the metric exists so we don't accidentally create it.
    metric = util.GetClient().projects_metrics.Get(
        util.GetMessages().LoggingProjectsMetricsGetRequest(
            metricName=util.CreateResourceName(util.GetCurrentProjectParent(),
                                               'metrics', args.metric_name)))

    updated_metric = util.UpdateLogMetric(
        metric,
        description=args.description,
        log_filter=args.log_filter,
        bucket_name=args.bucket_name,
        data=args.config_from_file)

    result = util.GetClient().projects_metrics.Update(
        util.GetMessages().LoggingProjectsMetricsUpdateRequest(
            metricName=util.CreateResourceName(util.GetCurrentProjectParent(),
                                               'metrics', args.metric_name),
            logMetric=updated_metric))
    log.UpdatedResource(args.metric_name)
    return result


Update.detailed_help = DETAILED_HELP

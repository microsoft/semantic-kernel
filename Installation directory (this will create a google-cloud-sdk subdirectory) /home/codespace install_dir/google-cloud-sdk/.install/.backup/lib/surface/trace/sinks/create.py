# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""'trace sinks create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.trace import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
        Creates a sink used to export trace spans to a destination.

        The sink's destination must be a BigQuery dataset.
        The destination must already exist. The identity created with the sink
        will need permission to write to the destination dataset. After creating
        a sink look for the *[writer_identity]* to be populated in the response.
        With that identity run the following command to give it permission:

        gcloud projects add-iam-policy-binding {bigquery_project_id} \\
          --member serviceAccount:{writer_identity from trace_sink} \\
          --role roles/bigquery.dataEditor

        You may also find an existing writer identity by describing a sink.

        It may take several minutes before trace spans are exported after the
        sink is created.
    """,
    'EXAMPLES':
        """
        $ {command} my-sink
      bigquery.googleapis.com/projects/my-project/datasets/my_dataset
    """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  # pylint: disable=line-too-long
  """Creates a sink."""
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('sink_name', help='The name for the sink.')
    parser.add_argument(
        'destination',
        help='The destination must be a fully qualified BigQuery resource name.'
        ' The destination can be for the same Google Cloud project or for a'
        ' different Google Cloud project in the same organization.')
    parser.add_argument(
        '--project',
        help='Create a sink associated with this project.'
        ' This will override the default project.')
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The created sink with its destination.
    """
    sink_resource_name = util.GetTraceSinkResource(args.sink_name,
                                                   args.project).RelativeName()

    sink_data = {
        'name': sink_resource_name,
        'outputConfig': {
            'destination': args.destination
        }
    }

    result_sink = util.GetClient().projects_traceSinks.Create(
        util.GetMessages().CloudtraceProjectsTraceSinksCreateRequest(
            parent=util.GetProjectResource(args.project).RelativeName(),
            traceSink=util.GetMessages().TraceSink(**sink_data)))

    log.status.Print(
        'You can give permission to the service account by running the '
        'following command.\ngcloud projects add-iam-policy-binding '
        'bigquery-project \\\n--member serviceAccount:{0} \\\n--role '
        'roles/bigquery.dataEditor'.format(result_sink.writerIdentity))

    return util.FormatTraceSink(result_sink)


Create.detailed_help = DETAILED_HELP

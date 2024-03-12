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
"""'trace sinks update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.trace import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """/
        Changes the *[destination]* associated with a sink.
        The new destination must already exist and Stackdriver Trace must have
        permission to write to it.

        Trace spans are exported to the new destination in a few minutes.
    """,
    'EXAMPLES':
        """/

        $ {command} my-sink bigquery.googleapis.com/projects/my-project/datasets/my_new_dataset
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Updates a sink."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('sink_name', help='The name of the sink to update.')
    parser.add_argument(
        'destination',
        help='The new destination for the sink. The destination must be a fully'
        ' qualified BigQuery resource name. The destination can be for the same'
        ' Google Cloud project or for a different Google Cloud project in the'
        ' same organization.')
    parser.add_argument(
        '--project',
        help='Update a sink associated with this project.'
        ' This will override the default project.')
    parser.display_info.AddFormat('yaml')
    parser.display_info.AddCacheUpdater(None)

  def PatchSink(self, sink_name, sink_data, update_mask):
    """Patches a sink specified by the arguments."""
    messages = util.GetMessages()
    return util.GetClient().projects_traceSinks.Patch(
        messages.CloudtraceProjectsTraceSinksPatchRequest(
            name=sink_name,
            traceSink=messages.TraceSink(**sink_data),
            updateMask=','.join(update_mask)))

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The updated sink with its new destination.
    """
    sink_ref = util.GetTraceSinkResource(args.sink_name, args.project)
    sink_resource_name = sink_ref.RelativeName()

    sink_data = {'name': sink_resource_name}
    update_mask = []
    if args.IsSpecified('destination'):
      sink_data['outputConfig'] = {'destination': args.destination}
      update_mask.append('output_config.destination')

    if not update_mask:
      raise calliope_exceptions.MinimumArgumentException(
          'Please specify the destination to update')

    result = self.PatchSink(sink_resource_name, sink_data, update_mask)
    log.UpdatedResource(sink_ref)
    return util.FormatTraceSink(result)


Update.detailed_help = DETAILED_HELP

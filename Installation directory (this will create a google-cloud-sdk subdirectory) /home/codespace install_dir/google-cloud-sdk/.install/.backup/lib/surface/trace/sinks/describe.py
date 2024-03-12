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
"""'trace sinks describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.trace import util
from googlecloudsdk.calliope import base

DETAILED_HELP = {
    'DESCRIPTION': """
        Displays information about a sink.
    """,
    'EXAMPLES': """/

        $ {command} my-sink
    """,
}


class Describe(base.DescribeCommand):
  """Displays information about a sink."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('sink_name', help='The name of the sink to describe.')
    parser.add_argument(
        '--project',
        help='Describe a sink associated with this project.'
        ' This will override the default project.')
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified sink with its destination.
    """
    sink_resource_name = util.GetTraceSinkResource(args.sink_name,
                                                   args.project).RelativeName()
    result_sink = util.GetClient().projects_traceSinks.Get(
        util.GetMessages().CloudtraceProjectsTraceSinksGetRequest(
            name=sink_resource_name))
    return util.FormatTraceSink(result_sink)


Describe.detailed_help = DETAILED_HELP

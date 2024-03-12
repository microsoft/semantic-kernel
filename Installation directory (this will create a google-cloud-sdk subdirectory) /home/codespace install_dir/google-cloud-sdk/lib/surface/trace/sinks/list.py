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
"""'trace sinks list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.trace import util
from googlecloudsdk.calliope import base

DETAILED_HELP = {
    'DESCRIPTION': """
        Lists the defined sinks for the project.
    """,
    'EXAMPLES': """/

        $ {command}
    """,
}


class List(base.ListCommand):
  """Lists the defined sinks for the project."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.LIMIT_FLAG.RemoveFromParser(parser)
    base.SORT_BY_FLAG.RemoveFromParser(parser)
    base.FILTER_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--project',
        help='List all sinks associated with this project.'
        ' This will override the default project.')
    parser.display_info.AddFormat('table(name, destination, writer_identity)')
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      The list of sinks.
    """
    result = util.GetClient().projects_traceSinks.List(
        util.GetMessages().CloudtraceProjectsTraceSinksListRequest(
            parent=util.GetProjectResource(args.project).RelativeName()))
    for sink in result.sinks:
      yield util.FormatTraceSink(sink)


List.detailed_help = DETAILED_HELP

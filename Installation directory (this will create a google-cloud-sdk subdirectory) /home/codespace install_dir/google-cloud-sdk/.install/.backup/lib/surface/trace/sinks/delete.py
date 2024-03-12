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
"""'logging sinks delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.trace import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'DESCRIPTION':
        """/
        Deletes a sink and halts the export of traces associated with that sink.
        Deleting a sink does not affect traces already exported through
        the deleted sink, and will not affect other sinks that are exporting
        the same traces.
    """,
    'EXAMPLES':
        """/

        $ {command} my-sink
    """,
}


class Delete(base.DeleteCommand):
  """Deletes a sink."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('sink_name', help='The name of the sink to delete.')
    parser.add_argument(
        '--project',
        help='Delete a sink associated with this project.'
        ' This will override the default project.')
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.
    """
    console_io.PromptContinue(
        'Really delete sink [%s]?' % args.sink_name,
        cancel_on_no=True,
        default=False)

    sink_ref = util.GetTraceSinkResource(args.sink_name, args.project)

    sink_resource_name = sink_ref.RelativeName()

    util.GetClient().projects_traceSinks.Delete(
        util.GetMessages().CloudtraceProjectsTraceSinksDeleteRequest(
            name=sink_resource_name))

    log.DeletedResource(sink_ref)


Delete.detailed_help = DETAILED_HELP

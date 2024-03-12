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

"""'logging sinks delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a sink.

  Delete a sink and halt the export of log entries associated with that sink.
  Deleting a sink does not affect log entries already exported through
  the deleted sink, and will not affect other sinks that are exporting
  the same log(s).

  ## EXAMPLES

  To delete a sync 'my-bq-sync':

    $ {command} my-bq-sink
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('sink_name', help='The name of the sink to delete.')
    util.AddParentArgs(parser, 'sink to delete')
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.
    """
    sink_ref = util.GetSinkReference(args.sink_name, args)
    sink_resource = util.CreateResourceName(util.GetParentFromArgs(args),
                                            'sinks', sink_ref.sinksId)

    console_io.PromptContinue('Really delete sink [%s]?' % sink_ref.sinksId,
                              cancel_on_no=True)

    util.GetClient().projects_sinks.Delete(
        util.GetMessages().LoggingProjectsSinksDeleteRequest(
            sinkName=sink_resource))
    log.DeletedResource(sink_ref)

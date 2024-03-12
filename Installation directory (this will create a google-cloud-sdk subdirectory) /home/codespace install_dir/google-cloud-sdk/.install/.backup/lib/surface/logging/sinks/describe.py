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

"""'logging sinks describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base


class Describe(base.DescribeCommand):
  """Display information about a sink.

  Display information about a sink.

  ## EXAMPLES

  To describe a sync 'my-bq-sync':

    $ {command} my-bq-sink
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.add_argument('sink_name', help='The name of the sink to describe.')
    util.AddParentArgs(parser, 'sink to describe')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified sink with its destination.
    """
    sink_ref = util.GetSinkReference(args.sink_name, args)
    sink_resource = util.CreateResourceName(util.GetParentFromArgs(args),
                                            'sinks', sink_ref.sinksId)
    return util.GetClient().projects_sinks.Get(
        util.GetMessages().LoggingProjectsSinksGetRequest(
            sinkName=sink_resource))

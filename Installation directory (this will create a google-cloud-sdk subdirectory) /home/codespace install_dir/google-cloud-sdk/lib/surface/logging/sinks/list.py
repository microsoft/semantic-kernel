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

"""'logging sinks list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List the defined sinks.

  List the defined sinks.

  ## EXAMPLES

  To list all defined sinks:

    $ {command} --limit=10
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    util.AddParentArgs(parser, 'sinks to list')
    parser.display_info.AddFormat('table(name, destination, filter)')
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      The list of sinks.
    """
    result = util.GetClient().projects_sinks.List(
        util.GetMessages().LoggingProjectsSinksListRequest(
            parent=util.GetParentFromArgs(args)))
    for sink in result.sinks:
      if not sink.filter:
        sink.filter = '(empty filter)'
      yield sink

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

"""'logging resource-descriptors list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List all available resource descriptors.

  ## EXAMPLES

  To list all resource descriptors:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.display_info.AddFormat(
        'table(type, description, labels[].key.list())')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The list of log entries.
    """
    return list_pager.YieldFromList(
        util.GetClient().monitoredResourceDescriptors,
        util.GetMessages().LoggingMonitoredResourceDescriptorsListRequest(),
        field='resourceDescriptors', limit=args.limit,
        batch_size=args.limit, batch_size_attribute='pageSize')


List.detailed_help = {
    'DESCRIPTION': ("""
        List all available resource descriptors that are used by Cloud
        Logging. Each log entry must be associated with a valid resource
        descriptor.
    """),
}

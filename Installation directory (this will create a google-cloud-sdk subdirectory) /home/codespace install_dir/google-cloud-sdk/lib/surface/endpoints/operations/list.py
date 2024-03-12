# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""service-management operations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.endpoints import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.endpoints import arg_parsers
from googlecloudsdk.command_lib.endpoints import common_flags


_FILTER_HELP = '''\
Apply a Boolean filter _EXPRESSION_ to each resource item to be listed.
If the expression evaluates as True then that item is listed.

The available filter fields are startTime and done. Unrecognized fields will
cause an error.

startTime is an ISO 8601 datetime and supports >=, >, <=, and < operators. The
datetime value must be wrapped in quotation marks. For example:

  --filter='startTime < "2017-03-20T16:02:32"'

done is a boolean value and supports = and != operators.\
'''


class List(base.ListCommand):
  # pylint: disable=line-too-long
  """List operations for a project.

     This command will list operations for a service, optionally matching
     a particular filter.

     ## EXAMPLES
     To list all operations for a service named
     `api.endpoints.proj.cloud.goog`, run:

       $ {command} --service=api.endpoints.proj.cloud.goog

     To list only operations which are complete, add the `--filter` argument
     with a status filter:

       $ {command} --service=api.endpoints.proj.cloud.goog --filter='done = true'

     To list only operations begun after a certain point in time, add the
     `--filter` argument with an ISO 8601 datetime startTime filter:

       $ {command} --service=api.endpoints.proj.cloud.goog --filter='startTime >= "2017-02-01"'
  """
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    common_flags.producer_service_flag(
        suffix='for which to list operations',
        flag_name='--service').AddToParser(parser)
    base.FILTER_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--filter', metavar='EXPRESSION',
        help=_FILTER_HELP)
    parser.display_info.AddFormat(
        'table(name, done, metadata.startTime.date(tz=LOCAL))')
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    """Run 'service-management operations list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of operations for this project.
    """
    messages = services_util.GetMessagesModule()
    client = services_util.GetClientInstance()
    service = arg_parsers.GetServiceNameFromArg(args.service)

    msg_filter = 'serviceName="{0}"'.format(service)
    if args.filter:
      msg_filter += ' AND ({0})'.format(args.filter)
      args.filter = None  # We don't want Display() to handle the filter.

    msg = messages.ServicemanagementOperationsListRequest(filter=msg_filter)

    return list_pager.YieldFromList(
        client.operations,
        msg,
        limit=args.limit,
        batch_size_attribute='pageSize',
        batch_size=args.page_size,
        field='operations')

# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to list transfer agent pools."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transfer import list_util
from googlecloudsdk.command_lib.transfer import name_util
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_printer


class List(base.Command):
  """List Transfer Service transfer agent pools."""

  detailed_help = {
      'DESCRIPTION':
          """\
      List Transfer Service transfer pools in a given project to show their
      configurations.
      """,
      'EXAMPLES':
          """\
      To list all agent pools in your current project, run:

        $ {command}

      To list agent pools named "foo" and "bar" in your project, run:

        $ {command} --names=foo,bar

      To list all information about jobs 'foo' and 'bar' formatted as JSON, run:

        $ {command} --names=foo,bar --format=json
      """,
  }

  @staticmethod
  def Args(parser):
    list_util.add_common_list_flags(parser)

    parser.add_argument(
        '--names',
        type=arg_parsers.ArgList(),
        metavar='NAMES',
        help='The names of the agent pools you want to list. Separate multiple'
        ' names with commas (e.g., --name=foo,bar). If not specified, all'
        ' agent pools in your current project will be listed.')

  def Display(self, args, resources):
    """API response display logic."""
    resource_printer.Print(resources, args.format or 'yaml')

  def Run(self, args):
    """Command execution logic."""
    client = apis.GetClientInstance('transfer', 'v1')
    messages = apis.GetMessagesModule('transfer', 'v1')

    if args.names:
      formatted_agent_pool_names = name_util.add_agent_pool_prefix(args.names)
    else:
      formatted_agent_pool_names = None

    filter_dictionary = {
        'agentPoolNames': formatted_agent_pool_names,
    }
    filter_string = json.dumps(filter_dictionary)

    resources_iterator = list_pager.YieldFromList(
        client.projects_agentPools,
        messages.StoragetransferProjectsAgentPoolsListRequest(
            filter=filter_string,
            projectId=properties.VALUES.core.project.Get()),
        batch_size=args.page_size,
        batch_size_attribute='pageSize',
        field='agentPools',
        limit=args.limit,
    )
    list_util.print_transfer_resources_iterator(resources_iterator,
                                                self.Display, args)

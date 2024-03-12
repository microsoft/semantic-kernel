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
"""Command to create a Transfer Service agent pool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.transfer import agent_pools_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transfer import agent_pools_flag_util
from googlecloudsdk.command_lib.transfer import name_util


class Create(base.Command):
  """Create a Transfer Service agent pool."""

  # pylint:disable=line-too-long
  detailed_help = {
      'DESCRIPTION':
          """\
      Create an agent pool -- a group of agents used to connect to a source or
      destination filesystem.
      """,
      'EXAMPLES':
          """\
      To create an agent pool with name 'my-pool', display name 'daily backups',
      and no bandwidth limit, run:

          $ {command} my-pool --display-name='daily backups'

      To create an agent pool with name 'my-pool', display name 'daily backups',
      and a bandwidth limit of 50 MB/s, run:

          $ {command} my-pool --display-name="daily backups" --bandwidth-limit=50

      """
  }
  # pylint:enable=line-too-long

  @staticmethod
  def Args(parser):
    agent_pools_flag_util.setup_parser(parser)
    parser.add_argument(
        '--no-async',
        action='store_true',
        help='Block other tasks in your terminal until the pool has been'
        ' created. If not included, pool creation will run asynchronously.')

  def Run(self, args):
    client = apis.GetClientInstance('transfer', 'v1')
    messages = apis.GetMessagesModule('transfer', 'v1')
    formatted_agent_pool_name = name_util.add_agent_pool_prefix(args.name)
    agent_pool_id = name_util.remove_agent_pool_prefix(args.name)
    agent_pool_project = name_util.get_agent_pool_project_from_string(
        formatted_agent_pool_name)

    agent_pool_object = messages.AgentPool(
        displayName=args.display_name, name=formatted_agent_pool_name)
    if args.bandwidth_limit:
      agent_pool_object.bandwidthLimit = messages.BandwidthLimit(
          limitMbps=args.bandwidth_limit)

    initial_result = client.projects_agentPools.Create(
        messages.StoragetransferProjectsAgentPoolsCreateRequest(
            agentPool=agent_pool_object,
            agentPoolId=agent_pool_id,
            projectId=agent_pool_project))

    if args.no_async:
      final_result = agent_pools_util.block_until_created(
          formatted_agent_pool_name)
    else:
      final_result = initial_result

    return final_result

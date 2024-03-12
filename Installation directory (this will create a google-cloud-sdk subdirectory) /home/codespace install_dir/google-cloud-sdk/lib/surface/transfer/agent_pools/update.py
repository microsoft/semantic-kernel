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
"""Command to update a Transfer Service agent pool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transfer import agent_pools_flag_util
from googlecloudsdk.command_lib.transfer import name_util


class Update(base.Command):
  """Update a Transfer Service agent pool."""

  # pylint:disable=line-too-long
  detailed_help = {
      'DESCRIPTION':
          """\
      Update an agent pool.
      """,
      'EXAMPLES':
          """\
      To remove the bandwidth limit for agent pool 'foo', run:

          $ {command} foo --clear-bandwidth-limit

      To remove the display name for agent pool 'foo', run:

          $ {command} foo --clear-display-name

      To update the bandwidth limit for agent pool 'foo' to 100 MB/s, run:

          $ {command} foo --bandwidth-limit=100

      To update the display name for agent pool 'foo' to 'example name', run:

          $ {command} foo --display-name="example name"
      """
  }
  # pylint:enable=line-too-long

  @staticmethod
  def Args(parser):
    agent_pools_flag_util.setup_parser(parser)
    parser.add_argument(
        '--clear-display-name',
        action='store_true',
        help='Remove the display name from the agent pool.')
    parser.add_argument(
        '--clear-bandwidth-limit',
        action='store_true',
        help="Remove the agent pool's bandwidth limit, which enables the pool's"
        ' agents to use all bandwidth available to them.')

  def Run(self, args):
    client = apis.GetClientInstance('transfer', 'v1')
    messages = apis.GetMessagesModule('transfer', 'v1')

    agent_pool_object = messages.AgentPool()
    update_mask_list = []
    if args.bandwidth_limit or args.clear_bandwidth_limit:
      update_mask_list.append('bandwidth_limit')
      if args.bandwidth_limit:
        agent_pool_object.bandwidthLimit = messages.BandwidthLimit(
            limitMbps=args.bandwidth_limit)
    if args.display_name or args.clear_display_name:
      update_mask_list.append('display_name')
      agent_pool_object.displayName = args.display_name

    if update_mask_list:
      update_mask = ','.join(update_mask_list)
    else:
      update_mask = None

    formatted_agent_pool_name = name_util.add_agent_pool_prefix(args.name)
    return client.projects_agentPools.Patch(
        messages.StoragetransferProjectsAgentPoolsPatchRequest(
            agentPool=agent_pool_object,
            name=formatted_agent_pool_name,
            updateMask=update_mask))

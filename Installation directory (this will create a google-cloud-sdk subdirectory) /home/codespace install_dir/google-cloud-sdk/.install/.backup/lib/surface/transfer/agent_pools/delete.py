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
"""Command to delete transfer agent pools."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transfer import name_util


class Delete(base.Command):
  """Delete a Transfer Service agent pool."""

  # pylint:disable=line-too-long
  detailed_help = {
      'DESCRIPTION':
          """\
      Delete an agent pool. Note that before you can delete a pool, all
      the pool's agents must be stopped, its associated jobs must be disabled,
      and there must be no associated in-progress transfer operations.
      """,
      'EXAMPLES':
          """\
      To delete agent pool 'foo', run:

        $ {command} foo

      To check if there are active operations associated with a pool before
      deleting it, scroll through the results of:

        $ {grandparent_command} operations list --format=yaml --operation-statuses=in_progress
      """
  }
  # pylint:enable=line-too-long

  @staticmethod
  def Args(parser):
    parser.add_argument('name', help='The name of the job you want to delete.')

  def Run(self, args):
    client = apis.GetClientInstance('transfer', 'v1')
    messages = apis.GetMessagesModule('transfer', 'v1')

    formatted_agent_pool_name = name_util.add_agent_pool_prefix(args.name)

    client.projects_agentPools.Delete(
        messages.StoragetransferProjectsAgentPoolsDeleteRequest(
            name=formatted_agent_pool_name))

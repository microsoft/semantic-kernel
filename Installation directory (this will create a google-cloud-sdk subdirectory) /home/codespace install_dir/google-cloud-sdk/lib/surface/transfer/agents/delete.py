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
"""Command to delete transfer agents."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.core.resource import resource_printer


_DELETE_SPECIFIC_AGENTS_MESSAGE_FORMAT = """\
To delete specific agents on your machine, run the following Docker command:

docker stop {}

Note: If you encounter a permission error, you may need to add "sudo" before "docker".
"""
_DELETE_ALL_AGENTS_COMMAND = (
    'docker stop $(docker container list --quiet --all --filter'
    ' ancestor=gcr.io/cloud-ingest/tsop-agent)')
_DELETE_ALL_AGENTS_MESSAGE = """\
To delete all agents on your machine, run the following Docker command:

{}

Note: If you encounter a permission error, you may need to add "sudo" before both instances of "docker".
""".format(_DELETE_ALL_AGENTS_COMMAND)
_UNINSTALL_MESSAGE = """\
To delete all agents on your machine and uninstall the machine's agent Docker image, run the following commands:

{}
# May take a moment for Docker containers to shutdown before you can run:
docker image rm gcr.io/cloud-ingest/tsop-agent

Note: If you encounter a permission error, you may need to add "sudo" before all three instances of "docker".
""".format(_DELETE_ALL_AGENTS_COMMAND)
_LIST_AGENTS_MESSAGE = """\
Pick which agents to delete. You can include --all to delete all agents on your machine or --ids to specify agent IDs. You can find agent IDs by running:

docker container list --all --filter ancestor=gcr.io/cloud-ingest/tsop-agent

"""


class Delete(base.Command):
  """Delete a Transfer Service transfer agents."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Delete agents and remove agent resources from your machine.

      """,
      'EXAMPLES':
          """\
      If you plan to delete specific agents, you can list which agents are running on your machine by running:

        $ docker container list --all --filter ancestor=gcr.io/cloud-ingest/tsop-agent

      Then run:

        $ {command} --ids=id1,id2,...
      """
  }

  @staticmethod
  def Args(parser):
    mutually_exclusive_flags_group = parser.add_group(
        mutex=True, sort_args=False)
    mutually_exclusive_flags_group.add_argument(
        '--ids',
        type=arg_parsers.ArgList(),
        metavar='IDS',
        help='The IDs of the agents you want to delete. Separate multiple agent'
        ' IDs with commas, with no spaces following the commas.')
    mutually_exclusive_flags_group.add_argument(
        '--all',
        action='store_true',
        help='Delete all agents running on your machine.')
    mutually_exclusive_flags_group.add_argument(
        '--uninstall',
        action='store_true',
        help='Fully uninstall the agent Docker image in addition to deleting'
        ' the agents. Uninstalling the Docker image will free up space, but'
        " you'll need to reinstall it to run agents on this machine in the"
        ' future.')

  def Display(self, args, resources):
    del args  # Unsued.
    resource_printer.Print(resources, 'object')

  def Run(self, args):
    if args.ids:
      return _DELETE_SPECIFIC_AGENTS_MESSAGE_FORMAT.format(' '.join(args.ids))
    if args.all:
      return _DELETE_ALL_AGENTS_MESSAGE
    if args.uninstall:
      return _UNINSTALL_MESSAGE
    return _LIST_AGENTS_MESSAGE

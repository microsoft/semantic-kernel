# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command to list fleet rollouts."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Generator

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.fleet import flags as fleet_flags
from googlecloudsdk.command_lib.container.fleet import util as fleet_util
from googlecloudsdk.generated_clients.apis.gkehub.v1alpha import gkehub_v1alpha_messages as alpha_messages


_EXAMPLES = """
To list all rollouts, run:

$ {command}
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List all fleet rollouts."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    """Registers flags for this command.

    Args:
      parser: Top level argument group to add new arguments.
    """

  def Run(
      self, args: parser_extensions.Namespace
  ) -> Generator[alpha_messages.Operation, None, None]:
    """Runs the rollout list command.

    Args:
      args: Flag arguments received from command line.

    Returns:
      A list of rollouts under the fleet project.
    """
    if '--format' not in args.GetSpecifiedArgNames():
      args.format = fleet_util.ROLLOUT_LIST_FORMAT

    flag_parser = fleet_flags.FleetFlagParser(
        args, release_track=self.ReleaseTrack()
    )
    fleet_client = client.FleetClient(self.ReleaseTrack())

    req = alpha_messages.GkehubProjectsLocationsRolloutsListRequest(
        parent=util.LocationResourceName(flag_parser.Project())
    )
    return fleet_client.ListRollouts(
        req, page_size=flag_parser.PageSize(), limit=flag_parser.Limit()
    )

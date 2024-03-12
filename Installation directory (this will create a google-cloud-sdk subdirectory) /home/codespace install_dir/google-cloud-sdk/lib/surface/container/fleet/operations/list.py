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
"""Command to list long-running operations."""

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
from googlecloudsdk.generated_clients.apis.gkehub.v1alpha import gkehub_v1alpha_messages as messages


_EXAMPLES = """
To list all operations in location ``us-west1'', run:

$ {command} --location=us-west1
"""


class List(base.ListCommand):
  """List long-running operations."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor) -> None:
    """Registers flags for this command.

    Args:
      parser: Top level argument group to add new arguments.
    """
    flags = fleet_flags.FleetFlags(parser)
    flags.AddLocation()

  def Run(
      self, args: parser_extensions.Namespace
  ) -> Generator[messages.Operation, None, None]:
    """Runs the operations list command.

    Long-running operations are retained no more than a week in the server.

    Args:
      args: Flag arguments received from command line.

    Returns:
      A list of long-running operations under the project.
    """
    if '--format' not in args.GetSpecifiedArgNames():
      args.format = fleet_util.OPERATION_FORMAT

    flag_parser = fleet_flags.FleetFlagParser(
        args, release_track=self.ReleaseTrack()
    )
    operation_client = client.OperationClient(self.ReleaseTrack())

    req = flag_parser.messages.GkehubProjectsLocationsOperationsListRequest(
        name=util.LocationResourceName(
            flag_parser.Project(), location=flag_parser.Location()
        )
    )
    return operation_client.List(
        req, page_size=flag_parser.PageSize(), limit=flag_parser.Limit()
    )

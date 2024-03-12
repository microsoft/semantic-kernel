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
"""Command to wait for a long-running operation to complete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.fleet import flags as fleet_flags

_EXAMPLES = """
To wait for an operation in location `us-west1` to complete, run:

$ {command} OPERATION --location=us-west1
"""


class Wait(base.Command):
  """Poll a long-running operation for completion."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Registers flags for this command."""
    flags = fleet_flags.FleetFlags(parser)
    flags.AddOperationResourceArg()

  def Run(self, args: parser_extensions.Namespace):
    """Runs the wait command."""
    flag_parser = fleet_flags.FleetFlagParser(
        args, release_track=self.ReleaseTrack()
    )
    operation_client = client.OperationClient(
        release_track=self.ReleaseTrack()
    )

    return operation_client.Wait(operation_ref=flag_parser.OperationRef())

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
"""Command to create a fleet rollout."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals
from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.command_lib.container.fleet.rollouts import flags as rollout_flags
from googlecloudsdk.core import log
from googlecloudsdk.generated_clients.apis.gkehub.v1alpha import gkehub_v1alpha_messages as alpha_messages


_EXAMPLES = """
To create a rollout, run:

$ {command} ROLLOUT
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a rollout resource."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Registers flags for this command."""
    flags = rollout_flags.RolloutFlags(parser)
    flags.AddRolloutResourceArg()
    flags.AddDisplayName()
    flags.AddLabels()
    flags.AddManagedRolloutConfig()
    flags.AddAsync()
    flags.AddFeatureUpdate()

  def Run(self, args: parser_extensions.Namespace) -> alpha_messages.Operation:
    """Runs the describe command."""
    flag_parser = rollout_flags.RolloutFlagParser(
        args, release_track=base.ReleaseTrack.ALPHA
    )

    req = alpha_messages.GkehubProjectsLocationsRolloutsCreateRequest(
        parent=util.RolloutParentName(args),
        rollout=flag_parser.Rollout(),
        rolloutId=util.RolloutId(args),
    )
    fleet_client = client.FleetClient(release_track=self.ReleaseTrack())
    operation = fleet_client.CreateRollout(req)
    rollout_ref = util.RolloutRef(args)

    if flag_parser.Async():
      log.CreatedResource(
          rollout_ref, kind='Fleet rollout', is_async=flag_parser.Async()
      )
      return operation

    operation_client = client.OperationClient(
        release_track=base.ReleaseTrack.ALPHA
    )
    completed_operation = operation_client.Wait(util.OperationRef(operation))
    log.CreatedResource(rollout_ref, kind='Fleet rollout')
    return completed_operation

# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""'notebooks runtimes stop' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.notebooks import runtimes as runtime_util
from googlecloudsdk.api_lib.notebooks import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.notebooks import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
        Request for stopping notebook runtimes.
    """,
    'EXAMPLES':
        """
    To stop a runtime, run:

        $ {command} example-runtime --location=us-central1
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Stop(base.Command):
  """Request for stopping runtimes."""

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    api_version = util.ApiVersionSelector(cls.ReleaseTrack())
    flags.AddStopRuntimeFlags(api_version, parser)

  def Run(self, args):
    release_track = self.ReleaseTrack()
    client = util.GetClient(release_track)
    messages = util.GetMessages(release_track)
    runtime_service = client.projects_locations_runtimes
    operation = runtime_service.Stop(
        runtime_util.CreateRuntimeStopRequest(args, messages))
    return runtime_util.HandleLRO(
        operation,
        args,
        runtime_service,
        release_track,
        operation_type=runtime_util.OperationType.UPDATE)


Stop.detailed_help = DETAILED_HELP

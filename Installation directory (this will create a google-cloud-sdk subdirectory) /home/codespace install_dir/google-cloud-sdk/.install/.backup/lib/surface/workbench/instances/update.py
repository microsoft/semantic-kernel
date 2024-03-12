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
"""'workbench instances update' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.workbench import instances as instance_util
from googlecloudsdk.api_lib.workbench import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.workbench import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
        Request for updating workbench instances.
    """,
    'EXAMPLES':
        """
    To update machine type for an instance, run:

        $ {command} example-instance --machine-type=n1-standard-8 --location=us-central1-a

    To update labels for an instance, run:

        $ {command} example-instance --labels=k1=v1,k2=v2 --location=us-central1-a
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Request for updating instances."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddUpdateInstanceFlags(parser)

  def Run(self, args):
    release_track = self.ReleaseTrack()
    client = util.GetClient(release_track)
    messages = util.GetMessages(release_track)
    instance_service = client.projects_locations_instances
    operation = instance_service.Patch(
        instance_util.CreateInstanceUpdateRequest(args, messages))
    return instance_util.HandleLRO(
        operation,
        args,
        instance_service,
        release_track,
        operation_type=instance_util.OperationType.UPDATE)

Update.detailed_help = DETAILED_HELP

# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""'notebooks environments delete' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.notebooks import environments as env_util
from googlecloudsdk.api_lib.notebooks import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.notebooks import flags

DETAILED_HELP = {
    'DESCRIPTION':
        """
        Request for deleting environments.
    """,
    'EXAMPLES':
        """
    To delete environment with id 'example-environment' in location
    'us-central1-a', run:

      $ {command} example-environment --location=us-central1-a
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Request for deleting environments."""

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    api_version = util.ApiVersionSelector(cls.ReleaseTrack())
    flags.AddDeleteEnvironmentFlags(api_version, parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    release_track = self.ReleaseTrack()
    client = util.GetClient(release_track)
    messages = util.GetMessages(release_track)
    environment_service = client.projects_locations_environments
    operation = environment_service.Delete(
        env_util.CreateEnvironmentDeleteRequest(args, messages))
    return env_util.HandleLRO(
        operation,
        args,
        environment_service,
        release_track,
        is_delete=True)


Delete.detailed_help = DETAILED_HELP

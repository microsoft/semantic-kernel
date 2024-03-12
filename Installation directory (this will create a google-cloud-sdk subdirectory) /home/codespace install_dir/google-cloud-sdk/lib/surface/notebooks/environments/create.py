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
"""'notebooks environments create' command."""

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
        Request for creating environments.
    """,
    'EXAMPLES':
        """
    To create an environment with id 'example-environment' in location
    'us-central1-a' using a container repository, run:

      $ {command} example-environment --location=us-central1-a --container-repository=gcr.io/deeplearning-platform-release/base-cpu --container-tag=test-tag --description=test-description --post-startup-script=gs://path-to-file/file-name --display-name=test-display-name --async

    To create an environment with id 'example-environment' in location
    'us-central1-a' using a VM Image Family, run:

      $ {command} example-environment --vm-image-project=deeplearning-platform-release --vm-image-family=caffe1-latest-cpu-experimental

    To create an environment with id 'example-environment' in location
    'us-central1-a' using a VM Image, run:

      $ {command} example-environment --location=us-central1-a --vm-image-project=deeplearning-platform-release --vm-image-name=tf2-2-1-cu101-notebooks-20200110
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Request for creating environments."""

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""
    api_version = util.ApiVersionSelector(cls.ReleaseTrack())
    flags.AddCreateEnvironmentFlags(api_version, parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    release_track = self.ReleaseTrack()
    client = util.GetClient(release_track)
    messages = util.GetMessages(release_track)
    environment_service = client.projects_locations_environments
    operation = environment_service.Create(
        env_util.CreateEnvironmentCreateRequest(args, messages))
    return env_util.HandleLRO(operation, args, environment_service,
                              release_track)


Create.detailed_help = DETAILED_HELP

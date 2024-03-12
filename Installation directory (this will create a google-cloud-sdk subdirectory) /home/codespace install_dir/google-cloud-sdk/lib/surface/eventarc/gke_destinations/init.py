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
"""Command for initializing a project for Eventarc GKE."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.eventarc import gke_destinations
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.GA)
class Init(base.Command):
  """Initialize a project for Eventarc with Cloud Run for Anthos/GKE destinations."""

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """
          To initialize a project for Eventarc with Cloud Run for Anthos/GKE destinations:

              $ {command}
          """,
  }

  def Run(self, args):
    """Run the gke command."""
    client = gke_destinations.GKEDestinationsClient(self.ReleaseTrack())
    client.InitServiceAccount()
    log.status.Print(_InitializedMessage())


def _InitializedMessage():
  project = properties.VALUES.core.project.Get(required=True)
  trigger_cmd = 'gcloud eventarc triggers create'
  return (
      'Initialized project [{}] for Cloud Run for Anthos/GKE destinations in '
      'Eventarc. Next, create a trigger via `{}`.').format(
          project, trigger_cmd)

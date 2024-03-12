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
"""Command to initialize Fleet configs for gke-fleet."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import enable_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet.features import base as feature_base
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

MCS_FEATURE_MESSAGE = (
    'Configuring Multi-Cluster Services feature.\nLearn more details at '
    'https://cloud.google.com/kubernetes-engine/docs/concepts/multi-cluster-services.\n'
)

MESH_FEATURE_MESSAGE = ('Configuring Service Mesh feature.\n'
                        'Learn more details at '
                        'https://cloud.google.com/anthos/service-mesh.\n')

MESH_ENABLE_PROMPT = 'Enable managed Service Mesh in your Fleet'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Init(feature_base.EnableCommand):
  """Initialize GKE fleets.

  This command enable Fleet API and configure following Fleet features to be
  ready for use:
    * multi-cluster-services
    * mesh
  """

  def Run(self, args):
    # Enable Fleet API
    enable_api.EnableServiceIfDisabled(self.Project(), 'gkehub.googleapis.com')

    # Enable MCS Feature
    log.status.Print(MCS_FEATURE_MESSAGE)
    self.feature_name = 'multiclusterservicediscovery'
    self.Enable(self.messages.Feature())

    # Prompt to enable Service Mesh feature.
    # If yes, enable it with 'management=AUTOMATIC'.
    enable = console_io.PromptContinue(
        message=MESH_FEATURE_MESSAGE,
        prompt_string=MESH_ENABLE_PROMPT,
        default=True,
    )
    if enable:
      enable_api.EnableServiceIfDisabled(self.Project(), 'mesh.googleapis.com')
      self.feature_name = 'servicemesh'
      feature = self.messages.Feature(
          fleetDefaultMemberConfig=self.messages
          .CommonFleetDefaultMemberConfigSpec(
              mesh=self.messages.ServiceMeshMembershipSpec(
                  management=self.messages.ServiceMeshMembershipSpec
                  .ManagementValueValuesEnum('MANAGEMENT_AUTOMATIC'))))
      self.Enable(feature)

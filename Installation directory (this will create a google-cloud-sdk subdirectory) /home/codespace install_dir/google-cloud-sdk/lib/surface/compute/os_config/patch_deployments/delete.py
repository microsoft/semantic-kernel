# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Implements command to delete the specified patch deployment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.os_config import resource_args
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete the specified patch deployment."""

  detailed_help = {
      'EXAMPLES':
          """\
      To delete the patch deployment `patch-deployment-1` in the current project,
      run:

          $ {command} patch-deployment-1
      """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddPatchDeploymentResourceArg(parser, 'to delete.')

  def Run(self, args):
    patch_deployment_ref = args.CONCEPTS.patch_deployment.Parse()
    patch_deployment_name = patch_deployment_ref.RelativeName()

    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(release_track)
    messages = osconfig_api_utils.GetClientMessages(release_track)

    request = messages.OsconfigProjectsPatchDeploymentsDeleteRequest(
        name=patch_deployment_name)

    response = client.projects_patchDeployments.Delete(request)
    log.DeletedResource(patch_deployment_name)
    return response

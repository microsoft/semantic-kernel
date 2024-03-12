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
"""Implements command to update a specified patch deployment."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.os_config import flags
from googlecloudsdk.command_lib.compute.os_config import utils as osconfig_command_utils
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Update patch deployment in a project."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Updates a patch deployment in a project. To update the patch deployment,
      you must specify a configuration file.
      """,
      'EXAMPLES':
          """\
      To update a patch deployment `patch-deployment-1` in the current project,
      run:

          $ {command} patch-deployment-1 --file=path_to_config_file
      """,
  }

  @staticmethod
  def Args(parser):
    flags.AddPatchDeploymentsUpdateFlags(
        parser, api_version='v1', release_track='')

  def Run(self, args):
    """See base class."""
    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(release_track)
    messages = osconfig_api_utils.GetClientMessages(release_track)

    (patch_deployment,
     _) = osconfig_command_utils.GetResourceAndUpdateFieldsFromFile(
         args.file, messages.PatchDeployment)

    project = properties.VALUES.core.project.GetOrFail()
    request = messages.OsconfigProjectsPatchDeploymentsPatchRequest(
        patchDeployment=patch_deployment,
        name=osconfig_command_utils.GetPatchDeploymentUriPath(
            project, args.PATCH_DEPLOYMENT_ID),
        updateMask=None,
    )
    service = client.projects_patchDeployments

    return service.Patch(request)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update a patch deployment in a project."""

  @staticmethod
  def Args(parser):
    flags.AddPatchDeploymentsUpdateFlags(
        parser, api_version='v1beta', release_track='beta')

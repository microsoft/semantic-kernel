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

"""Command to update an Anthos Config Controller instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.krmapihosting import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.anthos.config.controller import flags
from googlecloudsdk.command_lib.anthos.config.controller import utils


# TODO(b/234495254): promote the update command to GA
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update an Anthos Config Controller instance."""
  _API_VERSION = "v1alpha1"

  detailed_help = {
      "DESCRIPTION":
          "Update an Anthos Config Controller instance.",
      "EXAMPLES":
          """
          To update the master authorized network for an existing Anthos Config
          Controller instance, run:

            $ {command} sample-instance --man-block=MAN_BLOCK

          """
  }

  @staticmethod
  def Args(parser):
    utils.AddInstanceResourceArg(parser, Update._API_VERSION)
    flags.AddAsyncFlag(parser)
    flags.AddExperimentalFeaturesFlag(parser)
    flags.AddManBlockFlag(parser)

  def Run(self, args):
    op = util.GetClientInstance(
        api_version=self._API_VERSION).projects_locations_krmApiHosts.Patch(
            utils.PatchRequest(args))

    if args.async_:
      return utils.AsyncLog(op)

    return util.WaitForCreateKrmApiHostOperation(
        op,
        progress_message="Waiting for operation [{}] to complete".format(
            op.name))

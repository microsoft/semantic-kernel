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
"""The gcloud run regions group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import platforms


class Regions(base.Group):
  """View available Cloud Run (fully managed) regions."""

  @staticmethod
  def Args(parser):
    """Adds --platform and the various related args."""
    flags.AddPlatformArg(parser, managed_only=True)

  def Filter(self, context, args):
    """Runs before command.Run and validates platform with passed args."""
    # Ensures the run/platform property is either unset or set to `managed` and
    # all other passed args are valid for this platform and release track.
    flags.GetAndValidatePlatform(
        args, self.ReleaseTrack(), flags.Product.RUN)
    self._CheckPlatform()
    return context

  def _CheckPlatform(self):
    platform = platforms.GetPlatform()
    if platform is not None and platform != platforms.PLATFORM_MANAGED:
      raise exceptions.PlatformError(
          'This command group only supports listing regions for '
          'Cloud Run (fully managed).')

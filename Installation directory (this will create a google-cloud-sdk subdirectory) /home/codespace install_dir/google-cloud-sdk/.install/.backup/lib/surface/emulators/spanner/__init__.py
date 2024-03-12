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
"""The gcloud emulators spanner group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.emulators import spanner_util
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms


class UnsupportedPlatformError(exceptions.Error):
  pass


class DockerNotFoundError(exceptions.Error):
  pass


def _RequireDockerInstalled():
  docker_path = files.FindExecutableOnPath('docker')
  if not docker_path:
    raise DockerNotFoundError(
        'To use the Cloud Spanner Emulator on {platform}, '
        'docker must be installed on your system PATH'.format(
            platform=platforms.OperatingSystem.Current().name))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Spanner(base.Group):
  """Manage your local Spanner emulator.

  This set of commands allows you to start and use a local Spanner emulator.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To start a local Cloud Spanner emulator, run:

            $ {command} start
          """,
  }

  # Override
  def Filter(self, context, args):
    current_os = platforms.OperatingSystem.Current()
    if current_os is platforms.OperatingSystem.LINUX:
      util.EnsureComponentIsInstalled(
          spanner_util.SPANNER_EMULATOR_COMPONENT_ID,
          spanner_util.SPANNER_EMULATOR_TITLE)
    else:
      _RequireDockerInstalled()

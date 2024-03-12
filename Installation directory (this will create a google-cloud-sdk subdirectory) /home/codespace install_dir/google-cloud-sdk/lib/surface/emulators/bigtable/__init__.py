# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""The gcloud bigtable emulator group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.emulators import bigtable_util
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import platforms


class UnsupportedPlatformError(exceptions.Error):
  pass


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Bigtable(base.Group):
  """Manage your local Bigtable emulator.

  This set of commands allows you to start and use a local Bigtable emulator.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To start a local Bigtable emulator, run:

            $ {command} start
          """,
  }

  # Override
  def Filter(self, context, args):
    util.EnsureComponentIsInstalled(bigtable_util.BIGTABLE,
                                    bigtable_util.BIGTABLE_TITLE)

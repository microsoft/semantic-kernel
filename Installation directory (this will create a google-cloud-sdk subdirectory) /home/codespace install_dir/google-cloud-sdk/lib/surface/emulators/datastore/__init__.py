# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""The gcloud datastore emulator group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.emulators import datastore_util
from googlecloudsdk.command_lib.emulators import flags
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.command_lib.util import java


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Datastore(base.Group):
  """Manage your local datastore emulator.

  This set of commands allows you to start and use a local datastore emulator.
  """

  detailed_help = {
      'EXAMPLES': """\
          To start a local datastore emulator, run:

            $ {command} start
          """,
  }

  @staticmethod
  def Args(parser):
    flags.AddDataDirFlag(parser, datastore_util.DATASTORE)

  def Filter(self, context, args):
    java.RequireJavaInstalled(datastore_util.DATASTORE_TITLE, min_version=8)
    util.EnsureComponentIsInstalled('cloud-datastore-emulator',
                                    datastore_util.DATASTORE_TITLE)
    if not args.data_dir:
      args.data_dir = datastore_util.GetDataDir()

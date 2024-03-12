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
"""The gcloud firestore emulator group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.emulators import firestore_util
from googlecloudsdk.command_lib.emulators import flags
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.command_lib.util import java


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Firestore(base.Group):
  """Manage your local Firestore emulator.

  This set of commands allows you to start and use a local Firestore emulator.
  """

  detailed_help = {
      'EXAMPLES':
          """\
          To start the local Firestore emulator, run:

            $ {command} start
          """,
  }

  def Filter(self, context, args):
    java.RequireJavaInstalled(firestore_util.FIRESTORE_TITLE, min_version=8)
    util.EnsureComponentIsInstalled('cloud-firestore-emulator',
                                    firestore_util.FIRESTORE_TITLE)

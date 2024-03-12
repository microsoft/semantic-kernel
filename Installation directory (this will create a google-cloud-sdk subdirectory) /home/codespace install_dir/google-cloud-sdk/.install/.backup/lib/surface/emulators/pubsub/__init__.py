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
"""The gcloud pubsub emulator group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.emulators import flags
from googlecloudsdk.command_lib.emulators import pubsub_util
from googlecloudsdk.command_lib.emulators import util
from googlecloudsdk.command_lib.util import java


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class PubSub(base.Group):
  """Manage your local pubsub emulator.

  This set of commands allows you to start and use a local Pub/Sub emulator to
  produce a local emulation of your production Google Pub/Sub environment. In
  addition to having Java JRE (of version 7 or higher) installed and an
  application built with Google Cloud Client libraries, you must have your
  emulator configured (have it started with environment variables set) for
  it to run successfully. The underlying commands help to set up this
  configuration.

  To stop the emulator, press Ctrl+C.

  For a more comprehensive overview of Pub/Sub, see
  https://cloud.google.com/pubsub/docs/overview. For Pub/Sub emulator specific
  documentation, see https://cloud.google.com/pubsub/docs/emulator
  """

  detailed_help = {
      'EXAMPLES': """\
          To start a local pubsub emulator with the default directory for
          configuration data, run:

            $ {command} start

          After starting the emulator, if your application and
          emulator run on the same machine, set environment variables
          automatically by running:

            $ {command} env-init

          If you're running your emulator on a different machine, run the above
          command and use its resulting output to set the environment variables
          on the machine that runs your application. This might look like:

            $ export PUBSUB_EMULATOR_HOST=localhost:8538
            $ export PUBSUB_PROJECT_ID=my-project-id

          Your emulator is now ready for use.
          """,
  }

  @staticmethod
  def Args(parser):
    flags.AddDataDirFlag(parser, pubsub_util.PUBSUB)

  # Override
  def Filter(self, context, args):
    java.RequireJavaInstalled(pubsub_util.PUBSUB_TITLE)
    util.EnsureComponentIsInstalled('pubsub-emulator', pubsub_util.PUBSUB_TITLE)

    if not args.data_dir:
      args.data_dir = pubsub_util.GetDataDir()

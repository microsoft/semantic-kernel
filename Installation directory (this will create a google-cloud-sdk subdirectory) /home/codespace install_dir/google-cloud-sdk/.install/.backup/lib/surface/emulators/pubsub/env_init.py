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
"""gcloud pubsub emulator env_init command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.emulators import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class EnvInit(base.Command):
  """Print the commands required to export pubsub emulator's env variables.

  After starting the emulator, you need to set environment variables so that
  your application connects to the emulator instead of the production
  environment. Environment variables need to be set each time you start the
  emulator. The environment variables depend on dynamically assigned port
  numbers that could change when you restart the emulator.
  """

  detailed_help = {
      'EXAMPLES': """
To print the env variables exports for a pubsub emulator, run:

  $ {command} --data-dir=DATA-DIR

For a detailed walkthrough of setting Pub/Sub emulator environment
variables, see https://cloud.google.com/pubsub/docs/emulator#env.
""",
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('config[export]')

  def Run(self, args):
    return util.ReadEnvYaml(args.data_dir)

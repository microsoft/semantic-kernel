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
"""Command to deploy a Kuberun Component in development mode."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberun_command

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To deploy a Component named ``COMPONENT'' in development mode to the
        Environment set in gcloud config, run:

            $ {command} COMPONENT

        To deploy a Component named ``COMPONENT'' in development mode to
        Environment ``ENV'', run:

            $ {command} COMPONENT --environment=ENV

        To delete a Component named ``COMPONENT'' in development mode from the
        Environment set in gcloud config, run:

            $ {command} COMPONENT --delete

        To delete a Component named ``COMPONENT'' in development mode from
        Environment ``ENV'', run:

            $ {command} COMPONENT --delete --environment=ENV
        """,
}


def _DeleteFlag():
  return flags.BasicFlag(
      '--delete',
      help='Delete the deployed Component from the active Environment. This can only be used to delete Components deployed in development mode. This does not modify or remove any configuration or references to the component.',
      required=False)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Dev(kuberun_command.KubeRunCommand, base.CreateCommand):
  """Deploy a Component in development mode."""

  detailed_help = _DETAILED_HELP
  flags = [flags.EnvironmentFlag(), _DeleteFlag()]

  @classmethod
  def Args(cls, parser):
    super(Dev, cls).Args(parser)
    parser.add_argument('component', help='Name of the component.')

  def Command(self):
    return ['components', 'dev']

  def BuildKubeRunArgs(self, args):
    return [args.component] + super(Dev, self).BuildKubeRunArgs(args)

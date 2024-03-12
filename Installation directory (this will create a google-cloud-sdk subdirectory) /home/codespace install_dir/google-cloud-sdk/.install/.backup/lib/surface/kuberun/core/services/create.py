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
"""Creates a new KubeRun service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberun_command

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To create a new KubeRun service in the default namespace, run:

            $ {command} SERVICE --image=IMAGE

        To create a new KubeRun service in a specific namespace ``NAMESPACE'',
        run:

            $ {command} SERVICE --image=IMAGE --namespace=NAMESPACE
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(kuberun_command.KubeRunCommand, base.CreateCommand):
  """Creates a new KubeRun service."""

  detailed_help = _DETAILED_HELP
  flags = [
      flags.ClusterConnectionFlags(),
      flags.CommonServiceFlags(is_create=True),
      flags.AsyncFlag(),
  ]

  @classmethod
  def Args(cls, parser):
    super(Create, cls).Args(parser)
    parser.add_argument(
        'service',
        help='ID of the service or fully qualified identifier for the service.')

  def BuildKubeRunArgs(self, args):
    return [args.service] + super(Create, self).BuildKubeRunArgs(args)

  def Command(self):
    return ['core', 'services', 'create']

  def SuccessResult(self, out, args):
    return json.loads(out)

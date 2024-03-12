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
"""Deploy a KubeRun service."""

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
        To update one or more env vars on a service in the default namespace,
        run:

            $ {command} SERVICE --update-env-vars=KEY1=VALUE1,KEY2=VALUE2

        To update one or more env vars on a service in a specific namespace
        ``NAMESPACE'', run:

            $ {command} SERVICE --namespace=NAMESPACE --update-env-vars=KEY1=VALUE1,KEY2=VALUE2
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(kuberun_command.KubeRunCommand, base.UpdateCommand):
  """Updates a KubeRun service."""

  detailed_help = _DETAILED_HELP
  flags = [
      flags.ClusterConnectionFlags(),
      flags.CommonServiceFlags(),
      flags.CreateIfMissingFlag(),
      flags.NoTrafficFlag(),
      flags.AsyncFlag()
  ]

  @classmethod
  def Args(cls, parser):
    super(Update, cls).Args(parser)
    parser.add_argument(
        'service',
        help='ID of the service or fully qualified identifier for the service.')

  def BuildKubeRunArgs(self, args):
    return [args.service] + super(Update, self).BuildKubeRunArgs(args)

  def Command(self):
    return ['core', 'services', 'update']

  def SuccessResult(self, out, args):
    return json.loads(out)

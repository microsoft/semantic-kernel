# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Update a backend binding of a KubeRun service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.kuberun import backendbinding
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.core import exceptions

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To update the maximum number of requests per second ``MAX_RATE'' for
        the backend service in the default namespace, run:

            $ {command} BACKEND_BINDING --max-rate=MAX_RATE

        To update the maximum number of requests per second ``MAX_RATE'' for
        the backend service in a specific namespace ``NAMESPACE'', run:

            $ {command} BACKEND_BINDING --namespace=NAMESPACE --max-rate=MAX_RATE
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(kuberun_command.KubeRunCommand):
  """Updates a backend binding."""

  detailed_help = _DETAILED_HELP
  flags = [
      flags.NamespaceFlag(),
      flags.ClusterConnectionFlags(),
      flags.MaxRateFlag(),
  ]

  @classmethod
  def Args(cls, parser):
    super(Update, cls).Args(parser)
    parser.add_argument(
        'backend_binding',
        help="""Name of the backend binding to update. This name
        is the same as the Compute Engine backend service.""")
    parser.display_info.AddFormat("""table(
        name:label=NAME,
        service:label=SERVICE,
        ready:label=READY)""")

  def BuildKubeRunArgs(self, args):
    return [args.backend_binding] + super(Update, self).BuildKubeRunArgs(args)

  def Command(self):
    return ['core', 'backend-bindings', 'update']

  def SuccessResult(self, out, args):
    if out:
      return backendbinding.BackendBinding(json.loads(out))
    else:
      raise exceptions.Error('Could not update backend binding [{}]'.format(
          args.backend_binding))

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
"""Create a backend binding.

Binds a Compute Engine backend service to your KubeRun service.
"""

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
        To bind a KubeRun service ``SERVICE'' in the default namespace
        to a Compute Engine backend service ``BACKEND_SERVICE'' with a maximum
        requests per second limit ``MAX_RATE'', run:

            $ {command} --service=SERVICE --backend-service=BACKEND_SERVICE --max-rate=MAX_RATE

        To bind a KubeRun service ``SERVICE'' in a specific namespace
        ``NAMESPACE'' to a Compute Engine backend service ``BACKEND_SERVICE''
        with a maximum requests per second limit ``MAX_RATE'', run:

            $ {command} --service=SERVICE --namespace=NAMESPACE --backend-service=BACKEND_SERVICE --max-rate=MAX_RATE
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(kuberun_command.KubeRunCommand):
  """Creates a backend binding."""

  detailed_help = _DETAILED_HELP
  flags = [
      flags.NamespaceFlag(),
      flags.ClusterConnectionFlags(),
      flags.MaxRateFlag(True),
  ]

  @classmethod
  def Args(cls, parser):
    super(Create, cls).Args(parser)
    parser.add_argument(
        '--service',
        help='Name of the KubeRun service to bind to a Compute Engine backend service.',
        required=True)
    parser.add_argument(
        '--backend-service',
        help='Name of the Compute Engine backend service to bind to the KubeRun service.',
        required=True)
    parser.display_info.AddFormat("""table(
        name:label=NAME,
        service:label=SERVICE,
        ready:label=READY)""")

  def BuildKubeRunArgs(self, args):
    return [
        '--service', args.service, '--backend-service', args.backend_service,
    ] + super(Create, self).BuildKubeRunArgs(args)

  def Command(self):
    return ['core', 'backend-bindings', 'create']

  def SuccessResult(self, out, args):
    if out:
      return backendbinding.BackendBinding(json.loads(out))
    else:
      raise exceptions.Error(
          'Could not create backend binding [{}] for service [{}]'.format(
              args.domain, args.service))

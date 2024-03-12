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
"""Deletes the backend binding.

This removes the binding between the Compute
   Engine backend service and your KubeRun service.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To delete a backend binding ``BACKEND_BINDING'' in the default
        namespace, run:

            $ {command} BACKEND_BINDING

        To delete a backend binding ``BACKEND_BINDING'' in a specific namespace
        ``NAMESPACE'', run:

            $ {command} BACKEND_BINDING --namespace=NAMESPACE
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(kuberun_command.KubeRunCommand, base.DeleteCommand):
  """Deletes a backend binding."""

  detailed_help = _DETAILED_HELP
  flags = [flags.NamespaceFlag(), flags.ClusterConnectionFlags()]

  @classmethod
  def Args(cls, parser):
    super(Delete, cls).Args(parser)
    parser.add_argument(
        'backend_binding',
        help="""Name of the backend binding to delete. This name
        is the same as the Compute Engine backend service.""")

  def BuildKubeRunArgs(self, args):
    return [args.backend_binding] + super(Delete, self).BuildKubeRunArgs(args)

  def Command(self):
    return ['core', 'backend-bindings', 'delete']

  def SuccessResult(self, out, args):
    log.DeletedResource(args.backend_binding, 'backend binding')

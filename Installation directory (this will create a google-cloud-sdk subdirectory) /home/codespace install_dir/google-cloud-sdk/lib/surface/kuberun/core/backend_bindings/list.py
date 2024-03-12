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
"""Command to list backend bindings of a KubeRun cluster."""
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
        To show all backend bindings in the default namespace, run:

            $ {command}

        To show all backend bindings in namespace ``NAMESPACE'', run:

            $ {command} --namespace=NAMESPACE

        To show all backend bindings from all namespaces, run:

            $ {command} --all-namespaces
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(kuberun_command.KubeRunCommand, base.ListCommand):
  """Lists backend bindings in a KubeRun cluster."""

  detailed_help = _DETAILED_HELP
  flags = [flags.NamespaceFlagGroup(), flags.ClusterConnectionFlags()]

  @classmethod
  def Args(cls, parser):
    super(List, cls).Args(parser)
    base.ListCommand._Flags(parser)
    base.URI_FLAG.RemoveFromParser(parser)

    parser.display_info.AddFormat("""table(
        namespace:label=NAMESPACE,
        name:label=BACKEND_SERVICE,
        service:label=SERVICE,
        ready:label=READY)""")

  def Command(self):
    return ['core', 'backend-bindings', 'list']

  def SuccessResult(self, out, args):
    if out:
      json_object = json.loads(out)
      return [backendbinding.BackendBinding(x) for x in json_object]
    else:
      raise exceptions.Error('Cannot list backend bindings')

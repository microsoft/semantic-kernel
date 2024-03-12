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
"""Command to list KubeRun services in a Kubernetes cluster."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.kuberun import structuredout
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import k8s_object_printer
from googlecloudsdk.command_lib.kuberun import kubernetes_consts
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.command_lib.kuberun import pretty_print
from googlecloudsdk.core import exceptions

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To list the KubeRun services in the default namespace, run:

            $ {command}

        To list the KubeRun services in a specific namespace ``NAMESPACE'', run:

            $ {command} --namespace=NAMESPACE

        To list the KubeRun services from all namespaces, run:

            $ {command} --all-namespaces
        """,
}


_ALIAS_KEY_LAST_DEPLOYED_AT = 'lastDeployedAt'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(kuberun_command.KubeRunCommand, base.ListCommand):
  """Lists services in a KubeRun cluster."""

  detailed_help = _DETAILED_HELP
  flags = [
      flags.NamespaceFlagGroup(),
      flags.ClusterConnectionFlags(),
      flags.ServiceListServiceFlag(),
  ]

  @classmethod
  def Args(cls, parser):
    super(List, cls).Args(parser)
    base.ListCommand._Flags(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    pretty_print.AddReadyColumnTransform(parser)
    columns = [
        pretty_print.GetReadyColumn(),
        'metadata.name:label=SERVICE',
        'metadata.namespace:label=NAMESPACE',
        'status.url:label=URL',
        ('metadata.annotations["%s"]'
         ':label="LAST DEPLOYED BY":alias=LAST_DEPLOYED_BY' %
         kubernetes_consts.ANN_LAST_MODIFIER),
        ('aliases.%s:label="LAST DEPLOYED AT"'
         ':alias=LAST_DEPLOYED_AT' % _ALIAS_KEY_LAST_DEPLOYED_AT),
    ]
    parser.display_info.AddFormat('table({})'.format(','.join(columns)))

  def Command(self):
    return ['core', 'services', 'list']

  def SuccessResult(self, out, args):
    if out:
      return [_AddAliases(x) for x in json.loads(out)]
    else:
      raise exceptions.Error('Cannot list services')


def _AddAliases(service):
  """Add aliases to embedded fields displayed in the output.

  Adds aliases to embedded fields that would require a more complex expression
  to be shown in the output table.

  Args:
   service: service unmarshalled from json

  Returns:
   dictionary with aliases representing the service from the input
  """
  d = structuredout.DictWithAliases(service)
  ready_cond = k8s_object_printer.ReadyConditionFromDict(service)
  if ready_cond is not None:
    d.AddAlias(
        pretty_print.READY_COLUMN_ALIAS_KEY,
        ready_cond.get(kubernetes_consts.FIELD_STATUS,
                       kubernetes_consts.VAL_UNKNOWN))
    d.AddAlias(_ALIAS_KEY_LAST_DEPLOYED_AT,
               ready_cond.get(kubernetes_consts.FIELD_LAST_TRANSITION_TIME))
  return d

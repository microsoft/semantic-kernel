# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command to list domain mappings of a KubeRun cluster."""
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
        To list the domain mappings in the default namespace, run:

            $ {command}

        To list the domain mappings in a specific namespace ``NAMESPACE'', run:

            $ {command} --namespace=NAMESPACE

        To list the domain mappings from all namespaces, run:

            $ {command} --all-namespaces
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(kuberun_command.KubeRunCommand, base.ListCommand):
  """Lists domain mappings in a KubeRun cluster."""

  detailed_help = _DETAILED_HELP
  flags = [flags.NamespaceFlagGroup(), flags.ClusterConnectionFlags()]

  @classmethod
  def Args(cls, parser):
    super(List, cls).Args(parser)
    base.ListCommand._Flags(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    pretty_print.AddReadyColumnTransform(parser)
    parser.display_info.AddFormat("""table(
        {ready_column},
        metadata.name:label=DOMAIN,
        spec.routeName:label=SERVICE)""".format(
            ready_column=pretty_print.GetReadyColumn()))

  def Command(self):
    return ['core', 'domain-mappings', 'list']

  def SuccessResult(self, out, args):
    if out:
      return [_AddAliases(x) for x in json.loads(out)]
    else:
      raise exceptions.Error('Cannot list domain mappings')


def _AddAliases(mapping):
  """Add aliases to embedded fields displayed in the output.

  Adds aliases to embedded fields that would require a more complex expression
  to be shown in the output table.

  Args:
   mapping: a domain mapping unmarshalled from json

  Returns:
   dictionary with aliases representing the domain mapping from the input
  """
  d = structuredout.DictWithAliases(**mapping)
  ready_cond = k8s_object_printer.ReadyConditionFromDict(mapping)
  if ready_cond is not None:
    d.AddAlias(
        pretty_print.READY_COLUMN_ALIAS_KEY,
        ready_cond.get(kubernetes_consts.FIELD_STATUS,
                       kubernetes_consts.VAL_UNKNOWN))
  return d

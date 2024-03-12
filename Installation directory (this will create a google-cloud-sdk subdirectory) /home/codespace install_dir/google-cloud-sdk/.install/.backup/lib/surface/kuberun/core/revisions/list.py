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
"""Command to list KubeRun revisions in a Kubernetes cluster."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.kuberun import revision
from googlecloudsdk.api_lib.kuberun import structuredout
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import flags
from googlecloudsdk.command_lib.kuberun import k8s_object_printer
from googlecloudsdk.command_lib.kuberun import kubernetes_consts
from googlecloudsdk.command_lib.kuberun import kuberun_command
from googlecloudsdk.command_lib.kuberun import pretty_print
from googlecloudsdk.command_lib.kuberun import revision_printer
from googlecloudsdk.core import exceptions

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To show all KubeRun revisions in the default namespace, run:

            $ {command}

        To show all KubeRun revisions in a specific namespace ``NAMESPACE'', run:

            $ {command} --namespace=NAMESPACE

        To show all KubeRun revisions from all namespaces, run:

            $ {command} --all-namespaces
        """,
}


# lower-case to conform with convention for keys in the alias dictionary
_ALIAS_KEY_ACTIVE = 'active'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(kuberun_command.KubeRunCommand, base.ListCommand):
  """Lists revisions in a KubeRun cluster."""

  detailed_help = _DETAILED_HELP
  flags = [
      flags.NamespaceFlagGroup(),
      flags.ClusterConnectionFlags(),
      flags.RevisionListServiceFlag()
  ]

  @classmethod
  def Args(cls, parser):
    super(List, cls).Args(parser)
    base.ListCommand._Flags(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    pretty_print.AddReadyColumnTransform(parser)
    columns = [
        pretty_print.GetReadyColumn(),
        'metadata.name:label=REVISION',
        'aliases.%s.yesno(yes="yes", no="")' % _ALIAS_KEY_ACTIVE,
        'metadata.labels["%s"]:label=SERVICE:sort=1' % revision.SERVICE_LABEL,
        ('metadata.creationTimestamp.date("%Y-%m-%d %H:%M:%S %Z"):'
         'label=DEPLOYED:sort=2:reverse'),
        ('metadata.annotations["%s"]:label="DEPLOYED BY"' %
         revision.AUTHOR_ANNOTATION)
    ]
    parser.display_info.AddFormat('table({})'.format(','.join(columns)))

  def Command(self):
    return ['core', 'revisions', 'list']

  def SuccessResult(self, out, args):
    if out:
      return [_AddAliases(x) for x in json.loads(out)]
    else:
      raise exceptions.Error('Cannot list revisions')


def _AddAliases(rev):
  """Add aliases to embedded fields displayed in the output.

  Adds aliases to embedded fields that would require a more complex expression
  to be shown in the output table.

  Args:
   rev: revision unmarshalled from json

  Returns:
   dictionary with aliases representing the service from the input
  """
  d = structuredout.DictWithAliases(**rev)
  ready_cond = k8s_object_printer.ReadyConditionFromDict(rev)
  if ready_cond is not None:
    d.AddAlias(
        pretty_print.READY_COLUMN_ALIAS_KEY,
        ready_cond.get(kubernetes_consts.FIELD_STATUS,
                       kubernetes_consts.VAL_UNKNOWN))
    d.AddAlias(_ALIAS_KEY_ACTIVE,
               revision_printer.Active(rev))
  return d

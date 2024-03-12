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
"""Command to list available Kuberun Development Kits."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.api_lib.kuberun import structuredout
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.kuberun import kuberun_command

_DETAILED_HELP = {
    'EXAMPLES':
        """
        To show all available Environments, run:

            $ {command}
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(kuberun_command.KubeRunCommand, base.ListCommand):
  """Lists available Development Kits."""

  detailed_help = _DETAILED_HELP
  flags = []

  @classmethod
  def Args(cls, parser):
    super(List, cls).Args(parser)
    base.ListCommand._Flags(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    columns = [
        'name',
        ('spec.firstof(cluster, kubeconfig).extract(namespace).flatten():'
         'label=NAMESPACE'),
        'aliases.target_config.list()',
        'source']
    parser.display_info.AddFormat('table({})'.format(','.join(columns)))

  def Command(self):
    return ['environments', 'list']

  def SuccessResult(self, out, args):
    if not out:
      return []
    return [_AddAliases(item) for item in json.loads(out)]


def _AddAliases(data):
  """Adds aliases to the data which are used in the list output.

  This adds a single alias key, which is "target_config". The target_config
  is the spec filtered down to two keys, cluster and kubeconfig, which represent
  the cluster configuration for the environment. Additionally, the namespace
  has been removed from this config in the alias because the namespace is
  displayed in it's own column.

  Args:
    data: The deserialized json data for a single environment

  Returns:
    A DictWithAliases which includes aliases.target_config.
  """
  spec = data.get('spec', {})
  target_config = {}

  if 'cluster' in spec:
    target_config['cluster'] = _RemoveNamespaceAndSerialize(spec['cluster'])
  elif 'kubeconfig' in spec:
    target_config['kubeconfig'] = _RemoveNamespaceAndSerialize(
        spec['kubeconfig'])
  return structuredout.DictWithAliases(data,
                                       aliases={'target_config': target_config})


def _RemoveNamespaceAndSerialize(data):
  return json.dumps(
      {k: v for k, v in data.items() if k != 'namespace'}, sort_keys=True)

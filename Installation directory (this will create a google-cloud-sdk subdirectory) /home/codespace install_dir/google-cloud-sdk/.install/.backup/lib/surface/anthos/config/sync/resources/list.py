# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""List ConfigSync Managed Resources."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.anthos.config.sync.resources import list as r_list
from googlecloudsdk.core import properties

list_format = """\
    table[box](
      "cluster_name",
      "group",
      "kind",
      "namespace",
      "name",
      "status",
      "condition"
    )"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.Command):
  """List resources and their status that are synced by Config Sync."""

  detailed_help = {
      'PREREQUISITES':
          """
      Please setup Connect Gateway in order to use this command with non-GKE
      registered clusters. The instructions can be found at
      https://cloud.google.com/anthos/multicluster-management/gateway/setup.
      """,
      'EXAMPLES':
          """
      To list all managed resources in the current project, run:

          $ {command} list

      To list all managed resources in a specific Config Controller cluster, run:

          $ {command} list --cluster=<CLUSTER>

      To list managed resources from a Git repo synced by Config Sync across
      multiple clusters, run:

          $ {command} list --sync-name=root-sync --sync-namespace=config-management-system

      To list managed resources from a Git repo synced by Config Sync from a
      specific cluster, run:

          $ {command} list --sync-namespace=<NAMESPACE> --sync-name=repo-sync --cluster=<CLUSTER>
    """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(list_format)
    parser.add_argument(
        '--sync-name',
        required=False,
        help='Name of the RootSync or RepoSync CR to sync a repository.')
    parser.add_argument(
        '--sync-namespace',
        required=False,
        help='Namespace of the RootSync or RepoSync CR to sync a repository.')
    parser.add_argument(
        '--cluster',
        required=False,
        help='The cluster name or the membership name that a repository is synced to.'
    )
    parser.add_argument(
        '--membership',
        required=False,
        help='The membership name that the listed Config Sync repos ' +
        'are synced to. A membership is for a registered cluster to a ' +
        'fleet. It supports a single membership or multiple memberships ' +
        'with the format membership1,membership2 or membership*.')

  def Run(self, args):
    project_id = properties.VALUES.core.project.GetOrFail()
    return r_list.ListResources(project_id, args.sync_name, args.sync_namespace,
                                args.cluster, args.membership)

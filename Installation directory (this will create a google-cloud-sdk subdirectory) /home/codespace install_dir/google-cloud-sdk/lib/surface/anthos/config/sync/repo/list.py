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
"""List ConfigSync Repos package."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.anthos.config.sync.repo import status as statusutils
from googlecloudsdk.core import properties

list_format = """\
    table[box](
      "source",
      "total",
      "synced",
      "pending",
      "error",
      "stalled",
      "reconciling"
    )"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.Command):
  """List repositories and their status that are synced by Config Sync."""

  detailed_help = {
      'PREREQUISITES':
          """
       Please setup Connect Gateway if your registered clusters are non-GKE
       clusters. The instructions can be found at
       https://cloud.google.com/anthos/multicluster-management/gateway/setup.
       For registered clusters that are GKE clusters, no need to setup the Connect
       Gateway.
          """,
      'EXAMPLES':
          """
      To list all repositories synced to the registered clusters or to
      the Config Controller cluster in the current project:

          $ {command} list

      To list all repositories synced to the registered clusters to the
      fleet hosted in the current project:

          $ {command} list --targets=fleet-clusters

      To list all repositories synced to the Config Controller cluster
      in the current project:

          $ {command} list --targets=fleet-clusters

      To list repositories in namespace <NAMESPACE> synced
      to the registered clusters to the current fleet:

          $ {command} list --targets=fleet-clusters --namespace=<NAMESPACE>

      To list repositories synced to the registered clusters
      that are in a "pending" status:

          $ {command} list --targets=fleet-clusters --status=pending
      """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(list_format)
    parser.add_argument(
        '--status',
        required=False,
        default='all',
        help='The status for the Config Sync repos that the list command should include. The supported values are all, synced, pending, error, stalled.'
    )
    parser.add_argument(
        '--namespace',
        required=False,
        help='The namespace that the listed Config Sync repos are from.' +
        'It supports a single namespace or multiple namespaces with the format namespace1,namespace2 or namespace*.'
    )
    parser.add_argument(
        '--membership',
        required=False,
        help='The membership name that the listed Config Sync repos are synced to.'
        + 'A membership is for a registered cluster to a fleet. It supports' +
        'a single membership or multiple memberships with the format membership1,membership2 or membership*.'
        + 'It can only be specified when --targets=fleet-clusters is used.')
    parser.add_argument(
        '--selector',
        required=False,
        help='The label selector that the listed Config Sync repos should match. It supports the selector with the format key1=value1,key2=value2'
    )
    parser.add_argument(
        '--targets',
        default='all',
        required=False,
        help='The targets of the clusters. It must be one of the three values: all, fleet-clusters, config-controller.'
    )

  def Run(self, args):
    project_id = properties.VALUES.core.project.GetOrFail()
    return statusutils.ListRepos(project_id, args.status, args.namespace,
                                 args.membership, args.selector, args.targets)

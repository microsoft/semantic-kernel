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
"""Describe ConfigSync Repo package."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.anthos.config.sync.repo import status
from googlecloudsdk.core import properties

describe_format = (
    "multi(detailed_status:format='json', "
    "managed_resources:format='table[box,title=managed_resources](group:sort=2,kind:sort=3,name:sort=4,namespace:sort=1,status,conditions)')"
)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.Command):
  """Describe a repository that is synced across clusters in Config Sync."""

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
      To describe a repository with source as <SOURCE>
      where the source is from the output of the list command:

          $ {command} describe --source=<SOURCE>

      To describe the repository that is synced by a RootSync or RepoSync CR
      in the namespace <NAMESPACE> with the name <NAME>:

          $ {command} describe --sync-namespace=<NAMESPACE> --sync-name=<NAME>

      To describe the repository that is synced by a RootSync or RepoSync CR
      in the namespace <NAMESPACE> with the name <NAME> from a specific cluster <CLUSTER>:

          $ {command} describe --sync-namespace=<NAMESPACE> --sync-name=<NAME> --cluster=<CLUSTER>

      To describe a repository with source as <SOURCE> and list all the
      managed resources from this repositry:

          $ {command} describe --source=<SOURCE> --managed-resources=all

      To describe a repository with source as <SOURCE> and only print the
      failed managed resources from this repositry:

          $ {command} describe --source=<SOURCE> --managed-resources=failed --format="multi(statuses:format=none,managed_resources:format='table[box](group,kind,name,namespace,conditions)')"

      """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(describe_format)
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
        '--source',
        required=False,
        help='The source of the repository. It should be copied from' +
        'the output of the listing repo command.')
    parser.add_argument(
        '--managed-resources',
        default='failed',
        required=False,
        help='Specify the managed resource status that should be' +
        'included in the describe output.' + 'The supported values are' +
        'all, current, failed, inprogress, notfound, unknown.')

  def Run(self, args):
    project_id = properties.VALUES.core.project.GetOrFail()
    return status.DescribeRepo(project_id, args.sync_name, args.sync_namespace,
                               args.source, args.cluster,
                               args.managed_resources)

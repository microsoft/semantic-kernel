# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""bigtable backups list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import resources


def _GetUriFunction(resource):
  return resources.REGISTRY.ParseRelativeName(
      resource.name,
      collection='bigtableadmin.projects.instances.clusters.backups').SelfLink()


def _TransformCluster(resource):
  """Get Cluster ID from backup name."""
  # backup name is in the format of:
  # projects/{}/instances/{}/clusters/{}/backups/{}
  backup_name = resource.get('name')
  results = backup_name.split('/')
  cluster_name = results[-3]
  return cluster_name


class ListBackups(base.ListCommand):
  """List existing Bigtable backups."""

  detailed_help = {
      'DESCRIPTION':
          textwrap.dedent("""
          List existing Bigtable backups.
          """),
      'EXAMPLES':
          textwrap.dedent("""
          To list all backups in an instance, run:

            $ {command} --instance=INSTANCE_NAME

          To list all backups in a cluster, run:

            $ {command} --instance=INSTANCE_NAME --cluster=CLUSTER_NAME
          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddBackupResourceArg(parser, 'to list backups for')
    parser.display_info.AddFormat("""
          table(
            name.basename():sort=1:label=NAME,
            cluster():label=CLUSTER,
            sourceTable.basename():label=TABLE,
            expireTime:label=EXPIRE_TIME,
            state
          )
        """)
    parser.display_info.AddUriFunc(_GetUriFunction)
    parser.display_info.AddTransforms({'cluster': _TransformCluster})

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      Some value that we want to have printed later.
    """
    cli = util.GetAdminClient()
    instance_ref = args.CONCEPTS.instance.Parse()
    cluster_ref = args.CONCEPTS.cluster.Parse()

    if cluster_ref:
      cluster_str = cluster_ref.RelativeName()
    elif instance_ref:
      if args.IsSpecified('cluster'):
        cluster_str = instance_ref.RelativeName() + '/clusters/' + args.cluster
      else:
        cluster_str = instance_ref.RelativeName() + '/clusters/-'
    else:
      raise exceptions.InvalidArgumentException('--instance',
                                                '--instance must be specified')
    msg = (
        util.GetAdminMessages()
        .BigtableadminProjectsInstancesClustersBackupsListRequest(
            parent=cluster_str))
    for backup in list_pager.YieldFromList(
        cli.projects_instances_clusters_backups,
        msg,
        field='backups',
        batch_size_attribute=None):
      yield backup

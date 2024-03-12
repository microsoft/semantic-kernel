# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""bigtable clusters list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import resources


def _GetUriFunction(resource):
  return resources.REGISTRY.ParseRelativeName(
      resource.name,
      collection='bigtableadmin.projects.instances.clusters').SelfLink()


class ListClusters(base.ListCommand):
  """List existing Bigtable clusters."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To list all clusters in an instance, run:

            $ {command} --instances=my-instance-id

          To list all clusters in multiple instances, run:

            $ {command} --instances=my-instance-id,my-other-instance-id

          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddInstancesResourceArg(parser, 'to list clusters for')
    parser.display_info.AddFormat("""
          table(
            name.segment(3):sort=1:label=INSTANCE,
            name.basename():sort=2:label=NAME,
            location.basename():label=ZONE,
            serveNodes:label=NODES,
            defaultStorageType:label=STORAGE,
            state
          )
        """)
    parser.display_info.AddUriFunc(_GetUriFunction)
    parser.display_info.AddCacheUpdater(arguments.InstanceCompleter)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Yields:
      Some value that we want to have printed later.
    """
    cli = util.GetAdminClient()
    instance_refs = args.CONCEPTS.instances.Parse()
    if not args.IsSpecified('instances'):
      instance_refs = [util.GetInstanceRef('-')]
    for instance_ref in instance_refs:
      msg = (
          util.GetAdminMessages()
          .BigtableadminProjectsInstancesClustersListRequest(
              parent=instance_ref.RelativeName()))
      for cluster in list_pager.YieldFromList(
          cli.projects_instances_clusters,
          msg,
          field='clusters',
          batch_size_attribute=None):
        yield cluster

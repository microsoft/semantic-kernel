# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""bigtable tables list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def _GetUriFunction(resource):
  table_ref = resources.REGISTRY.ParseRelativeName(
      resource.name,
      collection='bigtableadmin.projects.instances.tables')
  return table_ref.SelfLink()


class ListInstances(base.ListCommand):
  """List existing Bigtable instance tables.

  ## EXAMPLES
  To list all tables in an instance, run:

    $ {command} --instances=INSTANCE_NAME

  To list all tables in several instances, run:
    $ {command} --instances=INSTANCE_NAME1,INSTANCE_NAME2
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    parser.display_info.AddFormat("""
          table(
            name.basename():sort=1
          )
        """)
    parser.display_info.AddUriFunc(_GetUriFunction)
    arguments.ArgAdder(parser).AddInstance(
        positional=False, required=True, multiple=True)

  def Run(self, args):
    cli = util.GetAdminClient()
    msgs = util.GetAdminMessages()

    instances = args.instances
    results = []
    for instance in instances:
      instance_ref = resources.REGISTRY.Parse(
          instance,
          params={'projectsId': properties.VALUES.core.project.GetOrFail},
          collection='bigtableadmin.projects.instances')

      request = msgs.BigtableadminProjectsInstancesTablesListRequest(
          parent=instance_ref.RelativeName(),)

      for table in list_pager.YieldFromList(
          cli.projects_instances_tables,
          request,
          field='tables',
          batch_size_attribute=None):
        results.append(table)

    return results

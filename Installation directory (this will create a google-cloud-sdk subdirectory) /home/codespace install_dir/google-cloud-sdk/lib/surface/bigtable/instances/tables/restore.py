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
"""bigtable tables restore command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import log


class RestoreTables(base.RestoreCommand):
  """Restore a Cloud Bigtable backup to a new table."""
  detailed_help = {
      'DESCRIPTION':
          textwrap.dedent("""
          This command restores a Cloud Bigtable backup to a new table.
          """),
      'EXAMPLES':
          textwrap.dedent("""
          To restore table 'table2' from backup 'backup1', run:

            $ {command} --source-instance=instance1 --source-cluster=cluster1 --source=backup1 --destination-instance=instance1 --destination=table2

          To restore table 'table2' from backup 'backup1' in a different project, run:

            $ {command} --source=projects/project1/instances/instance1/clusters/cluster1/backups/backup1 --destination=projects/project2/instances/instance2/tables/table2
          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddTableRestoreResourceArg(parser)
    arguments.ArgAdder(parser).AddAsync()

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    cli = util.GetAdminClient()
    msgs = util.GetAdminMessages()
    backup_ref = args.CONCEPTS.source.Parse()  # backup
    table_ref = args.CONCEPTS.destination.Parse()  # table

    restore_request = msgs.RestoreTableRequest(
        # Full backup name.
        backup=backup_ref.RelativeName(),
        # Table id
        tableId=table_ref.Name())

    msg = (msgs.BigtableadminProjectsInstancesTablesRestoreRequest(
        # The name of the instance in which to create the restored table.
        parent=table_ref.Parent().RelativeName(),
        restoreTableRequest=restore_request))

    operation = cli.projects_instances_tables.Restore(msg)
    operation_ref = util.GetOperationRef(operation)
    if args.async_:
      log.CreatedResource(
          operation_ref.RelativeName(),
          kind='bigtable table {0}'.format(table_ref.Name()),
          is_async=True)
      return
    return util.AwaitTable(
        operation_ref,
        'Creating bigtable table {0}'.format(table_ref.Name()))

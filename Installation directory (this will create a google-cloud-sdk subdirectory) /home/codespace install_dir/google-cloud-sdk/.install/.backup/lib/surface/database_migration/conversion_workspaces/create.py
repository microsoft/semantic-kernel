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
"""Command to create conversion workspaces for a database migration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import api_util
from googlecloudsdk.api_lib.database_migration import conversion_workspaces
from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.database_migration.conversion_workspaces import flags as cw_flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """
        Create a Database Migration Service conversion workspace.
        """,
    'EXAMPLES': """\
        To create a conversion workspace:

            $ {command} my-conversion-workspace --region=us-central1
            --display-name=cw1 --source-database-engine=ORACLE
            --source-database-version=11 --destination-database-engine=POSTGRESQL
            --destination-database-version=8
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.Command):
  """Create a Database Migration Service conversion workspace."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddConversionWorkspaceResourceArg(parser, 'to create')
    cw_flags.AddNoAsyncFlag(parser)
    cw_flags.AddDisplayNameFlag(parser)
    cw_flags.AddDatabaseEngineFlag(parser)
    cw_flags.AddDatabaseVersionFlag(parser)
    cw_flags.AddGlobalSettingsFlag(parser)

  def Run(self, args):
    """Create a Database Migration Service conversion workspace.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
    """
    conversion_workspace_ref = args.CONCEPTS.conversion_workspace.Parse()
    parent_ref = conversion_workspace_ref.Parent().RelativeName()

    cw_client = conversion_workspaces.ConversionWorkspacesClient(
        self.ReleaseTrack())
    result_operation = cw_client.Create(
        parent_ref, conversion_workspace_ref.conversionWorkspacesId, args)

    client = api_util.GetClientInstance(self.ReleaseTrack())
    messages = api_util.GetMessagesModule(self.ReleaseTrack())
    resource_parser = api_util.GetResourceParser(self.ReleaseTrack())

    if args.IsKnownAndSpecified('no_async'):
      log.status.Print(
          'Waiting for conversion workspace [{}] to be created with [{}]'
          .format(
              conversion_workspace_ref.conversionWorkspacesId,
              result_operation.name,
          )
      )

      api_util.HandleLRO(client, result_operation,
                         client.projects_locations_conversionWorkspaces)

      log.status.Print(
          'Created conversion workspace {} [{}]'.format(
              conversion_workspace_ref.conversionWorkspacesId,
              result_operation.name,
          )
      )
      return

    operation_ref = resource_parser.Create(
        'datamigration.projects.locations.operations',
        operationsId=result_operation.name,
        projectsId=conversion_workspace_ref.projectsId,
        locationsId=conversion_workspace_ref.locationsId)

    return client.projects_locations_operations.Get(
        messages.DatamigrationProjectsLocationsOperationsGetRequest(
            name=operation_ref.operationsId))

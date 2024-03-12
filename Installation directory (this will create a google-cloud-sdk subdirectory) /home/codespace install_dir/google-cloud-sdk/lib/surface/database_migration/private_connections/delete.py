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
"""Command to delete a database migration private connection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import api_util
from googlecloudsdk.api_lib.database_migration import private_connections
from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.database_migration.private_connections import flags as pc_flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io

DESCRIPTION = 'Delete a Database Migration private connection'
EXAMPLES = """\
    To delete a private connection called 'my-private-connection', run:

        $ {command} my-private-connection --region=us-central1


   """


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.Command):
  """Delete a Database Migration private connection."""
  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def CommonArgs(parser):
    """Common arguments for all release tracks.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddPrivateConnectionDeleteResourceArg(parser, 'to delete')
    pc_flags.AddNoAsyncFlag(parser)

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    Delete.CommonArgs(parser)

  def Run(self, args):
    """Delete a Database Migration private connection.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the delete
      operation if the delete was successful.
    """
    private_connection_ref = args.CONCEPTS.private_connection.Parse()
    delete_warning = ('You are about to delete private_connection {}.\n'
                      'Are you sure?'.format(
                          private_connection_ref.RelativeName()))

    if not console_io.PromptContinue(message=delete_warning):
      return None

    pc_client = private_connections.PrivateConnectionsClient(
        release_track=self.ReleaseTrack())
    result_operation = pc_client.Delete(private_connection_ref.RelativeName())

    client = api_util.GetClientInstance(self.ReleaseTrack())
    messages = api_util.GetMessagesModule(self.ReleaseTrack())
    resource_parser = api_util.GetResourceParser(self.ReleaseTrack())

    if args.IsKnownAndSpecified('no_async'):
      log.status.Print(
          'Waiting for private connection [{}] to be deleted with [{}]'.format(
              private_connection_ref.privateConnectionsId,
              result_operation.name))

      api_util.HandleLRO(
          client,
          result_operation,
          client.projects_locations_privateConnections,
          no_resource=True)

      log.status.Print('Deleted private connection {} [{}]'.format(
          private_connection_ref.privateConnectionsId, result_operation.name))
      return

    operation_ref = resource_parser.Create(
        'datamigration.projects.locations.operations',
        operationsId=result_operation.name,
        projectsId=private_connection_ref.projectsId,
        locationsId=private_connection_ref.locationsId)

    return client.projects_locations_operations.Get(
        messages.DatamigrationProjectsLocationsOperationsGetRequest(
            name=operation_ref.operationsId))

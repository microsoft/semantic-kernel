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
"""Command to update connection profiles for a database migration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import api_util
from googlecloudsdk.api_lib.database_migration import connection_profiles
from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.database_migration import flags
from googlecloudsdk.command_lib.database_migration.connection_profiles import flags as cp_flags
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'DESCRIPTION':
        """
        Update a Database Migration Service connection profile.
        - Draft connection profile: the user can update all flags available in
        `connection-profiles create` command.
        - Existing connection profile: the user can update a limited list of
        flags, see `connection-profiles update` Synopsis.
        - If a migration job is using the connection profile, then updates to
        fields `host`, `port`, `username`, and `password` will propagate to the
        destination instance.
        """,
    'EXAMPLES':
        """\
        To update the username of a connection profile:

            $ {command} my-profile --region=us-central1
            --username=new-user
        """,
}


class _Update(object):
  """Update a Database Migration Service connection profile."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddConnectionProfileResourceArg(parser, 'to update')

    cp_flags.AddDisplayNameFlag(parser)
    cp_flags.AddUsernameFlag(parser)
    cp_flags.AddPasswordFlagGroup(parser)
    cp_flags.AddHostFlag(parser)
    cp_flags.AddPortFlag(parser)
    cp_flags.AddCaCertificateFlag(parser)
    cp_flags.AddPrivateKeyFlag(parser)
    flags.AddLabelsUpdateFlags(parser)

  def Run(self, args):
    """Update a Database Migration Service connection profiles.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
    """
    connection_profile_ref = args.CONCEPTS.connection_profile.Parse()

    if args.prompt_for_password:
      args.password = console_io.PromptPassword('Please Enter Password: ')

    cp_client = connection_profiles.ConnectionProfilesClient(
        self.ReleaseTrack())
    result_operation = cp_client.Update(connection_profile_ref.RelativeName(),
                                        args)

    client = api_util.GetClientInstance(self.ReleaseTrack())
    messages = api_util.GetMessagesModule(self.ReleaseTrack())
    resource_parser = api_util.GetResourceParser(self.ReleaseTrack())

    operation_ref = resource_parser.Create(
        'datamigration.projects.locations.operations',
        operationsId=result_operation.name,
        projectsId=connection_profile_ref.projectsId,
        locationsId=connection_profile_ref.locationsId)

    return client.projects_locations_operations.Get(
        messages.DatamigrationProjectsLocationsOperationsGetRequest(
            name=operation_ref.operationsId))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(_Update, base.Command):
  """Update a Database Migration Service connection profile."""

  @staticmethod
  def Args(parser):
    _Update.Args(parser)
    cp_flags.AddCertificateFlag(parser)
    cp_flags.AddInstanceFlag(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateGA(_Update, base.Command):
  """Update a Database Migration Service connection profile."""

  @staticmethod
  def Args(parser):
    _Update.Args(parser)
    cp_flags.AddClientCertificateFlag(parser)
    cp_flags.AddCloudSQLInstanceFlag(parser)
    cp_flags.AddAlloydbClusterFlag(parser)

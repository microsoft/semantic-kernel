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
"""Command to create connection profiles for a database migration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.database_migration import flags
from googlecloudsdk.command_lib.database_migration.connection_profiles import create_helper
from googlecloudsdk.command_lib.database_migration.connection_profiles import flags as cp_flags
from googlecloudsdk.command_lib.database_migration.connection_profiles import oracle_flags
from googlecloudsdk.core.console import console_io

DETAILED_HELP = {
    'DESCRIPTION': (
        'Create a Database Migration Service connection profile for Oracle.'
    ),
    'EXAMPLES': """\
        To create a connection profile my-profile for Oracle:

            $ {command} my-profile --region=us-central1
            --password=123456 --username=my-user
            --host=1.2.3.4 --port=5432
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Oracle(base.Command):
  """Create a Database Migration Service connection profile for Oracle."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddOracleConnectionProfileResourceArg(parser, 'to create')

    cp_flags.AddNoAsyncFlag(parser)
    cp_flags.AddDisplayNameFlag(parser)
    cp_flags.AddUsernameFlag(parser, required=True)
    cp_flags.AddPasswordFlagGroup(parser, required=True)
    cp_flags.AddHostFlag(parser, required=True)
    cp_flags.AddPortFlag(parser, required=True)
    cp_flags.AddSslServerOnlyConfigGroup(parser)
    oracle_flags.AddDatabaseServiceFlag(parser)
    flags.AddLabelsCreateFlags(parser)

  def Run(self, args):
    """Create a Database Migration Service connection profile.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
    """
    connection_profile_ref = args.CONCEPTS.connection_profile.Parse()
    parent_ref = connection_profile_ref.Parent().RelativeName()

    if args.prompt_for_password:
      args.password = console_io.PromptPassword(
          'Please Enter Password for the database user {user}: '.format(
              user=args.username
          )
      )

    helper = create_helper.CreateHelper()
    return helper.create(self.ReleaseTrack(), parent_ref,
                         connection_profile_ref, args, 'ORACLE')

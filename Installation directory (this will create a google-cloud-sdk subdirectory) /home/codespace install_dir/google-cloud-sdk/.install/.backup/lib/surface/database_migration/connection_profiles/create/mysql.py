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
"""Command to create connection profiles for a database migration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.database_migration import flags
from googlecloudsdk.command_lib.database_migration.connection_profiles import create_helper
from googlecloudsdk.command_lib.database_migration.connection_profiles import flags as cp_flags
from googlecloudsdk.core.console import console_io

DESCRIPTION = ('Create a Database Migration Service connection profile for '
               'MySQL.')
EXAMPLES = """\
    To create a connection profile for MySQL:

        $ {{command}} my-profile --region=us-central1 --password=123456
        --username=my-user --host=1.2.3.4 --port=3306

    If the source is a Cloud SQL database, run:

        $ {{command}} my-profile --region=us-central1 --password=123456
        --username=my-user --host=1.2.3.4 --port=3306
        --{instance}=my-instance --provider=CLOUDSQL
    """


class _MySQL(object):
  """Create a Database Migration Service connection profile for MySQL."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddConnectionProfileResourceArg(parser, 'to create')

    cp_flags.AddNoAsyncFlag(parser)
    cp_flags.AddDisplayNameFlag(parser)
    cp_flags.AddDatabaseParamsFlags(parser, require_password=False)
    cp_flags.AddProviderFlag(parser)
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
      args.password = console_io.PromptPassword('Please Enter Password: ')

    helper = create_helper.CreateHelper()
    return helper.create(self.ReleaseTrack(), parent_ref,
                         connection_profile_ref, args, 'MYSQL')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class MySQLAlpha(_MySQL, base.Command):
  """Create a Database Migration Service connection profile for MySQL."""

  detailed_help = {
      'DESCRIPTION': DESCRIPTION,
      'EXAMPLES': EXAMPLES.format(instance='instance')
  }

  @staticmethod
  def Args(parser):
    _MySQL.Args(parser)
    cp_flags.AddSslConfigGroup(parser, base.ReleaseTrack.ALPHA)
    cp_flags.AddInstanceFlag(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class MySQLGA(_MySQL, base.Command):
  """Create a Database Migration Service connection profile for MySQL."""

  detailed_help = {
      'DESCRIPTION': DESCRIPTION,
      'EXAMPLES': EXAMPLES.format(instance='cloudsql-instance')
  }

  @staticmethod
  def Args(parser):
    _MySQL.Args(parser)
    cp_flags.AddSslConfigGroup(parser, base.ReleaseTrack.GA)
    cp_flags.AddCloudSQLInstanceFlag(parser)

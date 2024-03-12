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
from googlecloudsdk.command_lib.database_migration.connection_profiles import cloudsql_flags as cs_flags
from googlecloudsdk.command_lib.database_migration.connection_profiles import create_helper
from googlecloudsdk.command_lib.database_migration.connection_profiles import flags as cp_flags

DETAILED_HELP = {
    'DESCRIPTION':
        'Create a Database Migration Service destination connection profile '
        'for Cloud SQL. This will create a Cloud SQL replica. '
        'Used for PostgreSQL and MySQL migrations.',
    'EXAMPLES':
        """\
          To create a connection profile for Cloud SQL with database version
          MySQL 5.6:

              $ {command} my-profile --region=us-central1
              --database-version=MYSQL_5_6 --source-id=cp1 --tier=db-n1-standard-1

          To create a connection profile for Cloud SQL and a Cloud SQL replica
          with database version PostgreSQL 10:

              $ {command} my-profile --region=us-central1
              --database-version=POSTGRES_10 --source-id=cp1
              --tier=db-custom-1-3840 --zone=us-central1-a
        """,
}


class _CloudSQL(object):
  """Create a Database Migration Service connection profile for Cloud SQL."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddCloudSqlConnectionProfileResourceArgs(parser, 'to create')

    cp_flags.AddNoAsyncFlag(parser)
    cp_flags.AddDisplayNameFlag(parser)
    cp_flags.AddProviderFlag(parser)
    cs_flags.AddActivationPolicylag(parser)
    cs_flags.AddAuthorizedNetworksFlag(parser)
    cs_flags.AddAutoStorageIncreaseFlag(parser)
    cs_flags.AddDatabaseFlagsFlag(parser)
    cs_flags.AddDataDiskSizeFlag(parser)
    cs_flags.AddDataDiskTypeFlag(parser)
    cs_flags.AddAvailabilityTypeFlag(parser)
    cs_flags.AddEnableIpv4Flag(parser)
    cs_flags.AddPrivateNetworkFlag(parser)
    cs_flags.AddRequireSslFlag(parser)
    cs_flags.AddUserLabelsFlag(parser)
    cs_flags.AddStorageAutoResizeLimitFlag(parser)
    cs_flags.AddTierFlag(parser)
    cs_flags.AddZoneFlag(parser)
    cs_flags.AddSecondaryZoneFlag(parser)
    cs_flags.AddRootPassword(parser)
    flags.AddLabelsCreateFlags(parser)

  def Run(self, args):
    """Create a Database Migration Service connection profile for Cloud SQL.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
    """
    connection_profile_ref = args.CONCEPTS.connection_profile.Parse()
    parent_ref = connection_profile_ref.Parent().RelativeName()

    helper = create_helper.CreateHelper()
    return helper.create(self.ReleaseTrack(), parent_ref,
                         connection_profile_ref, args, 'CLOUDSQL')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CloudSQLAlpha(_CloudSQL, base.Command):
  """Create a Database Migration Service connection profile for Cloud SQL."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    _CloudSQL.Args(parser)
    cs_flags.AddDatabaseVersionFlag(parser, support_minor_version=False)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CloudSQLGA(_CloudSQL, base.Command):
  """Create a Database Migration Service connection profile for Cloud SQL."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    _CloudSQL.Args(parser)
    cs_flags.AddDatabaseVersionFlag(parser, support_minor_version=True)
    resource_args.AddCmekResourceArgs(parser)
    cs_flags.AddAllocatedIpRangeFlag(parser)
    cs_flags.AddEditionFlag(parser)
    cs_flags.AddEnableDataCacheFlag(parser)

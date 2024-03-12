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
"""Command to create migration jobs for a database migration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import api_util
from googlecloudsdk.api_lib.database_migration import migration_jobs
from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.database_migration import flags
from googlecloudsdk.command_lib.database_migration.migration_jobs import flags as mj_flags
from googlecloudsdk.core import log

MYSQL_CONNECTIVITY_DOC = 'https://cloud.google.com/database-migration/docs/mysql/configure-connectivity'

DETAILED_HELP_ALPHA = {
    'DESCRIPTION': """
        Create a Database Migration Service migration job.
        Recommended steps before creating the migration job:
        - Create a source connection profile. See prerequisites [here](https://cloud.google.com/database-migration/docs/mysql/configure-source-database).
        - Create a destination connection profile. For migrating to Cloud SQL for MySQL or Cloud SQL for PostgreSQL, use the cloudsql connection profile for DMS to create the CloudSQL replica for you.
        - Configure the connectivity method. See prerequisites [here]({MYSQL_CONNECTIVITY_DOC}).
        """.format(MYSQL_CONNECTIVITY_DOC=MYSQL_CONNECTIVITY_DOC),
    'EXAMPLES': """\
        To create a continuous migration job with IP allowlist connectivity:

            $ {command} my-migration-job --region=us-central1 --type=CONTINUOUS
            --source=cp1 --destination=cp2

        To create a continuous migration job with VPC peering connectivity:

            $ {command} my-migration-job --region=us-central1 --type=CONTINUOUS
            --source=cp1 --destination=cp2
            --peer-vpc=projects/my-project/global/networks/my-network

        To create a one-time migration job with reverse-SSH tunnel connectivity:

            $ {command} my-migration-job --region=us-central1 --type=ONE_TIME
            --source=cp1 --destination=cp2 --vm=vm1 --vm-ip=1.1.1.1
            --vm-port=1111 --vpc=projects/my-project/global/networks/my-network
        """,
}

DETAILED_HELP_GA = {
    'DESCRIPTION': """
        Create a Database Migration Service migration job.
        Recommended steps before creating the migration job:
        - Create a source connection profile. See prerequisites [here](https://cloud.google.com/database-migration/docs/mysql/configure-source-database).
        - Create a destination connection profile. For migrating to Cloud SQL for MySQL or Cloud SQL for PostgreSQL, use the cloudsql connection profile for DMS to create the CloudSQL replica for you.
        - Configure the connectivity method. See prerequisites [here]({MYSQL_CONNECTIVITY_DOC}).
        - [Heterogeneous migrations only] Create a conversion workspace.
        """.format(MYSQL_CONNECTIVITY_DOC=MYSQL_CONNECTIVITY_DOC),
    'EXAMPLES': """\
        To create a continuous migration job with IP allowlist connectivity:

            $ {command} my-migration-job --region=us-central1 --type=CONTINUOUS
            --source=cp1 --destination=cp2

        To create a continuous migration job with VPC peering connectivity:

            $ {command} my-migration-job --region=us-central1 --type=CONTINUOUS
            --source=cp1 --destination=cp2
            --peer-vpc=projects/my-project/global/networks/my-network

        To create a one-time migration job with reverse-SSH tunnel connectivity:

            $ {command} my-migration-job --region=us-central1 --type=ONE_TIME
            --source=cp1 --destination=cp2 --vm=vm1 --vm-ip=1.1.1.1
            --vm-port=1111 --vpc=projects/my-project/global/networks/my-network

        To create a heterogeneous continuous migration job:

            $ {command} my-migration-job --region=us-central1 --type=CONTINUOUS
            --source=cp1 --destination=cp2 --conversion-workspace=cw

        To create a continuous SQL Server to SQL Server homogeneous migration
        job:
            $ {command} my-migration-job --region=us-central1 --type=CONTINUOUS
            --source=cp1 --destination=cp2
            --sqlserver-backup-file-pattern=pattern
            --sqlserver-databases=db1,db2,db3

        To create a continuous SQL Server to SQL Server homogeneous migration
        job with encrypted databases:
            $ {command} my-migration-job --region=us-central1 --type=CONTINUOUS
            --source=cp1 --destination=cp2
            --sqlserver-backup-file-pattern=pattern
            --sqlserver-databases=db1,db2,db3
            --sqlserver-encrypted-databases=PATH/TO/ENCRYPTION/SETTINGS
        """,
}


class _Create(object):
  """Create a Database Migration Service migration job."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    mj_flags.AddNoAsyncFlag(parser)
    mj_flags.AddDisplayNameFlag(parser)
    mj_flags.AddTypeFlag(parser, required=True)
    mj_flags.AddDumpPathFlag(parser)
    mj_flags.AddConnectivityGroupFlag(
        parser, mj_flags.ApiType.CREATE, required=True
    )
    flags.AddLabelsCreateFlags(parser)

  def Run(self, args):
    """Create a Database Migration Service migration job.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the create
      operation if the create was successful.
    """
    migration_job_ref = args.CONCEPTS.migration_job.Parse()
    parent_ref = migration_job_ref.Parent().RelativeName()

    source_ref = args.CONCEPTS.source.Parse()
    destination_ref = args.CONCEPTS.destination.Parse()
    if self.ReleaseTrack() == base.ReleaseTrack.GA:
      conversion_workspace_ref = args.CONCEPTS.conversion_workspace.Parse()
      cmek_key_ref = args.CONCEPTS.cmek_key.Parse()
    else:
      conversion_workspace_ref = None
      cmek_key_ref = None

    mj_client = migration_jobs.MigrationJobsClient(self.ReleaseTrack())
    result_operation = mj_client.Create(
        parent_ref,
        migration_job_ref.migrationJobsId,
        source_ref,
        destination_ref,
        conversion_workspace_ref,
        cmek_key_ref,
        args,
    )

    client = api_util.GetClientInstance(self.ReleaseTrack())
    messages = api_util.GetMessagesModule(self.ReleaseTrack())
    resource_parser = api_util.GetResourceParser(self.ReleaseTrack())

    if args.IsKnownAndSpecified('no_async'):
      log.status.Print(
          'Waiting for migration job [{}] to be created with [{}]'.format(
              migration_job_ref.migrationJobsId, result_operation.name))

      api_util.HandleLRO(client, result_operation,
                         client.projects_locations_migrationJobs)

      log.status.Print('Created migration job {} [{}]'.format(
          migration_job_ref.migrationJobsId, result_operation.name))
      return

    operation_ref = resource_parser.Create(
        'datamigration.projects.locations.operations',
        operationsId=result_operation.name,
        projectsId=migration_job_ref.projectsId,
        locationsId=migration_job_ref.locationsId)

    return client.projects_locations_operations.Get(
        messages.DatamigrationProjectsLocationsOperationsGetRequest(
            name=operation_ref.operationsId))


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(_Create, base.Command):
  """Create a Database Migration Service migration job."""

  detailed_help = DETAILED_HELP_GA

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddHeterogeneousMigrationJobResourceArgs(
        parser, 'to create', required=True
    )
    _Create.Args(parser)
    mj_flags.AddFilterFlag(parser)
    mj_flags.AddCommitIdFlag(parser)
    mj_flags.AddDumpParallelLevelFlag(parser)
    mj_flags.AddSqlServerHomogeneousMigrationConfigFlag(parser)
    mj_flags.AddDumpTypeFlag(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(_Create, base.Command):
  """Create a Database Migration Service migration job."""

  detailed_help = DETAILED_HELP_ALPHA

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddMigrationJobResourceArgs(
        parser, 'to create', required=True
    )
    _Create.Args(parser)

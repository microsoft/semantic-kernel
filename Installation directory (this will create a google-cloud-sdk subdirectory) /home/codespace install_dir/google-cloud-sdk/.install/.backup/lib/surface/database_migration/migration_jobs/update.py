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
"""Command to update migration jobs for a database migration."""

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

DETAILED_HELP = {
    'DESCRIPTION':
        """
        Update a Database Migration Service migration job.
        - Draft migration job: user can update all available flags.
        - Any other state can only update flags: `--display-name`,
        `--dump-path`, and connectivity method flags.
        """,
    'EXAMPLES':
        """\
        To update the source and destination connection profiles of a draft
        migration job:

            $ {command} my-migration-job --region=us-central1 --source=new-src
            --destination=new-dest

        To update the display name of a running migration job:

            $ {command} my-migration-job --region=us-central1
            --display-name=new-name

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class _Update(object):
  """Update a Database Migration Service migration job."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    resource_args.AddMigrationJobResourceArgs(parser, 'to update')
    mj_flags.AddNoAsyncFlag(parser)
    mj_flags.AddDisplayNameFlag(parser)
    mj_flags.AddTypeFlag(parser)
    mj_flags.AddDumpPathFlag(parser)
    mj_flags.AddConnectivityGroupFlag(parser, mj_flags.ApiType.UPDATE)
    flags.AddLabelsUpdateFlags(parser)

  def Run(self, args):
    """Update a Database Migration Service migration job.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the update
      operation if the update was successful.
    """
    migration_job_ref = args.CONCEPTS.migration_job.Parse()

    source_ref = args.CONCEPTS.source.Parse()
    destination_ref = args.CONCEPTS.destination.Parse()

    mj_client = migration_jobs.MigrationJobsClient(self.ReleaseTrack())
    result_operation = mj_client.Update(migration_job_ref.RelativeName(),
                                        source_ref, destination_ref, args)

    client = api_util.GetClientInstance(self.ReleaseTrack())
    messages = api_util.GetMessagesModule(self.ReleaseTrack())
    resource_parser = api_util.GetResourceParser(self.ReleaseTrack())

    if args.IsKnownAndSpecified('no_async'):
      log.status.Print(
          'Waiting for migration job [{}] to be updated with [{}]'.format(
              migration_job_ref.migrationJobsId, result_operation.name))

      api_util.HandleLRO(client, result_operation,
                         client.projects_locations_migrationJobs)

      log.status.Print('Updated migration job {} [{}]'.format(
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
class UpdateGA(_Update, base.Command):
  """Update a Database Migration Service migration job."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    _Update.Args(parser)
    mj_flags.AddDumpParallelLevelFlag(parser)
    mj_flags.AddDumpTypeFlag(parser)
    mj_flags.AddFilterFlag(parser)
    mj_flags.AddCommitIdFlag(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(_Update, base.Command):
  """Update a Database Migration Service migration job."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    _Update.Args(parser)

# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to update connection profiles for datastream."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastream import connection_profiles
from googlecloudsdk.api_lib.datastream import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.datastream import flags
from googlecloudsdk.command_lib.datastream import resource_args
from googlecloudsdk.command_lib.datastream.connection_profiles import flags as cp_flags
from googlecloudsdk.core.console import console_io

DESCRIPTION = ('Updates a Datastream connection profile')
EXAMPLES = """\
    To update a connection profile for Oracle:

        $ {command} CONNECTION_PROFILE --location=us-central1 --type=oracle --oracle-password=fakepassword --oracle-username=fakeuser --display-name=my-profile --oracle-hostname=35.188.150.50 --oracle-port=1521 --database-service=ORCL --static-ip-connectivity

    To update a connection profile for MySQL:

        $ {command} CONNECTION_PROFILE --location=us-central1 --type=mysql --mysql-password=fakepassword --mysql-username=fakeuser --display-name=my-profile --mysql-hostname=35.188.150.50 --mysql-port=3306 --static-ip-connectivity

    To update a connection profile for PostgreSQL:

        $ {command} CONNECTION_PROFILE --location=us-central1 --type=postgresql --postgresql-password=fakepassword --postgresql-username=fakeuser --display-name=my-profile --postgresql-hostname=35.188.150.50 --postgresql-port=5432 --postgresql-database=db --static-ip-connectivity

    To update a connection profile for Google Cloud Storage:

        $ {command} CONNECTION_PROFILE --location=us-central1 --type=google-cloud-storage --bucket=fake-bucket --root-path=/root/path --display-name=my-profile

    To update a connection profile for Google Cloud Storage:

        $ {command} CONNECTION_PROFILE --location=us-central1 --type=bigquery --display-name=my-profile
   """

EXAMPLES_BETA = """\
    To update a connection profile for Oracle:

        $ {command} CONNECTION_PROFILE --location=us-central1 --type=oracle --oracle-password=fakepassword --oracle-username=fakeuser --display-name=my-profile --oracle-hostname=35.188.150.50 --oracle-port=1521 --database-service=ORCL --static-ip-connectivity

    To update a connection profile for MySQL:

        $ {command} CONNECTION_PROFILE --location=us-central1 --type=mysql --mysql-password=fakepassword --mysql-username=fakeuser --display-name=my-profile --mysql-hostname=35.188.150.50 --mysql-port=3306 --static-ip-connectivity

    To update a connection profile for Google Cloud Storage:

        $ {command} CONNECTION_PROFILE --location=us-central1 --type=google-cloud-storage --bucket-name=fake-bucket --root-path=/root/path --display-name=my-profile --no-connectivity
   """


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.Command):
  """Update a Datastream connection profile."""
  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def CommonArgs(parser, release_track):
    """Common arguments for all release tracks.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
      release_track: Some arguments are added based on the command release
        track.
    """
    resource_args.AddConnectionProfileResourceArg(
        parser, 'to update', release_track, required=False)

    cp_flags.AddTypeFlag(parser)
    cp_flags.AddDisplayNameFlag(parser, required=False)
    if release_track == base.ReleaseTrack.GA:
      cp_flags.AddValidationGroup(parser, 'Update')

    profile_flags = parser.add_group(mutex=True)
    cp_flags.AddMysqlProfileGroup(profile_flags, required=False)
    cp_flags.AddOracleProfileGroup(profile_flags, required=False)
    cp_flags.AddPostgresqlProfileGroup(profile_flags, required=False)
    cp_flags.AddGcsProfileGroup(profile_flags, release_track, required=False)
    flags.AddLabelsUpdateFlags(parser)

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    Update.CommonArgs(parser, base.ReleaseTrack.GA)

  def Run(self, args):
    """Update a Datastream connection profile.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the update
      operation if the update was successful.
    """
    connection_profile_ref = args.CONCEPTS.connection_profile.Parse()

    if args.oracle_prompt_for_password:
      args.oracle_password = console_io.PromptPassword(
          'Please Enter Password: ')

    if args.mysql_prompt_for_password:
      args.mysql_password = console_io.PromptPassword('Please Enter Password: ')

    if args.postgresql_prompt_for_password:
      args.postgresql_password = console_io.PromptPassword(
          'Please Enter Password: ')

    cp_type = (args.type).upper()
    cp_client = connection_profiles.ConnectionProfilesClient()
    result_operation = cp_client.Update(connection_profile_ref.RelativeName(),
                                        cp_type, self.ReleaseTrack(), args)

    client = util.GetClientInstance()
    messages = util.GetMessagesModule()
    resource_parser = util.GetResourceParser()

    operation_ref = resource_parser.Create(
        'datastream.projects.locations.operations',
        operationsId=result_operation.name,
        projectsId=connection_profile_ref.projectsId,
        locationsId=connection_profile_ref.locationsId)

    return client.projects_locations_operations.Get(
        messages.DatastreamProjectsLocationsOperationsGetRequest(
            name=operation_ref.operationsId))


@base.Deprecate(
    is_removed=False,
    warning=('Datastream beta version is deprecated. Please use`gcloud '
             'datastream connection-profiles update` command instead.')
)
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update a Datastream connection profile."""
  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES_BETA}

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command."""
    Update.CommonArgs(parser, base.ReleaseTrack.BETA)

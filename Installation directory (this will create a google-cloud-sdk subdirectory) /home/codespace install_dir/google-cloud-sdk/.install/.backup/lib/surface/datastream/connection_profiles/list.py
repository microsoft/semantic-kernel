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
"""Implementation of connection profile list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastream import connection_profiles
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.datastream import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def _GetUri(connection_profile_info):
  """Gets the resource URI for a connection profile."""

  return connection_profiles.ConnectionProfilesClient().GetUri(
      connection_profile_info.name)


class _ConnectionProfileInfo:
  """Container for connection profile data using in list display."""

  def __init__(self, message, db_type):
    self.display_name = message.displayName
    self.name = message.name
    self.type = db_type
    self.create_time = message.createTime


class _List:
  """Base class for listing Datastream connection profiles."""

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""

    concept_parsers.ConceptParser.ForResource(
        "--location",
        resource_args.GetLocationResourceSpec(),
        group_help="The location you want to list the connection profiles for.",
        required=True).AddToParser(parser)

    parser.display_info.AddFormat("""
          table(
            display_name,
            name:label=ID,
            type,
            create_time.date():label=CREATED
          )
        """)

  def Run(self, args):
    """Runs the command.

    Args:
      args: All the arguments that were provided to this command invocation.

    Returns:
      An iterator over objects containing connection profile data.
    """
    cp_client = connection_profiles.ConnectionProfilesClient()
    project_id = properties.VALUES.core.project.Get(required=True)
    profiles = cp_client.List(project_id, args)

    return [
        _ConnectionProfileInfo(profile, self._GetType(profile))
        for profile in profiles
    ]

  def _GetType(self, profile):
    """Gets DB type of a connection profile.

    Args:
      profile: A connection configuration type of a connection profile.

    Returns:
      A String representation of the provided profile DB type.
      Default is None.
    """
    raise NotImplementedError


@base.Deprecate(
    is_removed=False,
    warning=("Datastream beta version is deprecated. Please use`gcloud "
             "datastream connection-profiles list` command instead.")
)
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(_List, base.ListCommand):
  """List Datastream connection profiles.

  List connection profiles.

  ## API REFERENCE
    This command uses the datastream/v1 API. The full documentation
    for this API can be found at: https://cloud.google.com/datastream/

  ## EXAMPLES
    To list all connection profiles in a project and location 'us-central1',
    run:

        $ {command} --location=us-central1

  """

  def _GetType(self, profile):
    if profile.mysqlProfile:
      return "MySQL"
    elif profile.oracleProfile:
      return "Oracle"
    elif profile.gcsProfile:
      return "Google Cloud Storage"
    else:
      return None


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(_List, base.ListCommand):
  """List Datastream connection profiles.

  List connection profiles.

  ## API REFERENCE
    This command uses the datastream/v1 API. The full documentation
    for this API can be found at: https://cloud.google.com/datastream/

  ## EXAMPLES
    To list all connection profiles in a project and location 'us-central1',
    run:

        $ {command} --location=us-central1

  """

  def _GetType(self, profile):
    if profile.mysqlProfile:
      return "MySQL"
    elif profile.oracleProfile:
      return "Oracle"
    elif profile.postgresqlProfile:
      return "PostgreSQL"
    elif profile.gcsProfile:
      return "Google Cloud Storage"
    else:
      return None

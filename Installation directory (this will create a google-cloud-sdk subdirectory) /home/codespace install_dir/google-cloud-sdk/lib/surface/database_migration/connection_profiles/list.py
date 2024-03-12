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

from googlecloudsdk.api_lib.database_migration import connection_profiles
from googlecloudsdk.api_lib.database_migration import resource_args
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def _GetUri(release_track, connection_profile_info):
  """Gets the resource URI for a connection profile."""

  return connection_profiles.ConnectionProfilesClient(release_track).GetUri(
      connection_profile_info.name)


class _ConnectionProfileInfo(object):
  """Container for connection profile data using in list display."""

  def __init__(self, message, host, engine):
    self.display_name = message.displayName
    self.name = message.name
    self.state = message.state
    self.provider_display = message.provider
    self.host = host
    self.create_time = message.createTime
    self.engine = engine

    if message.cloudsql:
      # In old connection profiles the "provider" field isn't populated
      if not message.provider:
        self.provider_display = 'CLOUDSQL'
      # If the connection profile's "oneof" = cloudsql --> read only replica
      self.provider_display = '{}_{}'.format(self.provider_display, 'REPLICA')


class _List(object):
  """Base class for listing Database Migration Service connection profiles."""

  @classmethod
  def Args(cls, parser):
    """Register flags for this command."""

    concept_parsers.ConceptParser.ForResource(
        '--region',
        resource_args.GetRegionResourceSpec(),
        group_help='The location you want to list the connection profiles for.'
    ).AddToParser(parser)

    parser.display_info.AddFormat("""
          table(
            name.basename():label=CONNECTION_PROFILE_ID,
            display_name,
            name.scope('locations').segment(0):label=REGION,
            state,
            provider_display:label=PROVIDER,
            engine,
            host:label=HOSTNAME/IP,
            create_time.date():label=CREATED
          )
        """)
    parser.display_info.AddUriFunc(lambda p: _GetUri(cls.ReleaseTrack(), p))

  def Run(self, args):
    """Runs the command.

    Args:
      args: All the arguments that were provided to this command invocation.

    Returns:
      An iterator over objects containing connection profile data.
    """
    cp_client = connection_profiles.ConnectionProfilesClient(
        self.ReleaseTrack())
    project_id = properties.VALUES.core.project.Get(required=True)
    profiles = cp_client.List(project_id, args)

    if args.format is None or args.format.startswith('"table'):
      return [
          _ConnectionProfileInfo(profile, self._GetHost(profile),
                                 cp_client.GetEngineName(profile))
          for profile in profiles
      ]
    return profiles


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(_List, base.ListCommand):
  """List Database Migration Service connection profiles.

  List connection profiles.

  ## API REFERENCE
    This command uses the datamigration/v1alpha2 API. The full documentation
    for this API can be found at: https://cloud.google.com/database-migration/

  ## EXAMPLES
    To list all connection profiles in a project and region ``us-central1'',
    run:

        $ {command} --region=us-central1

    To filter connection profiles with the given state:

        $ {command} --filter="state=READY"
  """

  def _GetHost(self, profile):
    if profile.mysql:
      return profile.mysql.host
    elif profile.cloudsql:
      return (profile.cloudsql.publicIp
              if profile.cloudsql.publicIp
              else profile.cloudsql.privateIp)
    else:
      return None


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListGA(_List, base.ListCommand):
  """List Database Migration Service connection profiles.

  List connection profiles.

  ## API REFERENCE
    This command uses the datamigration/v1 API. The full documentation
    for this API can be found at: https://cloud.google.com/database-migration/

  ## EXAMPLES
    To list all connection profiles in a project and region 'us-central1', run:

        $ {command} --region=us-central1

    To filter connection profiles with the given state:

        $ {command} --filter="state=READY"
  """

  def _GetHost(self, profile):
    # TODO(b/178304949): Add SQL SERVER case once supported.
    if profile.mysql:
      return profile.mysql.host
    elif profile.postgresql:
      return profile.postgresql.host
    elif profile.cloudsql:
      return (profile.cloudsql.publicIp
              if profile.cloudsql.publicIp
              else profile.cloudsql.privateIp)
    elif profile.alloydb:
      return profile.alloydb.settings.primaryInstanceSettings.privateIp
    elif profile.oracle:
      return profile.oracle.host
    else:
      return None

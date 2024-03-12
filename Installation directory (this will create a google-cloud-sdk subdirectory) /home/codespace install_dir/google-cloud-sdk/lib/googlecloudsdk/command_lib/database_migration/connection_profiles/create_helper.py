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
"""Helper module to create connection profiles for a database migration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import api_util
from googlecloudsdk.api_lib.database_migration import connection_profiles
from googlecloudsdk.core import log


class CreateHelper:
  """Helper class to create connection profiles for a database migration."""

  def create(self, release_track, parent_ref, connection_profile_ref, args,
             cp_type):
    """Create a connection profile and wait for its LRO to complete, if necessary.
    """
    cp_client = connection_profiles.ConnectionProfilesClient(release_track)
    result_operation = cp_client.Create(
        parent_ref, connection_profile_ref.connectionProfilesId, cp_type, args)

    client = api_util.GetClientInstance(release_track)
    messages = api_util.GetMessagesModule(release_track)
    resource_parser = api_util.GetResourceParser(release_track)

    if args.IsKnownAndSpecified('no_async'):
      log.status.Print(
          'Waiting for connection profile [{}] to be created with [{}]'.format(
              connection_profile_ref.connectionProfilesId,
              result_operation.name))

      api_util.HandleLRO(client, result_operation,
                         client.projects_locations_connectionProfiles)

      log.status.Print('Created connection profile {} [{}]'.format(
          connection_profile_ref.connectionProfilesId, result_operation.name))
      return

    operation_ref = resource_parser.Create(
        'datamigration.projects.locations.operations',
        operationsId=result_operation.name,
        projectsId=connection_profile_ref.projectsId,
        locationsId=connection_profile_ref.locationsId)

    return client.projects_locations_operations.Get(
        messages.DatamigrationProjectsLocationsOperationsGetRequest(
            name=operation_ref.operationsId))

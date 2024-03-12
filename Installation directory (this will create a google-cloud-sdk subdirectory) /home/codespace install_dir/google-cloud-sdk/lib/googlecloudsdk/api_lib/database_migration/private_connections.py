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
"""Cloud database migration private connections API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.database_migration import api_util
from googlecloudsdk.core import resources


def GetPrivateConnectionURI(resource):
  private_connection = resources.REGISTRY.ParseRelativeName(
      resource.name,
      collection='datamigration.projects.locations.privateConnections')
  return private_connection.SelfLink()


class PrivateConnectionsClient:
  """Client for private connections service in the API."""

  def __init__(self, release_track, client=None, messages=None):
    self._client = client or api_util.GetClientInstance(release_track)
    self._messages = messages or api_util.GetMessagesModule(release_track)
    self._service = self._client.projects_locations_privateConnections
    self._resource_parser = api_util.GetResourceParser(release_track)

  def _GetPrivateConnection(self, private_connection_id, args):
    """Returns a private connection object."""
    private_connection_obj = self._messages.PrivateConnection(
        name=private_connection_id, labels={}, displayName=args.display_name)
    vpc_peering_ref = args.CONCEPTS.vpc.Parse()

    private_connection_obj.vpcPeeringConfig = self._messages.VpcPeeringConfig(
        vpcName=vpc_peering_ref.RelativeName(), subnet=args.subnet)

    return private_connection_obj

  def Create(self, parent_ref, private_connection_id, args=None):
    """Creates a private connection.

    Args:
      parent_ref: a Resource reference to a parent
        datamigration.projects.locations resource for this private connection.
      private_connection_id: str, the name of the resource to create.
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Operation: the operation for creating the private connection.
    """

    private_connection = self._GetPrivateConnection(private_connection_id, args)

    request_id = api_util.GenerateRequestId()
    create_req_type = self._messages.DatamigrationProjectsLocationsPrivateConnectionsCreateRequest
    create_req = create_req_type(
        privateConnection=private_connection,
        privateConnectionId=private_connection.name,
        parent=parent_ref,
        requestId=request_id)

    return self._service.Create(create_req)

  def Delete(self, private_connection_name):
    """Deletes a private connection.

    Args:
      private_connection_name: str, the name of the resource to delete.

    Returns:
      Operation: the operation for deleting the private connection.
    """

    request_id = api_util.GenerateRequestId()
    delete_req_type = self._messages.DatamigrationProjectsLocationsPrivateConnectionsDeleteRequest
    delete_req = delete_req_type(
        name=private_connection_name, requestId=request_id)

    return self._service.Delete(delete_req)

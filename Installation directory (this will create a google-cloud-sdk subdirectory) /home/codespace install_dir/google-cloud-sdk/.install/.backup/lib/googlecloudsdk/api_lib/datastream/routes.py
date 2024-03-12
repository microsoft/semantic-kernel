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
"""Cloud Datastream private connections API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.datastream import util


class RoutesClient:
  """Client for private connections routes service in the API."""

  def __init__(self, client=None, messages=None):
    self._client = client or util.GetClientInstance()
    self._messages = messages or util.GetMessagesModule()
    self._service = self._client.projects_locations_privateConnections_routes
    self._resource_parser = util.GetResourceParser()

  def _GetRoute(self, route_id, args):
    """Returns a route object."""
    route_obj = self._messages.Route(
        name=route_id, labels={}, displayName=args.display_name,
        destinationAddress=args.destination_address,
        destinationPort=args.destination_port)
    return route_obj

  def Create(self, parent_ref, route_id, args=None):
    """Creates a route.

    Args:
      parent_ref: a Resource reference to a parent datastream.projects.
      locations.privateConnections resource for this route.
      route_id: str, the name of the resource to create.
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Operation: the operation for creating the private connection.
    """

    route = self._GetRoute(route_id, args)

    request_id = util.GenerateRequestId()
    create_req_type = self._messages.DatastreamProjectsLocationsPrivateConnectionsRoutesCreateRequest
    create_req = create_req_type(
        route=route,
        routeId=route.name,
        parent=parent_ref,
        requestId=request_id)

    return self._service.Create(create_req)



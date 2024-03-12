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
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources


def GetPrivateConnectionURI(resource):
  private_connection = resources.REGISTRY.ParseRelativeName(
      resource.name,
      collection='datastream.projects.locations.privateConnections')
  return private_connection.SelfLink()


class PrivateConnectionsClient:
  """Client for private connections service in the API."""

  def __init__(self, client=None, messages=None):
    self._client = client or util.GetClientInstance()
    self._messages = messages or util.GetMessagesModule()
    self._service = self._client.projects_locations_privateConnections
    self._resource_parser = util.GetResourceParser()

  def _GetPrivateConnection(self, private_connection_id, release_track, args):
    """Returns a private connection object."""
    private_connection_obj = self._messages.PrivateConnection(
        name=private_connection_id, labels={}, displayName=args.display_name)

    # TODO(b/207467120): use only vpc flag.
    if release_track == base.ReleaseTrack.BETA:
      vpc_peering_ref = args.CONCEPTS.vpc_name.Parse()
    else:
      vpc_peering_ref = args.CONCEPTS.vpc.Parse()

    private_connection_obj.vpcPeeringConfig = self._messages.VpcPeeringConfig(
        vpc=vpc_peering_ref.RelativeName(), subnet=args.subnet)

    return private_connection_obj

  def Create(self, parent_ref, private_connection_id, release_track, args=None):
    """Creates a private connection.

    Args:
      parent_ref: a Resource reference to a parent datastream.projects.locations
        resource for this private connection.
      private_connection_id: str, the name of the resource to create.
      release_track: Some arguments are added based on the command release
        track.
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Operation: the operation for creating the private connection.
    """

    private_connection = self._GetPrivateConnection(private_connection_id,
                                                    release_track, args)

    request_id = util.GenerateRequestId()
    create_req_type = self._messages.DatastreamProjectsLocationsPrivateConnectionsCreateRequest
    create_req = create_req_type(
        privateConnection=private_connection,
        privateConnectionId=private_connection.name,
        parent=parent_ref,
        requestId=request_id)

    return self._service.Create(create_req)

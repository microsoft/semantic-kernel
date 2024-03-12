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
"""Cloud Datastream stream objects API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.datastream import util


class StreamObjectsClient:
  """Client for stream objects service in the API."""

  def __init__(self, client=None, messages=None):
    self._client = client or util.GetClientInstance()
    self._messages = messages or util.GetMessagesModule()
    self._service = self._client.projects_locations_streams_objects
    self._resource_parser = util.GetResourceParser()

  def List(self, project_id, stream, args):
    """Get the list of objects in a stream.

    Args:
      project_id: The project ID to retrieve
      stream: The stream name to retrieve
      args: parsed command line arguments

    Returns:
      An iterator over all the matching stream objects.
    """
    stream_ref = self._resource_parser.Create(
        'datastream.projects.locations.streams',
        projectsId=project_id,
        streamsId=stream,
        locationsId=args.location)

    list_req_type = self._messages.DatastreamProjectsLocationsStreamsObjectsListRequest
    list_req = list_req_type(parent=stream_ref.RelativeName())

    return list_pager.YieldFromList(
        service=self._service,
        request=list_req,
        limit=args.limit,
        batch_size=args.page_size,
        field='streamObjects',
        batch_size_attribute='pageSize')

  def Lookup(self, project_id, stream_id, args):
    """Lookup a stream object.

    Args:
      project_id:
      stream_id:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      StreamObject: the looked up stream object.
    """
    object_identifier = self._messages.SourceObjectIdentifier()
    if args.oracle_schema:
      object_identifier.oracleIdentifier = self._messages.OracleObjectIdentifier(
          schema=args.oracle_schema, table=args.oracle_table)
    elif args.mysql_database:
      object_identifier.mysqlIdentifier = self._messages.MysqlObjectIdentifier(
          database=args.mysql_database, table=args.mysql_table)
    elif args.postgresql_schema:
      object_identifier.postgresqlIdentifier = self._messages.PostgresqlObjectIdentifier(
          schema=args.postgresql_schema, table=args.postgresql_table)

    stream_ref = self._resource_parser.Create(
        'datastream.projects.locations.streams',
        projectsId=project_id,
        streamsId=stream_id,
        locationsId=args.location)

    lookup_req_type = self._messages.DatastreamProjectsLocationsStreamsObjectsLookupRequest
    lookup_req = lookup_req_type(
        lookupStreamObjectRequest=self._messages.LookupStreamObjectRequest(
            sourceObjectIdentifier=object_identifier),
        parent=stream_ref.RelativeName())
    return self._service.Lookup(lookup_req)

  def GetUri(self, name):
    """Get the URL string for a stream object.

    Args:
      name: stream object's full name.

    Returns:
      URL of the stream object resource
    """

    uri = self._resource_parser.ParseRelativeName(
        name, collection='datastream.projects.locations.streams.objects')
    return uri.SelfLink()

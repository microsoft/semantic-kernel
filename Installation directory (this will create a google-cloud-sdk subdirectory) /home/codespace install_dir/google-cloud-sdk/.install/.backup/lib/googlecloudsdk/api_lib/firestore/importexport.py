# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Useful commands for interacting with the Cloud Firestore Import/Export API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import api_utils


def _GetDatabaseService():
  """Returns the service for interacting with the Datastore Admin service."""
  return api_utils.GetClient().projects_databases


def GetExportDocumentsRequest(
    database,
    output_uri_prefix,
    namespace_ids=None,
    collection_ids=None,
    snapshot_time=None,
):
  """Returns a request for a Firestore Admin Export.

  Args:
    database: the database id to export, a string.
    output_uri_prefix: the output GCS path prefix, a string.
    namespace_ids: a string list of namespace ids to export.
    collection_ids: a string list of collection ids to export.
    snapshot_time: the version of the database to export, as string in
      google-datetime format.

  Returns:
    an ExportDocumentsRequest message.
  """
  messages = api_utils.GetMessages()
  export_request = messages.GoogleFirestoreAdminV1ExportDocumentsRequest(
      outputUriPrefix=output_uri_prefix,
      namespaceIds=namespace_ids if namespace_ids else [],
      collectionIds=collection_ids if collection_ids else [],
      snapshotTime=snapshot_time,
  )

  request = messages.FirestoreProjectsDatabasesExportDocumentsRequest(
      name=database, googleFirestoreAdminV1ExportDocumentsRequest=export_request
  )
  return request


def GetImportDocumentsRequest(
    database, input_uri_prefix, namespace_ids=None, collection_ids=None
):
  """Returns a request for a Firestore Admin Import.

  Args:
    database: the database id to import, a string.
    input_uri_prefix: the location of the GCS export files, a string.
    namespace_ids: a string list of namespace ids to import.
    collection_ids: a string list of collection ids to import.

  Returns:
    an ImportDocumentsRequest message.
  """
  messages = api_utils.GetMessages()
  request_class = messages.GoogleFirestoreAdminV1ImportDocumentsRequest

  kwargs = {'inputUriPrefix': input_uri_prefix}
  if collection_ids:
    kwargs['collectionIds'] = collection_ids

  if namespace_ids:
    kwargs['namespaceIds'] = namespace_ids

  import_request = request_class(**kwargs)

  return messages.FirestoreProjectsDatabasesImportDocumentsRequest(
      name=database, googleFirestoreAdminV1ImportDocumentsRequest=import_request
  )


def Export(
    project,
    database,
    output_uri_prefix,
    namespace_ids,
    collection_ids,
    snapshot_time,
):
  """Performs a Firestore Admin Export.

  Args:
    project: the project id to export, a string.
    database: the databae id to import, a string.
    output_uri_prefix: the output GCS path prefix, a string.
    namespace_ids: a string list of namespace ids to import.
    collection_ids: a string list of collections to export.
    snapshot_time: the version of the database to export, as string in
      google-datetime format.

  Returns:
    an Operation.
  """
  dbname = 'projects/{}/databases/{}'.format(project, database)
  return _GetDatabaseService().ExportDocuments(
      GetExportDocumentsRequest(
          database=dbname,
          output_uri_prefix=output_uri_prefix,
          namespace_ids=namespace_ids,
          collection_ids=collection_ids,
          snapshot_time=snapshot_time,
      )
  )


def Import(project, database, input_uri_prefix, namespace_ids, collection_ids):
  """Performs a Firestore Admin v1 Import.

  Args:
    project: the project id to import, a string.
    database: the databae id to import, a string.
    input_uri_prefix: the input uri prefix of the exported files, a string.
    namespace_ids: a string list of namespace ids to import.
    collection_ids: a string list of collections to import.

  Returns:
    an Operation.
  """
  dbname = 'projects/{}/databases/{}'.format(project, database)
  return _GetDatabaseService().ImportDocuments(
      GetImportDocumentsRequest(
          database=dbname,
          input_uri_prefix=input_uri_prefix,
          namespace_ids=namespace_ids,
          collection_ids=collection_ids,
      )
  )

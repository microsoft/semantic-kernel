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
"""Useful commands for interacting with the Cloud Firestore Indexes API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.firestore import api_utils


def _GetIndexService():
  """Returns the Firestore Index service for interacting with the Firestore Admin service."""
  return api_utils.GetClient().projects_databases_collectionGroups_indexes


def CreateIndex(project, database, collection_id, index):
  """Performs a Firestore Admin v1 Index Creation.

  Args:
    project: the project of the database of the index, a string.
    database: the database id of the index, a string.
    collection_id: the current group of the index, a string.
    index: the index to create, a googleFirestoreAdminV1Index message.

  Returns:
    an Operation.
  """
  messages = api_utils.GetMessages()
  return _GetIndexService().Create(
      messages.FirestoreProjectsDatabasesCollectionGroupsIndexesCreateRequest(
          parent='projects/{}/databases/{}/collectionGroups/{}'.format(
              project, database, collection_id
          ),
          googleFirestoreAdminV1Index=index
      )
  )


def ListIndexes(project, database):
  """Performs a Firestore Admin v1 Index list.

  Args:
    project: the project of the database of the index, a string.
    database: the database id of the index, a string.

  Returns:
    a list of Indexes.
  """
  messages = api_utils.GetMessages()
  return _GetIndexService().List(
      messages.FirestoreProjectsDatabasesCollectionGroupsIndexesListRequest(
          parent='projects/{}/databases/{}/collectionGroups/-'.format(
              project, database
          ),
      )
  )

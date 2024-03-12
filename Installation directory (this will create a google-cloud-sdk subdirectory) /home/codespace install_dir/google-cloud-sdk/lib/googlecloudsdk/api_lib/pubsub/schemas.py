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
"""Utilities for Cloud Pub/Sub Schemas API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.pubsub.util import InvalidArgumentError


def NoRevisionIdSpecified():
  return InvalidArgumentError(
      'The schema name must include a revision-id of the format:'
      ' SCHEMA_NAME@REVISION_ID.'
  )


def CheckRevisionIdInSchemaPath(schema_ref):
  find_id = schema_ref.split('@')
  return len(find_id) > 1


def InvalidSchemaType():
  return InvalidArgumentError(
      'The schema type must be either AVRO or PROTOCOL-BUFFER.'
  )


def ParseSchemaType(messages, schema_type):
  type_str = schema_type.lower()
  if type_str == 'protocol-buffer' or type_str == 'protocol_buffer':
    return messages.Schema.TypeValueValuesEnum.PROTOCOL_BUFFER
  elif type_str == 'avro':
    return messages.Schema.TypeValueValuesEnum.AVRO
  raise InvalidSchemaType()


def GetClientInstance(no_http=False):
  return apis.GetClientInstance('pubsub', 'v1', no_http=no_http)


def GetMessagesModule(client=None):
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


class SchemasClient(object):
  """Client for schemas service in the Cloud Pub/Sub API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._service = self.client.projects_schemas

  def Commit(self, schema_ref, schema_definition, schema_type):
    """Commits a revision for a Schema.

    Args:
      schema_ref: The full schema_path.
      schema_definition: The new schema definition to commit.
      schema_type: The type of the schema (avro or protocol-buffer).

    Returns:
    Schema: the committed Schema revision
    """
    schema = self.messages.Schema(
        name=schema_ref,
        type=ParseSchemaType(self.messages, schema_type),
        definition=schema_definition,
    )
    commit_req = self.messages.PubsubProjectsSchemasCommitRequest(
        commitSchemaRequest=self.messages.CommitSchemaRequest(schema=schema),
        name=schema_ref,
    )
    return self._service.Commit(commit_req)

  def Rollback(self, schema_ref, revision_id):
    """Rolls back to a previous schema revision.

    Args:
      schema_ref: The path of the schema to rollback.
      revision_id: The revision_id to rollback to.

    Returns:
    Schema: the new schema revision you have rolled back to.

    Raises:
      InvalidArgumentError: If no revision_id is provided.
    """
    rollback_req = self.messages.PubsubProjectsSchemasRollbackRequest(
        rollbackSchemaRequest=self.messages.RollbackSchemaRequest(
            revisionId=revision_id
        ),
        name=schema_ref,
    )
    return self._service.Rollback(rollback_req)

  def DeleteRevision(self, schema_ref):
    """Deletes a schema revision.

    Args:
      schema_ref: The path of the schema, with the revision_id.

    Returns:
    Schema: the deleted schema revision.
    """
    if not CheckRevisionIdInSchemaPath(schema_ref):
      raise NoRevisionIdSpecified()

    delete_revision_req = (
        self.messages.PubsubProjectsSchemasDeleteRevisionRequest(
            name=schema_ref
        )
    )
    return self._service.DeleteRevision(delete_revision_req)

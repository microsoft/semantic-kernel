# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Spanner database sessions API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import exceptions as apitools_exceptions
from apitools.base.py import extra_types
from apitools.base.py import http_wrapper
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.spanner.sql import QueryHasDml


def CheckResponse(response):
  """Wrap http_wrapper.CheckResponse to skip retry on 501."""
  if response.status_code == 501:
    raise apitools_exceptions.HttpError.FromResponse(response)
  return http_wrapper.CheckResponse(response)


def Create(database_ref, creator_role=None):
  """Create a database session.

  Args:
    database_ref: String, The database in which the new session is created.
    creator_role: String, The database role which created this session.

  Returns:
    Newly created session.
  """
  client = _GetClientInstance('spanner', 'v1', None)
  msgs = apis.GetMessagesModule('spanner', 'v1')
  if creator_role is None:
    req = msgs.SpannerProjectsInstancesDatabasesSessionsCreateRequest(
        database=database_ref.RelativeName())
  else:
    create_session_request = msgs.CreateSessionRequest(
        session=msgs.Session(creatorRole=creator_role))
    req = msgs.SpannerProjectsInstancesDatabasesSessionsCreateRequest(
        createSessionRequest=create_session_request,
        database=database_ref.RelativeName())
  return client.projects_instances_databases_sessions.Create(req)


def List(database_ref, server_filter=None):
  """Lists all active sessions on the given database."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesSessionsListRequest(
      database=database_ref.RelativeName(), filter=server_filter)

  return list_pager.YieldFromList(
      client.projects_instances_databases_sessions,
      req,
      # There is a batch_size_attribute ('pageSize') but we want to yield as
      # many results as possible per request.
      batch_size_attribute=None,
      field='sessions')


def Delete(session_ref):
  """Delete a database session."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstancesDatabasesSessionsDeleteRequest(
      name=session_ref.RelativeName())
  return client.projects_instances_databases_sessions.Delete(req)


def _GetClientInstance(api_name, api_version, http_timeout_sec=None):
  client = apis.GetClientInstance(
      api_name, api_version, http_timeout_sec=http_timeout_sec)
  client.check_response_func = CheckResponse
  return client


def ExecuteSql(sql, query_mode, session_ref, read_only_options=None,
               request_options=None, enable_partitioned_dml=False,
               http_timeout_sec=None):
  """Execute an SQL command.

  Args:
    sql: String, The SQL to execute.
    query_mode: String, The mode in which to run the query. Must be one of
      'NORMAL', 'PLAN', or 'PROFILE'
    session_ref: Session, Indicates that the repo should be created if it does
      not exist.
    read_only_options: The ReadOnly message for a read-only request. It is
      ignored in a DML request.
    request_options: The RequestOptions message that contains the priority.
    enable_partitioned_dml: Boolean, whether partitioned dml is enabled.
    http_timeout_sec: int, Maximum time in seconds to wait for the SQL query to
      complete.

  Returns:
    (Repo) The capture repository.
  """
  client = _GetClientInstance('spanner', 'v1', http_timeout_sec)
  msgs = apis.GetMessagesModule('spanner', 'v1')
  _RegisterCustomMessageCodec(msgs)

  execute_sql_request = _GetQueryRequest(
      sql,
      query_mode,
      session_ref,
      read_only_options,
      request_options,
      enable_partitioned_dml,
  )
  req = msgs.SpannerProjectsInstancesDatabasesSessionsExecuteSqlRequest(
      session=session_ref.RelativeName(), executeSqlRequest=execute_sql_request)
  resp = client.projects_instances_databases_sessions.ExecuteSql(req)
  if QueryHasDml(sql) and enable_partitioned_dml is False:
    result_set = msgs.ResultSet(metadata=resp.metadata)
    Commit(session_ref, [], result_set.metadata.transaction.id)
  return resp


def _RegisterCustomMessageCodec(msgs):
  """Register custom message code.

  Args:
    msgs: Spanner v1 messages.
  """
  # TODO(b/33482229): remove this workaround
  def _ToJson(msg):
    return extra_types.JsonProtoEncoder(
        extra_types.JsonArray(entries=msg.entry))
  def _FromJson(data):
    return msgs.ResultSet.RowsValueListEntry(
        entry=extra_types.JsonProtoDecoder(data).entries)
  encoding.RegisterCustomMessageCodec(
      encoder=_ToJson, decoder=_FromJson)(
          msgs.ResultSet.RowsValueListEntry)


def _GetQueryRequest(sql,
                     query_mode,
                     session_ref=None,
                     read_only_options=None,
                     request_options=None,
                     enable_partitioned_dml=False):
  """Formats the request based on whether the statement contains DML.

  Args:
    sql: String, The SQL to execute.
    query_mode: String, The mode in which to run the query. Must be one of
      'NORMAL', 'PLAN', or 'PROFILE'
    session_ref: Reference to the session.
    read_only_options: The ReadOnly message for a read-only request. It is
      ignored in a DML request.
    request_options: The RequestOptions message that contains the priority.
    enable_partitioned_dml: Boolean, whether partitioned dml is enabled.

  Returns:
    ExecuteSqlRequest parameters
  """
  msgs = apis.GetMessagesModule('spanner', 'v1')

  if enable_partitioned_dml is True:
    transaction = _GetPartitionedDmlTransaction(session_ref)
  elif QueryHasDml(sql):
    transaction_options = msgs.TransactionOptions(readWrite=msgs.ReadWrite())
    transaction = msgs.TransactionSelector(begin=transaction_options)
  else:
    transaction_options = msgs.TransactionOptions(
        readOnly=read_only_options)
    transaction = msgs.TransactionSelector(singleUse=transaction_options)
  return msgs.ExecuteSqlRequest(
      sql=sql,
      requestOptions=request_options,
      queryMode=msgs.ExecuteSqlRequest.QueryModeValueValuesEnum(query_mode),
      transaction=transaction)


def _GetPartitionedDmlTransaction(session_ref):
  """Creates a transaction for Partitioned DML.

  Args:
    session_ref: Reference to the session.

  Returns:
    TransactionSelector with the id property.
  """
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')

  transaction_options = msgs.TransactionOptions(
      partitionedDml=msgs.PartitionedDml())
  begin_transaction_req = msgs.BeginTransactionRequest(
      options=transaction_options)
  req = msgs.SpannerProjectsInstancesDatabasesSessionsBeginTransactionRequest(
      beginTransactionRequest=begin_transaction_req,
      session=session_ref.RelativeName())
  resp = client.projects_instances_databases_sessions.BeginTransaction(req)
  return msgs.TransactionSelector(id=resp.id)


def Commit(session_ref, mutations, transaction_id=None):
  """Commit a transaction through a session.

  In Cloud Spanner, each session can have at most one active transaction at a
  time. In order to avoid retrying aborted transactions by accident, this
  request uses a temporary single use transaction instead of a previously
  started transaction to execute the mutations.
  Note: this commit is non-idempotent.

  Args:
    session_ref: Session, through which the transaction would be committed.
    mutations: A list of mutations, each represents a modification to one or
        more Cloud Spanner rows.
    transaction_id: An optional string for the transaction id.

  Returns:
    The Cloud Spanner timestamp at which the transaction committed.
  """
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')

  if transaction_id is not None:
    req = msgs.SpannerProjectsInstancesDatabasesSessionsCommitRequest(
        session=session_ref.RelativeName(),
        commitRequest=msgs.CommitRequest(
            mutations=mutations, transactionId=transaction_id))
  else:
    req = msgs.SpannerProjectsInstancesDatabasesSessionsCommitRequest(
        session=session_ref.RelativeName(),
        commitRequest=msgs.CommitRequest(
            mutations=mutations,
            singleUseTransaction=msgs.TransactionOptions(
                readWrite=msgs.ReadWrite())))
  return client.projects_instances_databases_sessions.Commit(req)


class MutationFactory(object):
  """Factory that creates and returns a mutation object in Cloud Spanner.

  A Mutation represents a sequence of inserts, updates and deletes that can be
  applied to rows and tables in a Cloud Spanner database.
  """
  msgs = apis.GetMessagesModule('spanner', 'v1')

  @classmethod
  def Insert(cls, table, data):
    """Constructs an INSERT mutation, which inserts a new row in a table.

    Args:
      table: String, the name of the table.
      data: A collections.OrderedDict, the keys of which are the column names
        and values are the column values to be inserted.

    Returns:
      An insert mutation operation.
    """
    return cls.msgs.Mutation(insert=cls._GetWrite(table, data))

  @classmethod
  def Update(cls, table, data):
    """Constructs an UPDATE mutation, which updates a row in a table.

    Args:
      table: String, the name of the table.
      data: An ordered dictionary where the keys are the column names and values
        are the column values to be updated.

    Returns:
      An update mutation operation.
    """
    return cls.msgs.Mutation(update=cls._GetWrite(table, data))

  @classmethod
  def Delete(cls, table, keys):
    """Constructs a DELETE mutation, which deletes a row in a table.

    Args:
      table: String, the name of the table.
      keys: String list, the primary key values of the row to delete.

    Returns:
      A delete mutation operation.
    """
    return cls.msgs.Mutation(delete=cls._GetDelete(table, keys))

  @classmethod
  def _GetWrite(cls, table, data):
    """Constructs Write object, which is needed for insert/update operations."""
    # TODO(b/33482229): a workaround to handle JSON serialization
    def _ToJson(msg):
      return extra_types.JsonProtoEncoder(
          extra_types.JsonArray(entries=msg.entry))

    encoding.RegisterCustomMessageCodec(
        encoder=_ToJson, decoder=None)(
            cls.msgs.Write.ValuesValueListEntry)

    json_columns = table.GetJsonData(data)
    json_column_names = [col.col_name for col in json_columns]
    json_column_values = [col.col_value for col in json_columns]

    return cls.msgs.Write(
        columns=json_column_names,
        table=table.name,
        values=[cls.msgs.Write.ValuesValueListEntry(entry=json_column_values)])

  @classmethod
  def _GetDelete(cls, table, keys):
    """Constructs Delete object, which is needed for delete operation."""

    # TODO(b/33482229): a workaround to handle JSON serialization
    def _ToJson(msg):
      return extra_types.JsonProtoEncoder(
          extra_types.JsonArray(entries=msg.entry))

    encoding.RegisterCustomMessageCodec(
        encoder=_ToJson, decoder=None)(
            cls.msgs.KeySet.KeysValueListEntry)

    key_set = cls.msgs.KeySet(keys=[
        cls.msgs.KeySet.KeysValueListEntry(entry=table.GetJsonKeys(keys))
    ])

    return cls.msgs.Delete(table=table.name, keySet=key_set)

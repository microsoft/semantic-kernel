# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Common command-agnostic utility functions for sql import commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def ParseBakType(sql_messages, bak_type):
  if bak_type is None:
    return (
        sql_messages.ImportContext.BakImportOptionsValue.BakTypeValueValuesEnum.FULL
    )
  return sql_messages.ImportContext.BakImportOptionsValue.BakTypeValueValuesEnum.lookup_by_name(
      bak_type.upper()
  )


def SqlImportContext(
    sql_messages, uri, database=None, user=None, parallel=False, threads=None
):
  """Generates the ImportContext for the given args, for importing from SQL.

  Args:
    sql_messages: module, The messages module that should be used.
    uri: The URI of the bucket to import from; the output of the 'uri' arg.
    database: The database to import to; the output of the '--database' flag.
    user: The Postgres user to import as; the output of the '--user' flag.
    parallel: Whether to use parallel import or not; the output of the
      '--parallel' flag.
    threads: The number of threads to use; the output of the '--threads' flag.
      Only applicable for parallel import.

  Returns:
    ImportContext, for use in InstancesImportRequest.importContext.
  """
  if parallel:
    return sql_messages.ImportContext(
        kind='sql#importContext',
        uri=uri,
        database=database,
        fileType=sql_messages.ImportContext.FileTypeValueValuesEnum.SQL,
        importUser=user,
        sqlImportOptions=sql_messages.ImportContext.SqlImportOptionsValue(
            parallel=parallel, threads=threads
        ),
    )
  else:
    return sql_messages.ImportContext(
        kind='sql#importContext',
        uri=uri,
        database=database,
        fileType=sql_messages.ImportContext.FileTypeValueValuesEnum.SQL,
        importUser=user,
        sqlImportOptions=sql_messages.ImportContext.SqlImportOptionsValue(
            threads=threads
        ),
    )


def CsvImportContext(sql_messages,
                     uri,
                     database,
                     table,
                     columns=None,
                     user=None,
                     quote=None,
                     escape=None,
                     fields_terminated_by=None,
                     lines_terminated_by=None):
  """Generates the ImportContext for the given args, for importing from CSV.

  Args:
    sql_messages: module, The messages module that should be used.
    uri: The URI of the bucket to import from; the output of the 'uri' arg.
    database: The database to import into; the output of the '--database' flag.
    table: The table to import into; the output of the '--table' flag.
    columns: The CSV columns to import form; the output of the '--columns' flag.
    user: The Postgres user to import as; the output of the '--user' flag.
    quote: character in Hex. The quote character for CSV format; the output of
      the '--quote' flag.
    escape: character in Hex. The escape character for CSV format; the output of
      the '--escape' flag.
    fields_terminated_by: character in Hex. The fields delimiter character for
      CSV format; the output of the '--fields-terminated-by' flag.
    lines_terminated_by: character in Hex. The lines delimiter character for CSV
      format; the output of the '--lines-terminated-by' flag.

  Returns:
    ImportContext, for use in InstancesImportRequest.importContext.
  """
  return sql_messages.ImportContext(
      kind='sql#importContext',
      csvImportOptions=sql_messages.ImportContext.CsvImportOptionsValue(
          columns=columns or [], table=table,
          quoteCharacter=quote,
          escapeCharacter=escape,
          fieldsTerminatedBy=fields_terminated_by,
          linesTerminatedBy=lines_terminated_by),
      uri=uri,
      database=database,
      fileType=sql_messages.ImportContext.FileTypeValueValuesEnum.CSV,
      importUser=user)


def BakImportContext(
    sql_messages,
    uri,
    database,
    cert_path,
    pvk_path,
    pvk_password,
    striped,
    no_recovery,
    recovery_only,
    bak_type,
    stop_at,
    stop_at_mark,
):
  """Generates the ImportContext for the given args, for importing from BAK.

  Args:
    sql_messages: module, The messages module that should be used.
    uri: The URI of the bucket to import from; the output of the `uri` arg.
    database: The database to import to; the output of the `--database` flag.
    cert_path: The certificate used for encrypted .bak; the output of the
      `--cert-path` flag.
    pvk_path: The private key used for encrypted .bak; the output of the
      `--pvk-path` flag.
    pvk_password: The private key password used for encrypted .bak; the output
      of the `--pvk-password` or `--prompt-for-pvk-password` flag.
    striped: Whether or not the import is striped.
    no_recovery: Whether the import executes with NORECOVERY keyword.
    recovery_only: Whether the import skip download and bring database online.
    bak_type: Type of the bak file.
    stop_at: Equivalent to SQL Server STOPAT keyword.
    stop_at_mark: Equivalent to SQL Server STOPATMARK keyword.

  Returns:
    ImportContext, for use in InstancesImportRequest.importContext.
  """
  bak_import_options = None
  if cert_path and pvk_path and pvk_password:
    bak_import_options = sql_messages.ImportContext.BakImportOptionsValue(
        encryptionOptions=sql_messages.ImportContext.BakImportOptionsValue
        .EncryptionOptionsValue(
            certPath=cert_path, pvkPath=pvk_path, pvkPassword=pvk_password))
  else:
    bak_import_options = sql_messages.ImportContext.BakImportOptionsValue()

  if striped:
    bak_import_options.striped = striped

  bak_import_options.noRecovery = no_recovery
  bak_import_options.recoveryOnly = recovery_only
  bak_import_options.bakType = ParseBakType(sql_messages, bak_type)
  if stop_at is not None:
    bak_import_options.stopAt = stop_at.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
  bak_import_options.stopAtMark = stop_at_mark

  return sql_messages.ImportContext(
      kind='sql#importContext',
      uri=uri,
      database=database,
      fileType=sql_messages.ImportContext.FileTypeValueValuesEnum.BAK,
      bakImportOptions=bak_import_options)

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
"""Common command-agnostic utility functions for sql export commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def ParseBakType(sql_messages, bak_type):
  if bak_type is None:
    return (
        sql_messages.ExportContext.BakExportOptionsValue.BakTypeValueValuesEnum.FULL
    )
  return sql_messages.ExportContext.BakExportOptionsValue.BakTypeValueValuesEnum.lookup_by_name(
      bak_type.upper()
  )


def SqlExportContext(
    sql_messages,
    uri,
    database=None,
    table=None,
    offload=False,
    parallel=False,
    threads=None,
):
  """Generates the ExportContext for the given args, for exporting to SQL.

  Args:
    sql_messages: module, The messages module that should be used.
    uri: The URI of the bucket to export to; the output of the 'uri' arg.
    database: The list of databases to export from; the output of the
      '--database' flag.
    table: The list of tables to export from; the output of the '--table' flag.
    offload: bool, The export offload flag.
    parallel: Whether to use parallel export or not.
    threads: The number of threads to use. Only applicable for parallel export.

  Returns:
    ExportContext, for use in InstancesExportRequest.exportContext.
  """
  if parallel:
    return sql_messages.ExportContext(
        kind='sql#exportContext',
        uri=uri,
        databases=database or [],
        offload=offload,
        fileType=sql_messages.ExportContext.FileTypeValueValuesEnum.SQL,
        sqlExportOptions=sql_messages.ExportContext.SqlExportOptionsValue(
            tables=table or [], parallel=parallel, threads=threads
        ),
    )
  else:
    return sql_messages.ExportContext(
        kind='sql#exportContext',
        uri=uri,
        databases=database or [],
        offload=offload,
        fileType=sql_messages.ExportContext.FileTypeValueValuesEnum.SQL,
        sqlExportOptions=sql_messages.ExportContext.SqlExportOptionsValue(
            tables=table or [], threads=threads
        ),
    )


def CsvExportContext(sql_messages,
                     uri,
                     database=None,
                     query=None,
                     offload=False,
                     quote=None,
                     escape=None,
                     fields_terminated_by=None,
                     lines_terminated_by=None):
  """Generates the ExportContext for the given args, for exporting to CSV.

  Args:
    sql_messages: module, The messages module that should be used.
    uri: The URI of the bucket to export to; the output of the 'uri' arg.
    database: The list of databases to export from; the output of the
      '--database' flag.
    query: The query string to use to generate the table; the output of the
      '--query' flag.
    offload: bool, The export offload flag.
    quote: character in Hex. The quote character for CSV format; the output of
      the '--quote' flag.
    escape: character in Hex. The escape character for CSV format; the output of
      the '--escape' flag.
    fields_terminated_by: character in Hex. The fields delimiter character for
      CSV format; the output of the '--fields-terminated-by' flag.
    lines_terminated_by: character in Hex. The lines delimiter character for CSV
      format; the output of the '--lines-terminated-by' flag.

  Returns:
    ExportContext, for use in InstancesExportRequest.exportContext.
  """
  return sql_messages.ExportContext(
      kind='sql#exportContext',
      uri=uri,
      databases=database or [],
      offload=offload,
      fileType=sql_messages.ExportContext.FileTypeValueValuesEnum.CSV,
      csvExportOptions=sql_messages.ExportContext.CsvExportOptionsValue(
          selectQuery=query,
          quoteCharacter=quote,
          escapeCharacter=escape,
          fieldsTerminatedBy=fields_terminated_by,
          linesTerminatedBy=lines_terminated_by))


def BakExportContext(
    sql_messages,
    uri,
    database,
    stripe_count,
    striped,
    bak_type,
    differential_base,
):
  """Generates the ExportContext for the given args, for exporting to BAK.

  Args:
    sql_messages: module, The messages module that should be used.
    uri: The URI of the bucket to export to; the output of the 'uri' arg.
    database: The list of databases to export from; the output of the
      '--database' flag.
    stripe_count: How many stripes to perform the export with.
    striped: Whether the export should be striped.
    bak_type: Type of bak file that will be exported. SQL Server only.
    differential_base: Whether the bak file export can be used as differential
      base for future differential backup. SQL Server only.

  Returns:
    ExportContext, for use in InstancesExportRequest.exportContext.
  """
  bak_export_options = sql_messages.ExportContext.BakExportOptionsValue()
  if striped is not None:
    bak_export_options.striped = striped
  if stripe_count is not None:
    bak_export_options.stripeCount = stripe_count

  bak_export_options.differentialBase = differential_base
  bak_export_options.bakType = ParseBakType(sql_messages, bak_type)

  return sql_messages.ExportContext(
      kind='sql#exportContext',
      uri=uri,
      databases=database,
      fileType=sql_messages.ExportContext.FileTypeValueValuesEnum.BAK,
      bakExportOptions=bak_export_options)

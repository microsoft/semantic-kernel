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
"""Common utility functions for sql export commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import export_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def AddBaseExportFlags(
    parser,
    gz_supported=True,
    database_required=False,
    database_help_text=flags.DEFAULT_DATABASE_LIST_EXPORT_HELP_TEXT):
  """Adds the base export flags to the parser.

  Args:
    parser: The current argparse parser to add these flags to.
    gz_supported: Boolean, specifies whether gz compression is supported.
    database_required: Boolean, specifies whether the database flag is required.
    database_help_text: String, specifies the help text for the database flag.
  """
  base.ASYNC_FLAG.AddToParser(parser)
  flags.AddInstanceArgument(parser)

  uri_help_text = ('The path to the file in Google Cloud Storage where the '
                   'export will be stored. The URI is in the form '
                   'gs://bucketName/fileName. If the file already exists, the '
                   'operation fails.')
  if gz_supported:
    uri_help_text = uri_help_text + (' If the filename ends with .gz, the '
                                     'contents are compressed.')
  flags.AddUriArgument(parser, uri_help_text)
  flags.AddDatabaseList(parser, database_help_text, database_required)


def RunExportCommand(args, client, export_context):
  """Exports data from a Cloud SQL instance.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.
    client: SqlClient instance, with sql_client and sql_messages props, for use
      in generating messages and making API calls.
    export_context: ExportContext; format-specific export metadata.

  Returns:
    A dict representing the export operation resource, if '--async' is used,
    or else None.

  Raises:
    HttpException: An HTTP error response was received while executing API
        request.
    ToolException: An error other than HTTP error occurred while executing the
        command.
  """
  sql_client = client.sql_client
  sql_messages = client.sql_messages

  validate.ValidateInstanceName(args.instance)
  instance_ref = client.resource_parser.Parse(
      args.instance,
      params={'project': properties.VALUES.core.project.GetOrFail},
      collection='sql.instances')

  export_request = sql_messages.SqlInstancesExportRequest(
      instance=instance_ref.instance,
      project=instance_ref.project,
      instancesExportRequest=sql_messages.InstancesExportRequest(
          exportContext=export_context))

  result_operation = sql_client.instances.Export(export_request)

  operation_ref = client.resource_parser.Create(
      'sql.operations',
      operation=result_operation.name,
      project=instance_ref.project)

  if args.async_:
    return sql_client.operations.Get(
        sql_messages.SqlOperationsGetRequest(
            project=operation_ref.project, operation=operation_ref.operation))

  operations.OperationsV1Beta4.WaitForOperation(sql_client, operation_ref,
                                                'Exporting Cloud SQL instance')

  log.status.write('Exported [{instance}] to [{bucket}].\n'.format(
      instance=instance_ref, bucket=args.uri))

  return None


def RunSqlExportCommand(args, client):
  """Exports data from a Cloud SQL instance to a MySQL dump file.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.
    client: SqlClient instance, with sql_client and sql_messages props, for use
      in generating messages and making API calls.

  Returns:
    A dict object representing the operations resource describing the export
    operation if the export was successful.
  """
  sql_export_context = export_util.SqlExportContext(
      client.sql_messages,
      args.uri,
      args.database,
      args.table,
      offload=args.offload,
      parallel=args.parallel,
      threads=args.threads,
  )
  if args.offload:
    log.status.write(
        'Serverless exports cost extra. See the pricing page for more information: https://cloud.google.com/sql/pricing.\n'
    )
  return RunExportCommand(args, client, sql_export_context)


def RunCsvExportCommand(args, client):
  """Exports data from a Cloud SQL instance to a CSV file.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.
    client: SqlClient instance, with sql_client and sql_messages props, for use
      in generating messages and making API calls.

  Returns:
    A dict object representing the operations resource describing the export
    operation if the export was successful.
  """
  csv_export_context = export_util.CsvExportContext(
      client.sql_messages,
      args.uri,
      args.database,
      args.query,
      offload=args.offload,
      quote=args.quote,
      escape=args.escape,
      fields_terminated_by=args.fields_terminated_by,
      lines_terminated_by=args.lines_terminated_by)
  if args.offload:
    log.status.write(
        'Serverless exports cost extra. See the pricing page for more information: https://cloud.google.com/sql/pricing.\n'
    )
  return RunExportCommand(args, client, csv_export_context)


def RunBakExportCommand(args, client):
  """Export data from a Cloud SQL instance to a SQL Server BAK file.

  Args:
    args: argparse.Namespace, The arguments that this command was invoked with.
    client: SqlClient instance, with sql_client and sql_messages props, for use
      in generating messages and making API calls.

  Returns:
    A dict object representing the operations resource describing the export
    operation if the export was successful.
  """
  sql_export_context = export_util.BakExportContext(
      client.sql_messages,
      args.uri,
      args.database,
      args.stripe_count,
      args.striped,
      args.bak_type,
      args.differential_base,
  )
  return RunExportCommand(args, client, sql_export_context)

# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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
"""Exports data from a Cloud SQL instance.

Exports data from a Cloud SQL instance to a Google Cloud Storage bucket as
a MySQL dump file.
"""
# TODO(b/67459595): Deprecate this command when `sql export` goes to GA.


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib import deprecation_utils
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
@deprecation_utils.DeprecateCommandAtVersion(
    remove_version='205.0.0', remove=False, alt_command='gcloud sql export sql')
class Export(base.Command):
  """Exports data from a Cloud SQL instance.

  Exports data from a Cloud SQL instance to a Google Cloud Storage
  bucket as a MySQL dump file.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        'instance',
        completer=flags.InstanceCompleter,
        help='Cloud SQL instance ID.')
    parser.add_argument(
        'uri',
        help='The path to the file in Google Cloud Storage where the export '
        'will be stored. The URI is in the form gs://bucketName/fileName. '
        'If the file already exists, the operation fails. If the filename '
        'ends with .gz, the contents are compressed.')
    flags.AddDatabaseList(parser, flags.DEFAULT_DATABASE_LIST_EXPORT_HELP_TEXT)
    parser.add_argument(
        '--table',
        '-t',
        type=arg_parsers.ArgList(min_length=1),
        metavar='TABLE',
        required=False,
        help='Tables to export from the specified database. If you specify '
        'tables, specify one and only one database. For Postgres instances, '
        'only one table can be exported at a time.')

  def Run(self, args):
    """Exports data from a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the export
      operation if the export was successful.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')

    # TODO(b/36051079): add support for CSV exporting.
    export_request = sql_messages.SqlInstancesExportRequest(
        instance=instance_ref.instance,
        project=instance_ref.project,
        instancesExportRequest=sql_messages.InstancesExportRequest(
            exportContext=sql_messages.ExportContext(
                kind='sql#exportContext',
                uri=args.uri,
                databases=args.database or [],
                fileType=sql_messages.ExportContext.FileTypeValueValuesEnum.SQL,
                sqlExportOptions=(
                    sql_messages.ExportContext.SqlExportOptionsValue(
                        tables=args.table or [],)),
            ),),
    )

    result_operation = sql_client.instances.Export(export_request)

    operation_ref = client.resource_parser.Create(
        'sql.operations',
        operation=result_operation.name,
        project=instance_ref.project)

    if args.async_:
      return sql_client.operations.Get(
          sql_messages.SqlOperationsGetRequest(
              project=operation_ref.project, operation=operation_ref.operation))

    operations.OperationsV1Beta4.WaitForOperation(
        sql_client, operation_ref, 'Exporting Cloud SQL instance')

    log.status.write('Exported [{instance}] to [{bucket}].\n'.format(
        instance=instance_ref, bucket=args.uri))

    return None

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
"""Imports data into a Cloud SQL instance.

Imports data into a Cloud SQL instance from a MySQL dump file in
Google Cloud Storage.
"""
# TODO(b/67917387): Deprecate this command when `sql import` goes to GA.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib import deprecation_utils
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
@deprecation_utils.DeprecateCommandAtVersion(
    remove_version='205.0.0', remove=False, alt_command='gcloud sql import sql')
class Import(base.Command):
  """Imports data into a Cloud SQL instance from Google Cloud Storage.

  Note: authorization is required. For more information on importing data
  into Google Cloud SQL see
  [](https://cloud.google.com/sql/docs/import-export/importing).

  Cloud SQL supports importing CSV files and SQL dump files from both MySQL and
  PostgreSQL. For more information on how to create these export formats, see
  [](https://cloud.google.com/sql/docs/mysql/import-export/creating-sqldump-csv)
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        'instance',
        completer=flags.InstanceCompleter,
        help='Cloud SQL instance ID.')
    parser.add_argument(
        'uri',
        type=str,
        help='Path to the MySQL dump file in Google Cloud Storage from which'
        ' the import is made. The URI is in the form gs://bucketName/fileName.'
        ' Compressed gzip files (.gz) are also supported.')
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddDatabase(parser, flags.DEFAULT_DATABASE_IMPORT_HELP_TEXT)

  def Run(self, args):
    """Imports data into a Cloud SQL instance from Google Cloud Storage.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the import
      operation if the import was successful.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')

    console_io.PromptContinue(
        message='Data from {0} will be imported to {1}.'.format(
            args.uri, args.instance),
        default=True,
        cancel_on_no=True)

    import_request = sql_messages.SqlInstancesImportRequest(
        instance=instance_ref.instance,
        project=instance_ref.project,
        instancesImportRequest=sql_messages.InstancesImportRequest(
            importContext=sql_messages.ImportContext(
                kind='sql#importContext',
                uri=args.uri,
                database=args.database,
                fileType=sql_messages.ImportContext.FileTypeValueValuesEnum.SQL,
            ),),
    )

    result_operation = sql_client.instances.Import(import_request)

    operation_ref = client.resource_parser.Create(
        'sql.operations',
        operation=result_operation.name,
        project=instance_ref.project)

    if args.async_:
      return sql_client.operations.Get(
          sql_messages.SqlOperationsGetRequest(
              project=operation_ref.project, operation=operation_ref.operation))

    operations.OperationsV1Beta4.WaitForOperation(
        sql_client, operation_ref, 'Importing Cloud SQL instance')

    log.status.write('Imported [{instance}] from [{bucket}].\n'.format(
        instance=instance_ref, bucket=args.uri))

    return None

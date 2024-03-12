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
"""Command to query metadata against Dataproc Metastore services database."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import json

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.metastore import operations_util
from googlecloudsdk.api_lib.metastore import services_util as services_api_util
from googlecloudsdk.api_lib.metastore import util as api_util
from googlecloudsdk.api_lib.storage import storage_api
from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.metastore import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.resource import resource_printer
import six

DETAILED_HELP = {
    'EXAMPLES':
        """\
          To query metadata against a Dataproc Metastore service with the name
          `my-metastore-service` in location `us-central1`, and the sql query
          "show tables;", run:

          $ {command} my-metastore-service --location=us-central1
          --query="show tables;"

        """
}


def AddBaseArgs(parser):
  """Parses provided arguments to add base arguments used for Alpha/Beta/GA.

  Args:
    parser: an argparse argument parser.
  """
  resource_args.AddServiceResourceArg(
      parser, 'to query metadata', plural=False, required=True, positional=True)
  parser.add_argument(
      '--query',
      required=True,
      help="""\
            Use Google Standard SQL query for Cloud Spanner and MySQL query
            syntax for Cloud SQL. Cloud Spanner SQL is described at
            https://cloud.google.com/spanner/docs/query-syntax)"
        """,
  )


@base.UnicodeIsSupported
@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Query(base.Command):
  """Execute a SQL query against a Dataproc Metastore Service's metadata."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """See base class."""
    AddBaseArgs(parser)
    base.FORMAT_FLAG.AddToParser(parser)

  def Run(self, args):
    """Runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    env_ref = args.CONCEPTS.service.Parse()
    operation = None
    try:
      operation = services_api_util.QueryMetadata(
          env_ref.RelativeName(), args.query, release_track=self.ReleaseTrack())
      log.out.Print('with operation [{}]'.format(operation.name))
    except apitools_exceptions.HttpError:
      raise api_util.QueryMetadataError('Query did not succeed.')
    operation_result = None
    try:
      operation_result = operations_util.PollAndReturnOperation(
          operation,
          'Waiting for [{}] to query'.format(env_ref.RelativeName()),
          release_track=self.ReleaseTrack())
    except api_util.OperationError as e:
      log.UpdatedResource(
          env_ref.RelativeName(),
          kind='service',
          is_async=False,
          failed=six.text_type(e))
    if (operation_result is None or
        not operation_result.additionalProperties or
        len(operation_result.additionalProperties) < 2):
      return None
    result_manifest_uri = None
    for message in operation_result.additionalProperties:
      if message.key == 'resultManifestUri':
        result_manifest_uri = message.value.string_value
    if result_manifest_uri is None:
      return None
    gcs_client = storage_api.StorageClient()
    result_manifest_json = json.load(
        io.TextIOWrapper(
            gcs_client.ReadObject(
                storage_util.ObjectReference.FromUrl(result_manifest_uri,
                                                     True)),
            encoding='utf-8'))

    # Query succeed
    log.out.Print(result_manifest_json['status']['message'],
                  result_manifest_uri)
    if not result_manifest_json['filenames']:
      return None
    if len(result_manifest_json['filenames']) > 1:
      log.out.Print('The number of rows exceeds 1000 to display. ' +
                    'Please find more results at the cloud storage location.')
    query_result_file_name = result_manifest_json['filenames'][0]
    return json.load(
        io.TextIOWrapper(
            gcs_client.ReadObject(
                storage_util.ObjectReference.FromUrl(
                    self.ExtractQueryFolderUri(result_manifest_uri) +
                    query_result_file_name, True)),
            encoding='utf-8'))

  def ExtractQueryFolderUri(self, gcs_uri):
    """Returns the folder of query result gcs_uri.

    This takes gcs_uri and alter the filename to /filename[0]
    filename[0] is a string populated by grpc server.
      e.g., given gs://bucket-id/query-results/uuid/result-manifest
      output gs://bucket-id/query-results/uuid//

    Args:
      gcs_uri: the query metadata result gcs uri.
    """
    return gcs_uri[:gcs_uri.rfind('/')] + '//'

  def Display(self, args, result):
    """Displays the server response to a query.

    This is called higher up the stack to over-write default display behavior.
    What gets displayed depends on the mode in which the query was run.

    Args:
      args: The arguments originally passed to the command.
      result: The output of the command before display.
    """
    if not result or 'metadata' not in result or 'columns' not in result[
        'metadata'] or 'rows' not in result:
      return
    fields = [
        field['name'] or '(Unspecified)'
        for field in result['metadata']['columns']
    ]
    # Create the format string we pass to the table layout.
    table_format = ','.join('row.slice({0}).join():label="{1}"'.format(i, f)
                            for i, f in enumerate(fields))
    rows = [{'row': row} for row in result['rows']]
    # Can't use the PrintText method because we want special formatting.
    resource_printer.Print(rows, 'table({0})'.format(table_format), out=log.out)

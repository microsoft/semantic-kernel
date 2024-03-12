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
"""Performs a storage size decrease of a Cloud SQL instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import constants
from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
import six.moves.http_client


# TODO(b/265881192): remove Hidden label once we are ready to launch.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class PerformStorageShrink(base.Command):
  """Performs a storage size decrease of a Cloud SQL instance."""

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
    flags.AddStorageSizeForStorageShrink(parser)

  def Run(self, args):
    """Performs a storage size decrease of a Cloud SQL instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      A dict object representing the operations resource describing the perform
      storage shrink operation if the decrease was successful.

    Raises:
      HttpException: A http error response was received while executing api
          request.
      ResourceNotFoundError: The SQL instance wasn't found.
      RequiredArgumentException: A required argument was not supplied by the
      user, such as omitting --root-password on a SQL Server instance.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances',
    )

    if not console_io.PromptContinue(
        'Confirm that you have already run `gcloud alpha sql instances'
        ' get-storage-shrink-config $instance_name` and understand that this'
        ' operation will restart your database and might take a long time to'
        ' complete (y/n)'
    ):
      return None

    try:
      request = sql_messages.SqlProjectsInstancesPerformDiskShrinkRequest(
          instance=instance_ref.instance,
          project=instance_ref.project,
          performDiskShrinkContext=sql_messages.PerformDiskShrinkContext(
              targetSizeGb=int(args.storage_size / constants.BYTES_TO_GB),
          ),
      )

      result_operation = sql_client.projects_instances.PerformDiskShrink(
          request)

      operation_ref = client.resource_parser.Create(
          'sql.operations',
          operation=result_operation.name,
          project=instance_ref.project)

      if args.async_:
        return {'Name': instance_ref.instance, 'Project': instance_ref.project,
                'OperationId': result_operation.name,
                'Status': result_operation.status}

      operations.OperationsV1Beta4.WaitForOperation(
          sql_client,
          operation_ref,
          'Performing a storage size decrease on a Cloud SQL instance.',
          2147483647,  # 2^31-1
      )

      changed_instance_resource = sql_client.instances.Get(
          sql_messages.SqlInstancesGetRequest(
              project=instance_ref.project, instance=instance_ref.instance))

      return {
          'Name': instance_ref.instance,
          'Project': instance_ref.project,
          'StorageSizeGb': changed_instance_resource.settings.dataDiskSizeGb
          }
    except apitools_exceptions.HttpError as error:
      if error.status_code == six.moves.http_client.FORBIDDEN:
        raise exceptions.ResourceNotFoundError(
            "There's no instance found at {} or you're not authorized to "
            'access it.'.format(instance_ref.RelativeName()))
      raise calliope_exceptions.HttpException(error)

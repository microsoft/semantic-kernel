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
"""Retrieves the minimal storage size a Cloud SQL instance can be shrunk."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties
import six.moves.http_client


# TODO(b/265881192): remove Hidden label once we are ready to launch.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetStorageShrinkConfig(base.Command):
  """Displays the minimum storage size to which a Cloud SQL instance can be decreased.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use it to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument(
        'instance',
        completer=flags.InstanceCompleter,
        help='Cloud SQL instance ID.')

  def Run(self, args):
    """Displays the minimum storage size to which a Cloud SQL instance can be decreased.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A kind string representing the request run and the minimum storage
      size to which a Cloud SQL instance can be decreased.

    Raises:
      HttpException: A http error response was received while executing api
          request.
      ResourceNotFoundError: The SQL instance isn't found.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances')
    try:
      request = sql_messages.SqlProjectsInstancesGetDiskShrinkConfigRequest(
          project=instance_ref.project, instance=instance_ref.instance)
      instance = sql_client.projects_instances.GetDiskShrinkConfig(request)
      return instance
    except apitools_exceptions.HttpError as error:
      if error.status_code == six.moves.http_client.FORBIDDEN:
        raise exceptions.ResourceNotFoundError(
            "There's no instance found at {} or you're not authorized to "
            'access it.'.format(instance_ref.RelativeName()))
      raise calliope_exceptions.HttpException(error)

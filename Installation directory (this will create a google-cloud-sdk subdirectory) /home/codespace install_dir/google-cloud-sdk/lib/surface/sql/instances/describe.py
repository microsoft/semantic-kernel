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
"""Retrieves information about a Cloud SQL instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import exceptions
from googlecloudsdk.api_lib.sql import instances as instance_api_util
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import properties
import six.moves.http_client


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Get(base.DescribeCommand):
  """Displays configuration and metadata about a Cloud SQL instance.

  Displays configuration and metadata about a Cloud SQL instance.

  Information such as instance name, IP address, region, the CA certificate
  and configuration settings will be displayed.
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
    parser.display_info.AddFormat('{0} default'.format(
        flags.INSTANCES_USERLABELS_FORMAT))

  def Run(self, args):
    """Displays configuration and metadata about a Cloud SQL instance.

    Information such as instance name, IP address, region, the CA certificate
    and configuration settings will be displayed.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A DatabaseInstancePresentation object representing the instance resource
      if fetching the instance was successful.
    Raises:
      HttpException: A http error response was received while executing api
          request.
    ResourceNotFoundError: The SQL instance was not found.
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
      instance = sql_client.instances.Get(
          sql_messages.SqlInstancesGetRequest(
              project=instance_ref.project, instance=instance_ref.instance))
      return instance_api_util.DatabaseInstancePresentation(instance)
    except apitools_exceptions.HttpError as error:
      if error.status_code == six.moves.http_client.FORBIDDEN:
        raise exceptions.ResourceNotFoundError(
            'There was no instance found at {} or you are not authorized to '
            'access it.'.format(instance_ref.RelativeName()))
      raise calliope_exceptions.HttpException(error)

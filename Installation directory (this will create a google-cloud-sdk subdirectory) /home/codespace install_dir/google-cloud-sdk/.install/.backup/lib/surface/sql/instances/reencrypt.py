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
"""Reencrypts a Cloud SQL CMEK instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions
from googlecloudsdk.api_lib.sql import api_util
from googlecloudsdk.api_lib.sql import operations
from googlecloudsdk.api_lib.sql import validate
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.sql import flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
import six

DESCRIPTION = """\
    Reencrypt a Cloud SQL CMEK instance with the primary key version.
    """

EXAMPLES_GA = """\
    To reencrypt a Cloud SQL CMEK instance with the primary key version:

    $ {command} instance-foo
    """

DETAILED_HELP = {
    'DESCRIPTION': DESCRIPTION,
    'EXAMPLES': EXAMPLES_GA,
}


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Reencrypt(base.Command):
  """Reencrypts a Cloud SQL CMEK instance."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        'instance',
        completer=flags.InstanceCompleter,
        help='Cloud SQL instance ID.',
    )

  def Run(self, args):
    """Reencrypts a Cloud SQL CMEK instance.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      A dict object representing the operations resource describing the
      reencrypt operation if the reencryption was successful.
    """
    client = api_util.SqlClient(api_util.API_VERSION_DEFAULT)
    sql_client = client.sql_client
    sql_messages = client.sql_messages
    operation_ref = None

    validate.ValidateInstanceName(args.instance)
    instance_ref = client.resource_parser.Parse(
        args.instance,
        params={'project': properties.VALUES.core.project.GetOrFail},
        collection='sql.instances',
    )

    if not console_io.PromptContinue(
        'WARNING: Reencryption will restart your instance if the primary key'
        " version is different from the instance's key version."
    ):
      return None
    try:
      result = sql_client.instances.Reencrypt(
          sql_messages.SqlInstancesReencryptRequest(
              instance=instance_ref.instance, project=instance_ref.project
          )
      )

      operation_ref = client.resource_parser.Create(
          'sql.operations', operation=result.name, project=instance_ref.project
      )

      if args.async_:
        return sql_client.operations.Get(
            sql_messages.SqlOperationsGetRequest(
                project=operation_ref.project, operation=operation_ref.operation
            )
        )

      operations.OperationsV1Beta4.WaitForOperation(
          sql_client, operation_ref, 'Reencrypting Cloud SQL instance'
      )

    except exceptions.HttpError:
      log.debug('operation : %s', six.text_type(operation_ref))
      raise

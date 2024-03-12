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
"""Cloud Pub/Sub schemas rollback command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_ex

from googlecloudsdk.api_lib.pubsub import schemas
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import resource_args
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import log


class Rollback(base.Command):
  """Roll back a Pub/Sub schema to a specified revision."""

  detailed_help = {
      'EXAMPLES': """\
          To roll back to an existing schema revision called "key-schema" with revision_id: "0a0b0c0d", run:
          \
          \n$ {command} key-schema --revision-id=0a0b0c0d
          """
  }

  @staticmethod
  def Args(parser):
    # The flag name is 'schema'.
    resource_args.AddSchemaResourceArg(parser, 'to rollback.')
    parser.add_argument(
        '--revision-id',
        type=str,
        help='The revision to roll back to.',
        required=True,
    )

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      A serialized object (dict) describing the results of the operation.
      This description fits the Resource described in the ResourceRegistry under
      'pubsub.projects.schemas'.

    Raises:
      util.RequestFailedError: if any of the requests to the API failed.
    """
    client = schemas.SchemasClient()
    schema_ref = util.ParseSchemaName(args.schema)
    revision_id = getattr(args, 'revision_id', None)
    try:
      result = client.Rollback(schema_ref=schema_ref, revision_id=revision_id)
    except api_ex.HttpError as error:
      exc = exceptions.HttpException(error)
      log.CreatedResource(
          schema_ref,
          kind='schema revision',
          failed=util.CreateFailureErrorMessage(exc.payload.status_message),
      )
      return

    log.CreatedResource(result.name, kind='schema revision')
    return result

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
"""Cloud Pub/Sub schemas commit command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_ex

from googlecloudsdk.api_lib.pubsub import schemas
from googlecloudsdk.api_lib.util import exceptions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.pubsub import flags
from googlecloudsdk.command_lib.pubsub import resource_args
from googlecloudsdk.command_lib.pubsub import util
from googlecloudsdk.core import log


class Commit(base.Command):
  """Commit a Pub/Sub schema revision."""

  detailed_help = {
      'EXAMPLES': """\
          To commit a PROTOCOL_BUFFER schema revision called "key-schema" that requires exactly one-string field named "key", run:
          \
          \n$ {command} key-schema --definition="syntax = 'proto3'; message Message { optional string key = 1; }" --type=protocol-buffer
          \
          To commit an equivalent AVRO schema revision, run:
          \
          \n$ {command} key-schema --definition="{ 'type': 'record', 'namespace': 'my.ns', 'name': 'KeyMsg', 'fields': [ { 'name': 'key', 'type': 'string' } ] }" --type=avro
                  """
  }

  @staticmethod
  def Args(parser):
    # The flag name is 'schema'.
    resource_args.AddSchemaResourceArg(parser, 'to revise.')
    flags.AddCommitSchemaFlags(parser)

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
    if args.definition_file:
      definition = args.definition_file
    else:
      definition = args.definition

    try:
      result = client.Commit(
          schema_ref=schema_ref,
          schema_definition=definition,
          schema_type=args.type,
      )
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

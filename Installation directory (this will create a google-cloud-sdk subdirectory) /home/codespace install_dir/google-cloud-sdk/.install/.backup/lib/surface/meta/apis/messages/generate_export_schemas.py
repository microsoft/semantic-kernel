# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""A command that generates YAML export schemas for a message in a given API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.meta.apis import flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.apis import export
from googlecloudsdk.command_lib.util.apis import registry


class GenerateExportSchemas(base.SilentCommand):
  """Generate YAML export schemas for a message in a given API.

  *gcloud* commands that have "too many" *create*/*update* command flags may
  also provide *export*/*import* commands. *export* lists the current state
  of a resource in a YAML *export* format. *import* reads export format data
  and either creates a new resource or updates an existing resource.

  An export format is an abstract YAML representation of the mutable fields of a
  populated protobuf message. Abstraction allows the export format to hide
  implementation details of some protobuf constructs like enums and
  `additionalProperties`.

  One way of describing an export format is with JSON schemas. A schema
  documents export format properties for a message in an API, and can also be
  used to validate data on import. Validation is important because users can
  modify export data before importing it again.

  This command generates [JSON schemas](json-schema.org) (in YAML format, go
  figure) for a protobuf message in an API. A separate schema files is
  generated for each nested message in the resource message.

  ## CAVEATS

  The generated schemas depend on the quality of the protobuf discovery
  docs, including proto file comment conventions that are not error checked.
  Always manually inspect schemas before using them in a release.

  ## EXAMPLES

  To generate the WorkflowTemplate schemas in the current directory from the
  dataproc v1 API:

    $ {command} WorkflowTemplate --api=dataproc --api-version=v1
  """

  @staticmethod
  def Args(parser):
    flags.API_REQUIRED_FLAG.AddToParser(parser)
    flags.API_VERSION_FLAG.AddToParser(parser)
    parser.add_argument(
        'message',
        help='The name of the message to generate the YAML export schemas for.')
    parser.add_argument(
        '--directory',
        help=('The path name of the directory to create the YAML export '
              'schema files in. If not specified then the files are created in '
              'the current directory.'))

  def Run(self, args):
    api = registry.GetAPI(args.api, api_version=args.api_version)
    try:
      message = getattr(api.GetMessagesModule(), args.message)
    except AttributeError:
      raise exceptions.InvalidArgumentException(
          'message', 'Message [{}] does not exist for API [{} {}]'.format(
              args.message, args.api, api.version))
    message_spec = arg_utils.GetRecursiveMessageSpec(message)
    export.GenerateExportSchemas(
        api, args.message, message_spec, args.directory)

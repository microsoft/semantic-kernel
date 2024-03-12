# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""The configs variables set command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.runtime_config import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.util import http_encoding


class Set(base.CreateCommand):
  """Create or update variable resources.

  This command creates or updates a variable resource, setting its value to
  the specified string or file contents.
  """

  detailed_help = {
      'EXAMPLES': """\
          To create or update a variable named "my-var", run:

            $ {command} --config-name=my-config my-var "my value"

          To create or update a variable with a hierarchical name, such as
          "results/task1", run:

            $ {command} --config-name=my-config results/task1 "my value"

          To create a variable, but fail if it already exists, run:

            $ {command} --config-name=my-config my-var "my-value" --fail-if-present

          To update a variable, but fail if it does not exist, run:

            $ {command} --config-name=my-config my-var "my-value" --fail-if-absent

          It is possible to provide --is-text flag if the value contains only
          text (UTF-8 encoded). This affects how the variable is transmitted on
          the wire and requires less quota on the backend.

            $ {command} --config-name=my-config --is-text my-var "my value"

          If the variable's value parameter is not specified, the value will be
          read from standard input. This allows setting variables to large values
          or values that contain non-printable characters. The variable value
          will be automatically base64-encoded. For example, to set a variable's
          value to the contents of a file, run:

            $ cat my-file | {command} --config-name my-config my-var
          """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.AddRequiredConfigFlag(parser)

    fail_group = parser.add_mutually_exclusive_group()
    fail_group.add_argument(
        '--fail-if-present',
        help='Fail if a variable with the specified name already exists.',
        action='store_true')
    fail_group.add_argument(
        '--fail-if-absent',
        help='Fail if a variable with the specified name does not exist.',
        action='store_true')

    parser.add_argument('name', help='The variable name.')
    parser.add_argument(
        'value',
        nargs='?',
        default=None,
        help=(
            'The variable value. If absent, the value will be read from stdin. '
            'The value is automatically base64-encoded, '
            'unless --is-text flag is set.'))

    parser.add_argument('--is-text',
                        default=False,
                        required=False,
                        action='store_true',
                        help=('If True, send and store the value as text. Can '
                              'be used if the value contains only text '
                              '(UTF-8 encoded). This affects how the variable '
                              'is transmitted on the wire and requires less '
                              'quota on the backend.'))

  def Run(self, args):
    """Run 'runtime-configs variables set'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The new variable.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    var_resource = util.ParseVariableName(args.name, args)
    if args.value is None:
      log.status.Print('No value argument specified; reading value from stdin.')
      value = sys.stdin.read()
    else:
      value = args.value

    if args.fail_if_absent:
      # Update case
      return self._Update(args, var_resource, value)
    else:
      # Either create or create-or-update
      try:
        return self._Create(args, var_resource, value)
      except apitools_exceptions.HttpConflictError:
        # If --fail-if-present was not specified, and we got an
        # Already Exists error, try updating instead.
        if not args.fail_if_present:
          return self._Update(args, var_resource, value)

        # If --fail-if-present was specified re-raise the error.
        raise

  def _Create(self, args, var_resource, value):
    variable_client = util.VariableClient()
    messages = util.Messages()

    project = var_resource.projectsId
    config = var_resource.configsId

    result = variable_client.Create(
        messages.RuntimeconfigProjectsConfigsVariablesCreateRequest(
            parent=util.ConfigPath(project, config),
            variable=messages.Variable(
                name=var_resource.RelativeName(),
                value=http_encoding.Encode(value) if not args.is_text else None,
                text=value if args.is_text else None,
            )
        )
    )

    log.CreatedResource(var_resource)
    return util.FormatVariable(result)

  def _Update(self, args, var_resource, value):
    variable_client = util.VariableClient()
    messages = util.Messages()

    result = variable_client.Update(
        messages.Variable(
            name=var_resource.RelativeName(),
            value=http_encoding.Encode(value) if not args.is_text else None,
            text=value if args.is_text else None,
        )
    )

    log.UpdatedResource(var_resource)
    return util.FormatVariable(result)

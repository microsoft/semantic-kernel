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

"""Shared base classes for runtimeconfig commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.runtime_config import flags


class VariableRetrieverCommand(base.DescribeCommand):
  """A base command that retrieves a single variable object.
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    flags.AddRequiredConfigFlag(parser)
    parser.add_argument('name', help='The variable name.')

  def Run(self, args):
    """Run a command that retrieves a variable.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The requested variable.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    variable_client = util.VariableClient()
    messages = util.Messages()

    var_resource = util.ParseVariableName(args.name, args)

    return variable_client.Get(
        messages.RuntimeconfigProjectsConfigsVariablesGetRequest(
            name=var_resource.RelativeName(),
        )
    )

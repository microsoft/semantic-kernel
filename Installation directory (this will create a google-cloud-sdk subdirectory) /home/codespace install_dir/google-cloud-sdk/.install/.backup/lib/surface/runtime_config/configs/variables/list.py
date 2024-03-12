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

"""The configs variables list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.runtime_config import flags
from googlecloudsdk.core import log


class List(base.ListCommand):
  """List variable resources within a configuration.

  This command lists the variable resources within a specified configuration.
  """

  DEFAULT_PAGE_SIZE = 100

  detailed_help = {
      'EXAMPLES': """\
          To list all variables within the configuration named "my-config", run:

            $ {command} --config-name=my-config

          The --filter parameter can be used to filter results based on content.
          For example, to list all variables under the path 'status/', run:

            $ {command} --config-name=my-config --filter='name=status/*'
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

    parser.add_argument(
        '--values',
        action='store_true',
        help=('List the variables for which you have Get '
              'IAM permission along with their values.'))
    parser.display_info.AddFormat('table(name, updateTime, value:optional)')

  def Run(self, args):
    """Run 'runtime-configs variables list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Yields:
      The list of variables.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    variable_client = util.VariableClient()
    messages = util.Messages()

    config_resource = util.ParseConfigName(util.ConfigName(args))

    self._display_values = args.values

    request = messages.RuntimeconfigProjectsConfigsVariablesListRequest(
        parent=config_resource.RelativeName(),
        returnValues=self._display_values)

    page_size = args.page_size or self.DEFAULT_PAGE_SIZE

    results = list_pager.YieldFromList(
        variable_client, request, field='variables',
        batch_size_attribute='pageSize', limit=args.limit,
        batch_size=page_size
    )

    for result in results:
      yield util.FormatVariable(result, self._display_values)

  def Epilog(self, resources_were_displayed):
    if resources_were_displayed and self._display_values:
      log.status.Print("""\
With --values flag specified, only those variables for which you have Get IAM permission will be returned along with their values.
To see all the variables for which you have List IAM permission, please run the command without the --values flag.
""")

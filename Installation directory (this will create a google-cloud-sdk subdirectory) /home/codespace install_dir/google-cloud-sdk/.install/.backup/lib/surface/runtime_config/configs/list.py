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

"""The configs list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List runtime-config resources within the current project.

  This command lists runtime-config resources for the current project.
  """

  DEFAULT_PAGE_SIZE = 100

  detailed_help = {
      'EXAMPLES': """
          To list all runtime-config resources for the current project, run:

            $ {command}

          The --filter parameter can be used to filter results based on content.
          For example, to list all runtime-config resources with names that
          begin with 'foo', run:

            $ {command} --filter='name=foo*'
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('table(name, description)')

  def Run(self, args):
    """Run 'runtime-configs list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Yields:
      The list of runtime-config resources.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    config_client = util.ConfigClient()
    messages = util.Messages()
    project = util.Project()

    request = messages.RuntimeconfigProjectsConfigsListRequest(
        parent=util.ProjectPath(project),
    )

    page_size = args.page_size or self.DEFAULT_PAGE_SIZE

    results = list_pager.YieldFromList(
        config_client, request, field='configs',
        batch_size_attribute='pageSize', limit=args.limit,
        batch_size=page_size,
    )

    for result in results:
      yield util.FormatConfig(result)

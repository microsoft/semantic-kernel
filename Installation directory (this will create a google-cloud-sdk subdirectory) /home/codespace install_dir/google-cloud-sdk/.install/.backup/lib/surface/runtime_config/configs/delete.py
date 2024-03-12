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

"""The configs delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.runtime_config import util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class Delete(base.DeleteCommand):
  """Delete runtime-config resources.

  This command deletes the runtime-config resource with the specified name and
  all of its variable and waiter children.
  """

  detailed_help = {
      'EXAMPLES': """\
          To delete a runtime-config resource named "my-config", run:

            $ {command} my-config
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
    parser.add_argument('name', help='The runtime-config resource name.')

  def Run(self, args):
    """Run 'runtime-configs delete'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    config_client = util.ConfigClient()
    messages = util.Messages()

    config_resource = util.ParseConfigName(args.name)

    config_client.Delete(
        messages.RuntimeconfigProjectsConfigsDeleteRequest(
            name=config_resource.RelativeName(),
        )
    )

    log.DeletedResource(config_resource)

# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import common_args
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


class Create(base.CreateCommand):
  """Create a service identity for a consumer.

  This command creates a service identity for a consumer. The supported
  consumers are projects, folders, and organizations.

  ## EXAMPLES

  To create a service identity for a project, folder, or organization, run:

    $ {command} --service=example.googleapis.com --project=helloworld
    $ {command} --service=example.googleapis.com --project=1234567890
    $ {command} --service=example.googleapis.com --folder=1234567890
    $ {command} --service=example.googleapis.com --organization=1234567890
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument(
        '--service',
        required=True,
        help='The service to create a service identity for.')
    container = parser.add_group(
        mutex=True,
        help=(
            'Container resource where the service identity will be used.'
        ),
    )
    common_args.ProjectArgument(
        help_text_to_prepend='Project where the service identity will be used.'
    ).AddToParser(container)
    base.Argument(
        '--folder',
        default=None,
        type=int,
        help='Folder where the service identity will be used.',
    ).AddToParser(container)
    base.Argument(
        '--organization',
        default=None,
        type=int,
        help='Organization where the service identity will be used.',
    ).AddToParser(container)

  def Run(self, args):
    """Run 'services identity create'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      response with service identity email and uniqueId.
    """
    if args.folder:
      container = args.folder
      container_type = serviceusage.ContainerType.FOLDER_SERVICE_RESOURCE
    elif args.organization:
      container = args.organization
      container_type = serviceusage.ContainerType.ORG_SERVICE_RESOURCE
    else:
      if args.project:
        container = args.project
      else:
        container = properties.VALUES.core.project.Get(required=True)
      container_type = serviceusage.ContainerType.PROJECT_SERVICE_RESOURCE
    response = serviceusage.GenerateServiceIdentity(
        container, args.service, container_type
    )
    if 'email' not in response:
      # Print generic message when email not provided in response.
      # Error in GenerateServiceIdentity indicated by thrown exception.
      log.status.Print('Service identity created')
    else:
      log.status.Print('Service identity created: {0}'.format(
          response['email']))
    return response

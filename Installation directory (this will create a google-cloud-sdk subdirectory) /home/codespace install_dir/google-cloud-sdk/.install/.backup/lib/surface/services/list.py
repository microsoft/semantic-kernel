# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""services list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags


# TODO(b/321801975) make command public after preview.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListAlpha(base.ListCommand):
  """List services for a project, folder or organization.

  This command lists the services that are enabled or available (Google first
  party services) to be enabled
  by a project, folder or organization. Service enablement can be inherited from
  resource ancestors. A resource's enabled services include services that are
  enabled on the resource itself and enabled on all resource ancestors.
  services by using exactly one of the `--enabled` or `--available` flags.
  `--enabled` is the default.

  ## EXAMPLES

  To list the services the current project has enabled for consumption, run:

    $ {command} --enabled

  To list the Google first party services the current project can enable for
  consumption, run:

    $ {command} --available
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    mode_group = parser.add_mutually_exclusive_group(required=False)

    mode_group.add_argument(
        '--enabled',
        action='store_true',
        help=(
            '(DEFAULT) Return the services which the project, folder or'
            ' organization has enabled.'
        ),
    )

    mode_group.add_argument(
        '--available',
        action='store_true',
        help=(
            'Return the Google first party services available to the '
            'project, folder or organization to enable. This list will '
            'include any services that the project, folder or organization '
            'has already enabled.'
        ),
    )

    common_flags.add_resource_args(parser)

    base.PAGE_SIZE_FLAG.SetDefault(parser, 200)

    # Remove unneeded list-related flags from parser
    base.URI_FLAG.RemoveFromParser(parser)

    parser.display_info.AddFormat("""
        table(
            name:label=NAME:sort=1,
            title
        )
      """)

  def Run(self, args):
    """Run 'services list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The list of services for this project.
    """
    # Default mode is --enabled, so if no flags were specified,
    # turn on the args.enabled flag.
    if not (args.enabled or args.available):
      args.enabled = True
    if args.IsSpecified('project'):
      project = args.project
    else:
      project = services_util.GetValidatedProject(args.project)
    if args.IsSpecified('folder'):
      folder = args.folder
    else:
      folder = None
    if args.IsSpecified('organization'):
      organization = args.organization
    else:
      organization = None
    if args.IsSpecified('limit'):
      return serviceusage.ListServicesV2Alpha(
          project,
          args.enabled,
          args.page_size,
          args.limit,
          folder=folder,
          organization=organization,
      )
    else:
      return serviceusage.ListServicesV2Alpha(
          project,
          args.enabled,
          args.page_size,
          folder=folder,
          organization=organization,
      )


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class List(base.ListCommand):

  """List services for a project.

  This command lists the services that are enabled or available to be enabled
  by a project. You can choose the mode in which the command will list
  services by using exactly one of the `--enabled` or `--available` flags.
  `--enabled` is the default.

  ## EXAMPLES

  To list the services for  the current project has enabled for consumption,
  run:

    $ {command} --enabled

  To list the services for the current project can enable for consumption, run:

    $ {command} --available

  To list the services for project `my-project` has enabled for consumption,
  run:

    $ {command} --enabled --project=my-project

  To list the services the project `my-project` can enable for consumption, run:

    $ {command} --available --project=my-project
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    mode_group = parser.add_mutually_exclusive_group(required=False)

    mode_group.add_argument(
        '--enabled',
        action='store_true',
        help=('(DEFAULT) Return the services which the '
              'project has enabled.'))

    mode_group.add_argument(
        '--available',
        action='store_true',
        help=('Return the services available to the '
              'project to enable. This list will '
              'include any services that the project '
              'has already enabled.'))

    base.PAGE_SIZE_FLAG.SetDefault(parser, 200)

    # Remove unneeded list-related flags from parser
    base.URI_FLAG.RemoveFromParser(parser)

    parser.display_info.AddFormat("""
          table(
            config.name:label=NAME:sort=1,
            config.title
          )
        """)

  def Run(self, args):
    """Run 'services list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The list of services for this project.
    """
    # Default mode is --enabled, so if no flags were specified,
    # turn on the args.enabled flag.
    if not (args.enabled or args.available):
      args.enabled = True
    project = services_util.GetValidatedProject(args.project)
    return serviceusage.ListServices(
        project, args.enabled, args.page_size, args.limit
    )

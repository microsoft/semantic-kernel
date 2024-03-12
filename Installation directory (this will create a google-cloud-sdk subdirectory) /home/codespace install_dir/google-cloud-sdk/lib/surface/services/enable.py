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

"""services enable command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_OP_BASE_CMD = 'gcloud beta services operations '
_OP_WAIT_CMD = _OP_BASE_CMD + 'wait {0}'

_DETAILED_HELP_ALPHA = {
    'DESCRIPTION': """\
        This command enables a service for consumption for a project, folder or organization.

        To see a list of available services for a project, run:

          $ {parent_command} list --available

     More information on listing services can be found at:
     https://cloud.google.com/service-usage/docs/list-services and on
     disabling a service at:
     https://cloud.google.com/service-usage/docs/enable-disable
        """,
    'EXAMPLES': """\
        To enable a service called `my-consumed-service` on the current
        project, run:

          $ {command} my-consumed-service

        To enable a service called `my-consumed-service` on the project
        `my-project`, run:

          $ {command} my-consumed-service --project=my-project

        To enable a service called `my-consumed-service` on the folder
        `my-folder, run:

          $ {command} my-consumed-service --folder=my-folder

        To enable a service called `my-consumed-service` on the organization
        `my-organization`, run:

          $ {command} my-consumed-service --organization=my-organization

        To run the same command asynchronously (non-blocking), run:

          $ {command} my-consumed-service --async

        To enable services called `service1`, `service2`, and `service3` on the
        current project, run:

          $ {command} service1 service2 service3
        """,
}

_DETAILED_HELP = {
    'DESCRIPTION': """\
        This command enables a service for consumption for a project.

        To see a list of available services for a project, run:

          $ {parent_command} list --available

     More information on listing services can be found at:
     https://cloud.google.com/service-usage/docs/list-services and on
     disabling a service at:
     https://cloud.google.com/service-usage/docs/enable-disable
        """,
    'EXAMPLES': """\
        To enable a service called `my-consumed-service` on the current
        project, run:

          $ {command} my-consumed-service

        To run the same command asynchronously (non-blocking), run:

          $ {command} my-consumed-service --async

        To enable services called `service1`, `service2`, and `service3` on the
        current project, run:

          $ {command} service1 service2 service3
        """,
}


# TODO(b/321801975) make command public after preview.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class EnableAlpha(base.SilentCommand):
  """Enables a service for consumption for a project, folder or organization."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    common_flags.available_service_flag(suffix='to enable').AddToParser(parser)
    common_flags.add_resource_args(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    common_flags.validate_only_args(parser)

  def Run(self, args):
    """Run 'services enable'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Nothing.
    """
    if args.IsSpecified('project'):
      project = args.project
    else:
      project = properties.VALUES.core.project.Get(required=True)
    if args.IsSpecified('folder'):
      folder = args.folder
    else:
      folder = None
    if args.IsSpecified('organization'):
      organization = args.organization
    else:
      organization = None

    op = serviceusage.AddEnableRule(
        args.service,
        project,
        folder=folder,
        organization=organization,
        validate_only=args.validate_only,
    )
    if not args.validate_only:
      if args.async_:
        cmd = _OP_WAIT_CMD.format(op.name)
        log.status.Print(
            'Asynchronous operation is in progress... '
            'Use the following command to wait for its '
            'completion:\n {0}'.format(cmd)
        )
    log.status.Print('Operation finished successfully')

EnableAlpha.detailed_help = _DETAILED_HELP_ALPHA


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Enable(base.SilentCommand):
  """Enables a service for consumption for a project."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    common_flags.available_service_flag(suffix='to enable').AddToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run 'services enable'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      Nothing.
    """
    project = properties.VALUES.core.project.Get(required=True)
    if len(args.service) == 1:
      op = serviceusage.EnableApiCall(project, args.service[0])
    else:
      op = serviceusage.BatchEnableApiCall(project, args.service)
    if op.done:
      return
    if args.async_:
      cmd = _OP_WAIT_CMD.format(op.name)
      log.status.Print('Asynchronous operation is in progress... '
                       'Use the following command to wait for its '
                       'completion:\n {0}'.format(cmd))
      return
    op = services_util.WaitOperation(op.name, serviceusage.GetOperation)
    services_util.PrintOperation(op)


Enable.detailed_help = _DETAILED_HELP

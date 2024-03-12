# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""services policies remove-enable-rule command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.services import arg_parsers
from googlecloudsdk.command_lib.services import common_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

_PROJECT_RESOURCE = 'projects/{}'
_FOLDER_RESOURCE = 'folders/{}'
_ORGANIZATION_RESOURCE = 'organizations/{}'
_CONSUMER_POLICY_DEFAULT = '/consumerPolicies/{}'

OP_BASE_CMD = 'gcloud beta services operations '
OP_WAIT_CMD = OP_BASE_CMD + 'wait {0}'


# TODO(b/321801975) make command public after preview.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RemovedEnableRules(base.SilentCommand):
  """Remove service(s) from a consumer policy for a project, folder or organization.

  Remove service(s) from a consumer policy for a project, folder or
  organization.

  ## EXAMPLES
  To remove service called `my-consumed-service` from the default consumer
  policy on the current project, run:

    $ {command} my-consumed-service
        OR
    $ {command} my-consumed-service --policy-name=default

   To remove service called `my-consumed-service` from from the default consumer
   policy on project `my-project`, run:

    $ {command} my-consumed-service --project=my-project
        OR
    $ {command} my-consumed-service --policy-name=default

  To run the same command asynchronously (non-blocking), run:

    $ {command} my-consumed-service --async
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    common_flags.consumer_service_flag(
        suffix='to remove enable rule for'
    ).AddToParser(parser)
    parser.add_argument(
        '--policy-name',
        help=(
            'Name of the consumer policy. Currently only "default" is'
            ' supported.'
        ),
        default='default',
    )
    common_flags.add_resource_args(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        '--force',
        action='store_true',
        help=(
            'If specified, the remove-enable-rules call will proceed even if'
            ' there are enabled services which depend on the service to be'
            ' removed from enable rule. Forcing the call means that the'
            ' services which depend on the service to be removed from enable'
            ' rule will also be removed  .'
        ),
    )
    common_flags.validate_only_args(parser)

    parser.display_info.AddFormat("""
        table(
            services:label=''
        )
      """)

  def Run(self, args):
    """Run services policies remove-enable-rules.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The services in the consumer policy.
    """

    if args.IsSpecified('project'):
      project = args.project
    else:
      project = properties.VALUES.core.project.Get(required=True)
    resource_name = _PROJECT_RESOURCE.format(project)
    if args.IsSpecified('folder'):
      folder = args.folder
      resource_name = _FOLDER_RESOURCE.format(args.folder)
    else:
      folder = None
    if args.IsSpecified('organization'):
      organization = args.organization
      resource_name = _ORGANIZATION_RESOURCE.format(args.organization)
    else:
      organization = None
    for service_name in args.service:
      service_name = arg_parsers.GetServiceNameFromArg(service_name)

      protected_msg = serviceusage.GetProtectedServiceWarning(service_name)
      if protected_msg:
        if args.IsSpecified('quiet'):
          raise console_io.RequiredPromptError()
        do_disable = console_io.PromptContinue(
            protected_msg, default=False, throw_if_unattended=True
        )
        if not do_disable:
          continue

      op = serviceusage.RemoveEnableRule(
          project,
          service_name,
          args.policy_name,
          args.force,
          folder,
          organization,
          args.validate_only,
      )

      if args.validate_only:
        return

      if op.done:
        continue
      if args.async_:
        cmd = OP_WAIT_CMD.format(op.name)
        log.status.Print(
            'Asynchronous operation is in progress... '
            'Use the following command to wait for its '
            'completion:\n {0}'.format(cmd)
        )
        continue

    update_policy = serviceusage.GetConsumerPolicyV2Alpha(
        resource_name + _CONSUMER_POLICY_DEFAULT.format(args.policy_name)
    )

    log.status.Print(
        'Consumer policy ('
        + resource_name
        + _CONSUMER_POLICY_DEFAULT.format(args.policy_name)
        + ') has been updated to:',
    )

    if update_policy.enableRules:
      resources = collections.namedtuple('Values', ['services'])
      result = []
      for value in update_policy.enableRules[0].services:
        result.append(resources(value))
      return result

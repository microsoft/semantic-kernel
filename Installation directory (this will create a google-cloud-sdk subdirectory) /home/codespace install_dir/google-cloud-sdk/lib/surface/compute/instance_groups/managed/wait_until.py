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
"""Command for waiting until managed instance group reaches desired state."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.instance_groups.managed import wait_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


def _AddArgs(parser, beta=False):
  """Adds args."""
  parser.add_argument(
      '--timeout',
      type=int,
      help='Waiting time in seconds for the group '
      'to reach the desired state.')

  event_type = parser.add_mutually_exclusive_group(required=True)
  event_type.add_argument('--version-target-reached',
                          action='store_true',
                          default=False,
                          help='Wait until version target is reached.')
  if beta:
    event_type.add_argument(
        '--all-instances-config-effective',
        action='store_true',
        default=False,
        help="Wait until the group's all-instances configuration is applied "
             "to all VMs in the group.")

  event_type.add_argument('--stable',
                          action='store_true',
                          default=False,
                          help='Wait until the group is stable.')
  instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
      parser)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class WaitUntilGA(base.Command):
  """Wait until the managed instance group reaches the desired state."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser)

  def CreateGroupReference(self, client, resources, args):
    return (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
            .ResolveAsResource)(
                args,
                resources,
                default_scope=compute_scope.ScopeEnum.ZONE,
                scope_lister=flags.GetDefaultScopeLister(client))

  def Run(self, args):
    """Issues requests necessary to wait until stable on a MIG."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    group_ref = self.CreateGroupReference(client, holder.resources, args)

    if args.stable:
      igm_state = wait_utils.IgmState.STABLE
    elif args.version_target_reached:
      igm_state = wait_utils.IgmState.VERSION_TARGET_REACHED
    elif args.all_instances_config_effective:
      igm_state = wait_utils.IgmState.ALL_INSTANCES_CONFIG_EFFECTIVE

    wait_utils.WaitForIgmState(client, group_ref, igm_state, args.timeout)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class WaitUntilBeta(WaitUntilGA):
  """Wait until the managed instance group reaches the desired state."""

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser, beta=True)

WaitUntilGA.detailed_help = {
    'brief':
        'Wait until the managed instance group reaches the desired state.',
    'EXAMPLES':
        """\
        To wait until the managed instance group ``instance-group-1'' is stable,
        run:

          $ {command} --stable instance-group-1
        """,
}

WaitUntilBeta.detailed_help = WaitUntilGA.detailed_help

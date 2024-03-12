# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Command for waiting until managed instance group becomes stable."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.instance_groups.managed import wait_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


def _AddArgs(parser):
  """Adds args."""
  parser.add_argument('--timeout',
                      type=int,
                      help='Timeout in seconds for waiting '
                      'for group becoming stable.')
  instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
      parser)

_DEPRECATION_WARNING = (
    '`gcloud compute instance-groups managed wait-until-stable` is deprecated. '
    'Please use `gcloud compute instance-groups managed wait-until --stable` '
    'instead.')


@base.Deprecate(is_removed=False, warning=_DEPRECATION_WARNING)
@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class WaitUntilStable(base.Command):
  """Waits until state of managed instance group is stable."""

  _TIME_BETWEEN_POLLS_SEC = 10

  @staticmethod
  def Args(parser):
    _AddArgs(parser=parser)

  def CreateGroupReference(self, client, resources, args):
    return (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.
            ResolveAsResource)(
                args,
                resources,
                default_scope=compute_scope.ScopeEnum.ZONE,
                scope_lister=flags.GetDefaultScopeLister(client))

  def Run(self, args):
    """Issues requests necessary to wait until stable on a MIG."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    group_ref = self.CreateGroupReference(client, holder.resources, args)

    wait_utils.WaitForIgmState(
        client, group_ref, wait_utils.IgmState.STABLE, args.timeout)

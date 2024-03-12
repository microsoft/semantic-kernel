# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for setting a backup target pool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.target_pools import flags


class SetBackup(base.SilentCommand):
  # pylint: disable=line-too-long
  """Set a backup pool for a target pool.

  *{command}* is used to set a backup target pool for a primary
  target pool, which defines the fallback behavior of the primary
  pool. If the ratio of the healthy instances in the primary pool
  is at or below the specified ``--failover-ratio value'', then traffic
  arriving at the load-balanced IP address will be directed to the
  backup pool.

  ## EXAMPLES
  To cause `TARGET-POOL` (in region `us-central1`) to fail over
  to `BACKUP-POOL` when more than half of the `TARGET-POOL`
  instances are unhealthy, run:

    $ {command} TARGET-POOL --backup-pool=BACKUP-POOL --failover-ratio=0.5 --region=us-central1

  To remove `BACKUP-POOL` as a backup to `TARGET-POOL`, run:

    $ {command} TARGET-POOL --backup-pool='' --region=us-central1
  """
  # pylint: enable=line-too-long

  BACKUP_POOL_ARG = None
  TARGET_POOL_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.BACKUP_POOL_ARG = flags.BackupPoolArgument()
    cls.TARGET_POOL_ARG = flags.TargetPoolArgument(
        help_suffix=' for which to set the backup pool.')
    cls.TARGET_POOL_ARG.AddArgument(
        parser, operation_type='set a backup pool for')

    backup_pool_group = parser.add_mutually_exclusive_group(required=True)
    backup_pool_group.add_argument(
        '--no-backup-pool', action='store_true',
        help='Unsets the backup pool. This disables failover.')
    backup_pool_group.add_argument(
        '--backup-pool',
        completer=flags.TargetPoolsCompleter,
        help='Name of the target pool that will serve as backup.')

    parser.add_argument(
        '--failover-ratio',
        type=float,
        help=('The new failover ratio value for the target pool. '
              'This must be a float in the range of [0, 1].'))

  def Run(self, args):
    """Issues a request necessary for setting a backup target pool."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    target_pool_ref = self.TARGET_POOL_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    if args.backup_pool:
      args.backup_pool_region = target_pool_ref.region
      backup_pool_ref = self.BACKUP_POOL_ARG.ResolveAsResource(args,
                                                               holder.resources)
      target_reference = client.messages.TargetReference(
          target=backup_pool_ref.SelfLink())
    else:
      target_reference = client.messages.TargetReference()

    if args.backup_pool and args.failover_ratio is None:
      raise compute_exceptions.ArgumentError(
          '[--failover-ratio] must be provided when setting a backup pool.')

    if args.failover_ratio is not None and (
        args.failover_ratio < 0 or args.failover_ratio > 1):
      raise compute_exceptions.ArgumentError(
          '[--failover-ratio] must be a number between 0 and 1, inclusive.')

    request = client.messages.ComputeTargetPoolsSetBackupRequest(
        targetPool=target_pool_ref.Name(),
        targetReference=target_reference,
        failoverRatio=args.failover_ratio,
        region=target_pool_ref.region,
        project=target_pool_ref.project)

    return client.MakeRequests([(client.apitools_client.targetPools,
                                 'SetBackup', request)])

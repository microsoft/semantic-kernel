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
"""Updates a Cloud NetApp Volumes Backup Policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.backup_policies import client as backuppolicies_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.backup_policies import flags as backuppolicies_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(base.UpdateCommand):
  """Update a Cloud NetApp Volumes Backup Policies."""

  detailed_help = {
      'DESCRIPTION': """\
          Updates a Backup Policy
          """,
      'EXAMPLES': """\
          The following command updates a Backup Policy named BACKUP_POLICY with all possible arguments

              $ {command} BACKUP_POLICY --location=us-central1 --enabled=True --daily-backup-limit=5 --weekly-backup-limit=3 --monthly-backup-limit=2

          To update a Backup Policy named BACKUP_POLICY asynchronously, run the following command:

              $ {command} BACKUP_POLICY --async --location=us-central1 --enabled=True --daily-backup-limit=5 --weekly-backup-limit=3 --monthly-backup-limit=2
              """,
  }

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  @staticmethod
  def Args(parser):
    backuppolicies_flags.AddBackupPolicyUpdateArgs(parser)

  def Run(self, args):
    """Update a Cloud NetApp Volumes Backup Policy in the current project."""
    backuppolicy_ref = args.CONCEPTS.backup_policy.Parse()
    client = backuppolicies_client.BackupPoliciesClient(self._RELEASE_TRACK)
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    orig_backuppolicy = client.GetBackupPolicy(backuppolicy_ref)
    ## Update labels
    if labels_diff.MayHaveUpdates():
      labels = labels_diff.Apply(
          client.messages.BackupPolicy.LabelsValue, orig_backuppolicy.labels
      ).GetOrNone()
    else:
      labels = None
    backup_policy = client.ParseUpdatedBackupPolicy(
        orig_backuppolicy,
        enabled=args.enabled,
        daily_backup_limit=args.daily_backup_limit,
        weekly_backup_limit=args.weekly_backup_limit,
        monthly_backup_limit=args.monthly_backup_limit,
        description=args.description,
        labels=labels,
    )

    updated_fields = []
    if args.IsSpecified('enabled'):
      updated_fields.append('enabled')
    if args.IsSpecified('daily_backup_limit'):
      updated_fields.append('dailyBackupLimit')
    if args.IsSpecified('weekly_backup_limit'):
      updated_fields.append('weeklyBackupLimit')
    if args.IsSpecified('monthly_backup_limit'):
      updated_fields.append('monthlyBackupLimit')
    if args.IsSpecified('description'):
      updated_fields.append('description')
    if (
        args.IsSpecified('update_labels')
        or args.IsSpecified('remove_labels')
        or args.IsSpecified('clear_labels')
    ):
      updated_fields.append('labels')
    update_mask = ','.join(updated_fields)

    result = client.UpdateBackupPolicy(
        backuppolicy_ref, backup_policy, update_mask, args.async_
    )
    if args.async_:
      command = 'gcloud {} netapp backup-policies list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the updated backup policy by listing all kms'
          ' configs:\n  $ {} '.format(command)
      )
    return result

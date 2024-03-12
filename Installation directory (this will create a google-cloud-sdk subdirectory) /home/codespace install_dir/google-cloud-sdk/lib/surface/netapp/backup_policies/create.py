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
"""Creates a Cloud NetApp Backup Policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.backup_policies import client as backuppolicies_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.netapp.backup_policies import flags as backuppolicies_flags
from googlecloudsdk.command_lib.util.args import labels_util

from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateBeta(base.CreateCommand):
  """Create a Cloud NetApp Backup Policy."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  detailed_help = {
      'DESCRIPTION': """\
          Creates a Backup Policy for Cloud NetApp Volumes.
          """,
      'EXAMPLES': """\
          The following command creates a Backup Policy named BACKUP_POLICY with all possible arguments:

              $ {command} BACKUP_POLICY --location=us-central1 --enabled=true --daily-backup-limit=3 --weekly-backup-limit=5 --monthly-backup-limit=2 --description="first backup policy" --labels=key1=val1
          """,
  }

  @staticmethod
  def Args(parser):
    backuppolicies_flags.AddBackupPolicyCreateArgs(parser)

  def Run(self, args):
    """Create a Cloud NetApp Backup Policy in the current project."""
    backuppolicy_ref = args.CONCEPTS.backup_policy.Parse()
    client = backuppolicies_client.BackupPoliciesClient(self._RELEASE_TRACK)
    labels = labels_util.ParseCreateArgs(
        args, client.messages.BackupPolicy.LabelsValue)

    backup_policy = client.ParseBackupPolicy(
        name=backuppolicy_ref.RelativeName(),
        enabled=args.enabled,
        daily_backup_limit=args.daily_backup_limit,
        weekly_backup_limit=args.weekly_backup_limit,
        monthly_backup_limit=args.monthly_backup_limit,
        description=args.description,
        labels=labels,
    )
    result = client.CreateBackupPolicy(
        backuppolicy_ref, args.async_, backup_policy
    )
    if args.async_:
      command = 'gcloud {} netapp backup-policies list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the new backup policy by listing all backup'
          ' policies:\n  $ {} '.format(command)
      )
    return result

# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Create command for Backup for GKE backup."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.backup_restore import util as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.backup_restore import resource_args
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Creates a backup.

  Creates a Backup for GKE backup.

  ## EXAMPLES

  To create a backup ``my-backup'' in project ``my-project'' in location
  ``us-central1'' under backup plan ``my-backup-plan'', run:

    $ {command} my-backup --project=my-project --location=us-central1
    --backup-plan=my-backup-plan

  To create a backup ``my-backup'' in project ``my-project'' in location
  ``us-central1'' under backup plan ``my-backup-plan'' and not wait for the
  resulting operation to finish, run:

    $ {command} my-backup --project=my-project --location=us-central1
    --backup-plan=my-backup-plan --async

  To create a backup ``my-backup'' in project ``my-project'' in location
  ``us-central1'' under backup plan ``my-backup-plan'' and wait for the Backup
   to complete, run:

    $ {command} my-backup --project=my-project --location=us-central1
    --backup-plan=my-backup-plan --wait-for-completion
  """

  @staticmethod
  def Args(parser):
    resource_args.AddBackupArg(parser)
    group = parser.add_group(mutex=True)
    group.add_argument(
        '--async',
        required=False,
        action='store_true',
        default=False,
        help='Return immediately, without waiting for the operation in progress to complete.'
    )
    group.add_argument(
        '--wait-for-completion',
        required=False,
        action='store_true',
        default=False,
        help='Wait for the created backup to complete.')
    parser.add_argument(
        '--description',
        type=str,
        required=False,
        default=None,
        help='Optional text description for the backup being created.')
    parser.add_argument(
        '--retain-days',
        type=int,
        required=False,
        default=None,
        help="""
        Retain days specifies the desired number of days from the createTime of
        this backup after which it will be automatically deleted.
        If not specified or set to 0, it means the backup will NOT be automatically
        deleted.
        Manual creation of a backup with this field unspecified causes the service
        to use the value of backupPlan.retentionPolicy.backupRetainDays.
        Creation of a Backup with this field set to a value SMALLER than
        delete_lock_days results in an invalid response from the service.
        This field may ONLY be increased in an Update request, or an invalid
        response will be returned by the service immediately.
        Default to 0 if not provided.
        """)
    parser.add_argument(
        '--delete-lock-days',
        type=int,
        required=False,
        default=None,
        help="""
        Delete lock days specifies the number of days from the createTime of this
        Backup before which deletion will be blocked. Must be >= the value in
        the backup plan. If not specified, inherited from the backup plan.
        Manual creation of a backup with this field unspecified causes the
        service to use the value of backupPlan.RetentionPolicy.backupDeleteBlockDays.
        Creation of a backup with this field set to a value SMALLER than
        backupPlan.RetentionPolicy.backupDeleteBlockDays results in an invalid
        response from the service.
        This field MUST be an int value between 0-90(inclusive).
        This field may only be INCREASED in an update command, or an invalid
        response will be returned by the service.
        """)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    labels = labels_util.GetUpdateLabelsDictFromArgs(args)
    backup_ref = args.CONCEPTS.backup.Parse()
    if args.IsSpecified('async'):
      return api_util.CreateBackup(
          backup_ref,
          description=args.description,
          labels=labels,
          retain_days=args.retain_days,
          delete_lock_days=args.delete_lock_days)
    api_util.CreateBackupAndWaitForLRO(
        backup_ref,
        description=args.description,
        labels=labels,
        retain_days=args.retain_days,
        delete_lock_days=args.delete_lock_days)
    if not args.IsSpecified('wait_for_completion'):
      return []
    return api_util.WaitForBackupToFinish(backup_ref.RelativeName())

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
"""Command to delete a backup schedule for a Firestore Database."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import backup_schedules
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firestore import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.Command):
  """Deletes a Cloud Firestore backup schedule.

  ## EXAMPLES

  To delete backup schedule 'cf9f748a-7980-4703-b1a1-d1ffff591db0' under
  database testdb.

      $ {command} --database='testdb'
      --backup-schedule='cf9f748a-7980-4703-b1a1-d1ffff591db0'
  """

  @staticmethod
  def Args(parser):
    """Set args for gcloud firestore backups schedules delete."""
    flags.AddDatabaseIdFlag(parser, required=True)
    flags.AddBackupScheduleFlag(parser)

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    return backup_schedules.DeleteBackupSchedule(
        project, args.database, args.backup_schedule
    )

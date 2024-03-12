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
"""Command to list backup schedules for a Firestore Database."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import backup_schedules
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firestore import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """Lists backup schedules under a Cloud Firesore database.

  ## EXAMPLES

  To list all backup schedules under database testdb.

      $ {command} --database='testdb'
  """

  @staticmethod
  def Args(parser):
    flags.AddDatabaseIdFlag(parser, required=True)

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    return backup_schedules.ListBackupSchedules(project, args.database)

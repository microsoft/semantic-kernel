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
"""Useful commands for interacting with the Cloud Firestore Backup Schedules API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import api_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions as ex


def _GetBackupSchedulesService():
  """Returns the service to interact with the Firestore Backup Schedules."""
  return api_utils.GetClient().projects_databases_backupSchedules


def GetBackupSchedule(project, database, backup_schedule):
  """Gets a backup schedule.

  Args:
    project: the project of the database of the backup schedule, a string.
    database: the database id of the backup schedule, a string.
    backup_schedule: the backup schedule to read, a string.

  Returns:
    a backup schedule.
  """
  messages = api_utils.GetMessages()
  return _GetBackupSchedulesService().Get(
      messages.FirestoreProjectsDatabasesBackupSchedulesGetRequest(
          name='projects/{}/databases/{}/backupSchedules/{}'.format(
              project,
              database,
              backup_schedule,
          ),
      )
  )


def ListBackupSchedules(project, database):
  """Lists backup schedules under a database.

  Args:
    project: the project of the database of the backup schedule, a string.
    database: the database id of the backup schedule, a string.

  Returns:
    a list of backup schedules.
  """
  messages = api_utils.GetMessages()
  return list(
      _GetBackupSchedulesService()
      .List(
          messages.FirestoreProjectsDatabasesBackupSchedulesListRequest(
              parent='projects/{}/databases/{}'.format(
                  project,
                  database,
              ),
          )
      )
      .backupSchedules
  )


def DeleteBackupSchedule(project, database, backup_schedule):
  """Deletes a backup schedule.

  Args:
    project: the project of the database of the backup schedule, a string.
    database: the database id of the backup schedule, a string.
    backup_schedule: the backup schedule to delete, a string.

  Returns:
    Empty response message.
  """
  messages = api_utils.GetMessages()
  return _GetBackupSchedulesService().Delete(
      messages.FirestoreProjectsDatabasesBackupSchedulesDeleteRequest(
          name='projects/{}/databases/{}/backupSchedules/{}'.format(
              project,
              database,
              backup_schedule,
          ),
      )
  )


def UpdateBackupSchedule(project, database, backup_schedule, retention):
  """Updates a backup schedule.

  Args:
    project: the project of the database of the backup schedule, a string.
    database: the database id of the backup schedule, a string.
    backup_schedule: the backup to read, a string.
    retention: the retention of the backup schedule, an int. At what relative
      time in the future, compared to the creation time of the backup should the
      backup be deleted. The unit is seconds.

  Returns:
    a backup schedule.
  """
  messages = api_utils.GetMessages()
  backup_schedule_updates = messages.GoogleFirestoreAdminV1BackupSchedule()
  if retention:
    backup_schedule_updates.retention = api_utils.FormatDurationString(
        retention
    )

  return _GetBackupSchedulesService().Patch(
      messages.FirestoreProjectsDatabasesBackupSchedulesPatchRequest(
          name='projects/{}/databases/{}/backupSchedules/{}'.format(
              project,
              database,
              backup_schedule,
          ),
          googleFirestoreAdminV1BackupSchedule=backup_schedule_updates,
      )
  )


def CreateBackupSchedule(
    project, database, retention, recurrence, day_of_week=None
):
  """Creates a backup schedule.

  Args:
    project: the project of the database of the backup schedule, a string.
    database: the database id of the backup schedule, a string.
    retention: the retention of the backup schedule, an int. At what relative
      time in the future, compared to the creation time of the backup should the
      backup be deleted. The unit is seconds.
    recurrence: the recurrence of the backup schedule, a string. The valid
      values are: daily and weekly.
    day_of_week: day of week for weekly backup schdeule.

  Returns:
    a backup schedule.

  Raises:
    InvalidArgumentException: if recurrence is invalid.
    ConflictingArgumentsException: if recurrence is daily but day-of-week is
    provided.
    RequiredArgumentException: if recurrence is weekly but day-of-week is not
    provided.
  """
  messages = api_utils.GetMessages()
  backup_schedule = messages.GoogleFirestoreAdminV1BackupSchedule()
  backup_schedule.retention = api_utils.FormatDurationString(retention)
  if recurrence == 'daily':
    if day_of_week is not None:
      raise ex.ConflictingArgumentsException(
          '--day-of-week',
          'Cannot set day of week for daily backup schedules.',
      )
    backup_schedule.dailyRecurrence = (
        messages.GoogleFirestoreAdminV1DailyRecurrence()
    )
  elif recurrence == 'weekly':
    if day_of_week is None:
      raise ex.RequiredArgumentException(
          '--day-of-week',
          'Day of week is required for weekly backup schedules, please use'
          ' --day-of-week to specify this value',
      )
    backup_schedule.weeklyRecurrence = (
        messages.GoogleFirestoreAdminV1WeeklyRecurrence()
    )
    backup_schedule.weeklyRecurrence.day = ConvertDayOfWeek(day_of_week)
  else:
    raise ex.InvalidArgumentException(
        '--recurrence',
        'invalid recurrence: {}. The available values are: `daily` and'
        ' `weekly`.'.format(recurrence),
    )

  return _GetBackupSchedulesService().Create(
      messages.FirestoreProjectsDatabasesBackupSchedulesCreateRequest(
          parent='projects/{}/databases/{}'.format(
              project,
              database,
          ),
          googleFirestoreAdminV1BackupSchedule=backup_schedule,
      )
  )


def ConvertDayOfWeek(day):
  """Converts the user-given day-of-week into DayValueValuesEnum.

  Args:
    day: day of Week for weekly backup schdeule.

  Returns:
    DayValueValuesEnum.

  Raises:
    ValueError: if it is an invalid input.
  """

  day_num = arg_parsers.DayOfWeek.DAYS.index(day)
  messages = api_utils.GetMessages().GoogleFirestoreAdminV1WeeklyRecurrence()
  # a special case for SUN.
  if day_num == 0:
    day_num = 7
  return messages.DayValueValuesEnum(day_num)

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
"""Utility for creating Looker instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core.util import times


def GetMessagesModuleForVersion(version):
  return apis.GetMessagesModule('looker', version)


def ParseToDateTypeV1Alpha1(date):
  """Convert the input to Date Type for v1alpha1 Create method."""
  messages = GetMessagesModuleForVersion('v1alpha1')
  return ParseDate(date, messages)


def ParseToDateTypeV1(date):
  """Convert the input to Date Type for v1 Create method."""
  messages = GetMessagesModuleForVersion('v1')
  return ParseDate(date, messages)


def ParseDate(date, messages, fmt='%Y-%m-%d'):
  """Convert to Date Type."""
  datetime_obj = times.ParseDateTime(date, fmt=fmt)
  return messages.Date(
      year=datetime_obj.year, month=datetime_obj.month, day=datetime_obj.day
  )


def ParseTimeOfDayDenyPeriodV1Alpha1(time_of_day):
  """Convert input to TimeOfDay type for Deny Main Period v1alpha1."""
  messages = GetMessagesModuleForVersion('v1alpha1')
  arg = '--deny-maintenance-period-time'
  error_message = (
      "'--deny-maintenance-period-time' must be used in a valid 24-hr UTC Time"
      ' format.'
  )
  CheckTimeOfDayField(time_of_day, error_message, arg)
  return ParseTimeOfDay(time_of_day, messages)


def ParseTimeOfDayDenyPeriodV1(time_of_day):
  """Convert input to TimeOfDay type for Deny Main Period v1."""
  messages = GetMessagesModuleForVersion('v1')
  arg = '--deny-maintenance-period-time'
  error_message = (
      "'--deny-maintenance-period-time' must be used in a valid 24-hr UTC Time"
      ' format.'
  )
  CheckTimeOfDayField(time_of_day, error_message, arg)
  return ParseTimeOfDay(time_of_day, messages)


def ParseTimeOfDayMainWindowV1Alpha1(time_of_day):
  """Convert input to TimeOfDay type for Main Window v1alpha1."""
  messages = GetMessagesModuleForVersion('v1alpha1')
  arg = '--maintenance-window-time'
  error_message = (
      "'--maintenance-window-time' must be used in a valid 24-hr UTC Time"
      ' format.'
  )
  CheckTimeOfDayField(time_of_day, error_message, arg)
  return ParseTimeOfDay(time_of_day, messages)


def ParseTimeOfDayMainWindowV1(time_of_day):
  """Convert input to TimeOfDay type for Main Window v1."""
  messages = GetMessagesModuleForVersion('v1')
  arg = '--maintenance-window-time'
  error_message = (
      "'--maintenance-window-time' must be used in a valid 24-hr UTC Time"
      ' format.'
  )
  CheckTimeOfDayField(time_of_day, error_message, arg)
  return ParseTimeOfDay(time_of_day, messages)


def CheckTimeOfDayField(time_of_day, error_message, arg):
  """Check if input is a valid TimeOfDay format."""
  hour_and_min = time_of_day.split(':')
  if (
      len(hour_and_min) != 2
      or not hour_and_min[0].isdigit()
      or not hour_and_min[1].isdigit()
  ):
    raise exceptions.InvalidArgumentException(arg, error_message)

  hour = int(hour_and_min[0])
  minute = int(hour_and_min[1])

  if hour < 0 or minute < 0 or hour > 23 or minute > 59:
    raise exceptions.InvalidArgumentException(arg, error_message)


def ParseTimeOfDay(time_of_day, messages):
  hour_and_min = time_of_day.split(':')
  hour = int(hour_and_min[0])
  minute = int(hour_and_min[1])
  return messages.TimeOfDay(hours=hour, minutes=minute)

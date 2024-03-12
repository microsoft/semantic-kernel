# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute future reservations commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.command_lib.compute.reservations import flags as reservation_flags


def GetNamePrefixFlag():
  """Gets the --name-prefix flag."""
  help_text = """\
  A name prefix for the auto-created reservations when capacity is
  delivered at the start time. Each auto-created reservation name
  starts with the name prefix.
  """
  return base.Argument('--name-prefix', help=help_text)


def GetClearNamePrefixFlag():
  """Gets the --clear-name-prefix flag."""
  help_text = """\
  Clears the name prefix for the system generated reservations.
  """
  return base.Argument(
      '--clear-name-prefix', action='store_true', help=help_text
  )


def GetTotalCountFlag(required=True):
  """Gets the --total-count flag."""
  help_text = """\
  The total number of instances for which capacity assurance is requested at a
  future time period.
  """
  return base.Argument(
      '--total-count', required=required, type=int, help=help_text
  )


def GetStartTimeFlag(required=True):
  """Gets the --start-time flag."""
  return base.Argument(
      '--start-time', required=required, type=str, help=GetStartTimeHelpText()
  )


def GetStartTimeHelpText():
  """Gets the --start-time help text."""
  help_text = """\
  Start time of the Future Reservation. The start time must be an RFC3339 valid
  string formatted by date, time, and timezone or "YYYY-MM-DDTHH:MM:SSZ"; where
  YYYY = year, MM = month, DD = day, HH = hours, MM = minutes, SS = seconds, and
  Z = timezone (i.e. 2021-11-20T07:00:00Z).
  """
  return help_text


def GetEndTimeHelpText():
  """Gets the --end-time help text."""
  help_text = """\
  End time of the Future Reservation. The end time must be an RFC3339 valid
  string formatted by date, time, and timezone or "YYYY-MM-DDTHH:MM:SSZ"; where
  YYYY = year, MM = month, DD = day, HH = hours, MM = minutes, SS = seconds, and
  Z = timezone (i.e. 2021-11-20T07:00:00Z).
  """
  return help_text


def GetAutoDeleteAutoCreatedReservationsFlag(required=False):
  """Gets the --auto-delete-auto-created-reservations flag."""
  help_text = """\
  If specified, the auto-created reservations for a future reservation
  are deleted at the end time (default) or at a specified delete time.
  """
  return base.Argument(
      '--auto-delete-auto-created-reservations',
      action=arg_parsers.StoreTrueFalseAction,
      help=help_text,
      required=required,
  )


def GetAutoCreatedReservationsDeleteTimeFlag(required=False):
  """Gets the --auto-created-reservations-delete-time flag."""
  help_text = """\
  Automatically deletes an auto-created reservations at a specific time.
  The specified time must be an RFC3339 timestamp, which must be
  formatted as "YYYY-MM-DDTHH:MM:SSZ" where YYYY = year, MM = month, DD = day,
  HH = hours, MM = minutes, SS = seconds, and Z = time zone in
  Coordinated Universal Time (UTC). For example, specify 2021-11-20T07:00:00Z.
  """
  return base.Argument(
      '--auto-created-reservations-delete-time',
      required=required,
      type=arg_parsers.Datetime.Parse,
      help=help_text,
  )


def GetAutoCreatedReservationsDurationFlag(required=False):
  """Gets the --auto-created-reservations-duration flag."""
  help_text = """\
  Automatically deletes an auto-created reservations after a specified
  number of days, hours, minutes, or seconds. For example, specify 30m
  for 30 minutes, or 1d2h3m4s for 1 day, 2 hours, 3 minutes, and 4
  seconds. For more information, see $ gcloud topic datetimes.
  """
  return base.Argument(
      '--auto-created-reservations-duration',
      required=required,
      type=arg_parsers.Duration(),
      help=help_text,
  )


def GetDurationHelpText():
  """Gets the --duration help text."""
  help_text = """\
  Alternate way of specifying time in the number of seconds to terminate
  capacity request relative to the start time of a request.
  """
  return help_text


def GetSharedSettingFlag(custom_name=None):
  """Gets the --share-setting flag."""
  help_text = """\
  Specify if this future reservation is shared, and if so, the type of sharing.
  If you omit this flag, this value is local by default.
  """
  return base.Argument(
      custom_name if custom_name else '--share-setting',
      choices=['local', 'projects'],
      help=help_text,
  )


def GetShareWithFlag(custom_name=None):
  """Gets the --share-with flag."""
  help_text = """\
  If this future reservation is shared, provide a comma-separated list
  of projects that this future reservation is shared with.
  The list must contain project IDs or project numbers.
  """
  return base.Argument(
      custom_name if custom_name else '--share-with',
      type=arg_parsers.ArgList(min_length=1),
      metavar='PROJECT',
      help=help_text,
  )


def GetClearShareSettingsFlag():
  """Gets the --clear-share-settings help text."""
  help_text = """\
  Clear share settings on future reservation. This will result in non-shared
  future reservation.
  """
  return base.Argument(
      '--clear-share-settings', action='store_true', help=help_text
  )


def GetClearLocalSsdFlag():
  """Gets the --clear-local-ssd flag."""
  help_text = """\
  Remove all local ssd information on the future reservation.
  """
  return base.Argument('--clear-local-ssd', action='store_true', help=help_text)


def GetClearAcceleratorFlag():
  """Gets the --clear-accelerator flag."""
  help_text = """\
  Remove all accelerators from the future reservation.
  """
  return base.Argument(
      '--clear-accelerator', action='store_true', help=help_text
  )


def GetPlanningStatusFlag():
  """Gets the --planning-status flag."""
  help_text = """\
  The planning status of the future reservation. The default value is DRAFT.
  While in DRAFT, any changes to the future reservation's properties will be
  allowed. If set to SUBMITTED, the future reservation will submit and its
  procurementStatus will change to PENDING_APPROVAL. Once the future reservation
  is pending approval, changes to the future reservation's properties will not
  be allowed.
  """
  return base.Argument(
      '--planning-status',
      type=lambda x: x.upper(),
      choices={
          'DRAFT': 'Default planning status value.',
          'SUBMITTED': (
              'Planning status value to immediately submit the future'
              ' reservation.'
          ),
      },
      help=help_text,
  )


def GetRequireSpecificReservationFlag():
  """--require-specific-reservation flag."""
  help_text = """\
  Indicate whether the auto-created reservations can be consumed by VMs with
  "any reservation" defined. If enabled, then only VMs that target the
  auto-created reservation by name using `--reservation-affinity=specific` can
  consume from this reservation. Auto-created reservations delivered with this
  flag enabled will inherit the name of the future reservation.
  """
  return base.Argument(
      '--require-specific-reservation',
      action=arg_parsers.StoreTrueFalseAction,
      help=help_text,
  )


def AddCreateFlags(
    parser,
    support_location_hint=False,
    support_share_setting=False,
    support_fleet=False,
    support_instance_template=False,
    support_planning_status=False,
    support_local_ssd_count=False,
    support_auto_delete=False,
    support_require_specific_reservation=False,
):
  """Adds all flags needed for the create command."""
  GetNamePrefixFlag().AddToParser(parser)
  GetTotalCountFlag().AddToParser(parser)
  if support_require_specific_reservation:
    GetRequireSpecificReservationFlag().AddToParser(parser)
  reservation_flags.GetDescriptionFlag(is_fr=True).AddToParser(parser)
  if support_planning_status:
    GetPlanningStatusFlag().AddToParser(parser)

  specific_sku_properties_group = base.ArgumentGroup(
      'Manage the instance properties for the auto-created reservations. You'
      ' must either provide a source instance template or define the instance'
      ' properties.',
      required=True,
      mutex=True,
  )

  if support_instance_template:
    specific_sku_properties_group.AddArgument(
        reservation_flags.GetSourceInstanceTemplateFlag()
    )

  AddTimeWindowFlags(parser, time_window_requird=True)

  instance_properties_group = base.ArgumentGroup(
      'Define individual instance properties for the specific SKU reservation.'
  )
  instance_properties_group.AddArgument(reservation_flags.GetMachineType())
  instance_properties_group.AddArgument(reservation_flags.GetMinCpuPlatform())
  if support_local_ssd_count:
    instance_properties_group.AddArgument(
        reservation_flags.GetLocalSsdFlagWithCount()
    )
  else:
    instance_properties_group.AddArgument(reservation_flags.GetLocalSsdFlag())
  instance_properties_group.AddArgument(reservation_flags.GetAcceleratorFlag())
  if support_location_hint:
    instance_properties_group.AddArgument(reservation_flags.GetLocationHint())
  if support_fleet:
    instance_properties_group.AddArgument(
        instance_flags.AddMaintenanceFreezeDuration()
    )
    instance_properties_group.AddArgument(
        instance_flags.AddMaintenanceInterval()
    )

  specific_sku_properties_group.AddArgument(instance_properties_group)
  specific_sku_properties_group.AddToParser(parser)

  if support_share_setting:
    share_group = base.ArgumentGroup(
        'Manage the properties of a shared reservation.', required=False
    )
    share_group.AddArgument(GetSharedSettingFlag())
    share_group.AddArgument(GetShareWithFlag())
    share_group.AddToParser(parser)

  if support_auto_delete:
    AddAutoDeleteFlags(parser)


def AddUpdateFlags(
    parser,
    support_location_hint=False,
    support_fleet=False,
    support_planning_status=False,
    support_local_ssd_count=False,
    support_share_setting=False,
    support_auto_delete=False,
    support_require_specific_reservation=False,
):
  """Adds all flags needed for the update command."""

  name_prefix_group = base.ArgumentGroup(
      'Manage the name-prefix of a future reservation.',
      required=False,
      mutex=True
  )
  name_prefix_group.AddArgument(GetNamePrefixFlag())
  name_prefix_group.AddArgument(GetClearNamePrefixFlag())
  name_prefix_group.AddToParser(parser)

  GetTotalCountFlag(required=False).AddToParser(parser)
  reservation_flags.GetDescriptionFlag(is_fr=True).AddToParser(parser)

  if support_planning_status:
    GetPlanningStatusFlag().AddToParser(parser)
  group = base.ArgumentGroup(
      'Manage the specific SKU reservation properties.', required=False
  )
  group.AddArgument(reservation_flags.GetMachineType(required=False))
  group.AddArgument(reservation_flags.GetMinCpuPlatform())

  accelerator_group = base.ArgumentGroup(
      'Manage the accelerators of a future reservation.',
      required=False,
      mutex=True,
  )
  accelerator_group.AddArgument(reservation_flags.GetAcceleratorFlag())
  accelerator_group.AddArgument(GetClearAcceleratorFlag())
  group.AddArgument(accelerator_group)

  local_ssd_group = base.ArgumentGroup(
      'Manage the local ssd of a future reservation.',
      required=False,
      mutex=True,
  )
  if support_local_ssd_count:
    local_ssd_group.AddArgument(reservation_flags.GetLocalSsdFlagWithCount())
  else:
    local_ssd_group.AddArgument(reservation_flags.GetLocalSsdFlag())
  local_ssd_group.AddArgument(GetClearLocalSsdFlag())
  group.AddArgument(local_ssd_group)

  if support_location_hint:
    group.AddArgument(reservation_flags.GetLocationHint())
  if support_fleet:
    group.AddArgument(instance_flags.AddMaintenanceInterval())
  group.AddToParser(parser)
  AddTimeWindowFlags(parser, time_window_requird=False)

  if support_share_setting:
    share_group = base.ArgumentGroup(
        'Manage the properties of a shared future reservation.',
        required=False,
        mutex=True,
    )
    share_group.AddArgument(GetClearShareSettingsFlag())

    share_setting_group = base.ArgumentGroup(
        'Manage the share settings of a future reservation.', required=False
    )
    share_setting_group.AddArgument(GetSharedSettingFlag())
    share_setting_group.AddArgument(GetShareWithFlag())

    share_group.AddArgument(share_setting_group)
    share_group.AddToParser(parser)

  if support_auto_delete:
    AddAutoDeleteFlags(parser, is_update=True)

  if support_require_specific_reservation:
    GetRequireSpecificReservationFlag().AddToParser(parser)


def AddAutoDeleteFlags(parser, is_update=False):
  """Adds all flags needed for the modifying the auto-delete properties."""

  GetAutoDeleteAutoCreatedReservationsFlag(
      required=False if is_update else True
  ).AddToParser(parser)

  auto_delete_time_settings_group = base.ArgumentGroup(
      'Manage the auto-delete time properties.',
      required=False,
      mutex=True,
  )

  auto_delete_time_settings_group.AddArgument(
      GetAutoCreatedReservationsDeleteTimeFlag()
  )
  auto_delete_time_settings_group.AddArgument(
      GetAutoCreatedReservationsDurationFlag()
  )

  auto_delete_time_settings_group.AddToParser(parser)


def AddTimeWindowFlags(parser, time_window_requird=False):
  """Adds all flags needed for the modifying the time window properties."""

  time_window_group = parser.add_group(
      help='Manage the time specific properties for requesting future capacity',
      required=time_window_requird,
  )
  time_window_group.add_argument(
      '--start-time', required=time_window_requird, help=GetStartTimeHelpText()
  )
  end_time_window_group = time_window_group.add_mutually_exclusive_group(
      required=time_window_requird
  )
  end_time_window_group.add_argument('--end-time', help=GetEndTimeHelpText())
  end_time_window_group.add_argument(
      '--duration', type=int, help=GetDurationHelpText()
  )

# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Utility functions for Google Compute Engine resource policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import scope as compute_scopes
from googlecloudsdk.command_lib.compute.resource_policies import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import times

_API_TIMEZONE = times.UTC


def _ParseWeeklyDayAndTime(start_time, weekday):
  """Converts the dt and day to _API_TIMEZONE and returns API formatted values.

  Args:
    start_time: The datetime object which represents a start time.
    weekday: The times.Weekday value which corresponds to the weekday.

  Returns:
    The weekday and start_time pair formatted as strings for use by the API
    clients.
  """
  weekday = times.GetWeekdayInTimezone(start_time, weekday, _API_TIMEZONE)
  formatted_time = _FormatStartTime(start_time)
  return weekday.name, formatted_time


def _FormatStartTime(dt):
  return times.FormatDateTime(dt, '%H:%M', _API_TIMEZONE)


def MakeVmMaintenancePolicy(policy_ref, args, messages):
  """Creates a VM Maintenance Window Resource Policy message from args."""
  vm_policy = messages.ResourcePolicyVmMaintenancePolicy()
  if args.IsSpecified('daily_cycle'):
    _, daily_cycle, _ = _ParseCycleFrequencyArgs(args, messages)
    vm_policy.maintenanceWindow = \
      messages.ResourcePolicyVmMaintenancePolicyMaintenanceWindow(
          dailyMaintenanceWindow=daily_cycle)
  else:
    if 1 <= args.concurrency_limit_percent <= 100:
      concurrency_control_group = \
        messages.ResourcePolicyVmMaintenancePolicyConcurrencyControl(
            concurrencyLimit=args.concurrency_limit_percent)
      vm_policy.concurrencyControlGroup = concurrency_control_group
    else:
      raise ValueError('--concurrency-limit-percent must be greater or equal to'
                       ' 1 and less or equal to 100')
  return messages.ResourcePolicy(
      name=policy_ref.Name(),
      description=args.description,
      region=policy_ref.region,
      vmMaintenancePolicy=vm_policy)


def MakeVmMaintenanceMaintenanceWindow(policy_ref, args, messages):
  """Creates a VM Maintenance window policy message from args."""
  vm_policy = messages.ResourcePolicyVmMaintenancePolicy()
  _, daily_cycle, _ = _ParseCycleFrequencyArgs(args, messages)
  vm_policy.maintenanceWindow = \
    messages.ResourcePolicyVmMaintenancePolicyMaintenanceWindow(
        dailyMaintenanceWindow=daily_cycle)
  return messages.ResourcePolicy(
      name=policy_ref.Name(),
      description=args.description,
      region=policy_ref.region,
      vmMaintenancePolicy=vm_policy)


def MakeVmMaintenanceConcurrentPolicy(policy_ref, args, messages):
  """Creates a VM Maintenance concurrency limit policy message from args."""
  concurrency_control_group = \
    messages.ResourcePolicyVmMaintenancePolicyConcurrencyControl(
        concurrencyLimit=args.max_percent
    )
  vm_policy = messages.ResourcePolicyVmMaintenancePolicy(
      concurrencyControlGroup=concurrency_control_group)

  return messages.ResourcePolicy(
      name=policy_ref.Name(),
      description=args.description,
      region=policy_ref.region,
      vmMaintenancePolicy=vm_policy)


def MakeDiskSnapshotSchedulePolicy(policy_ref, args, messages):
  """Creates a Disk Snapshot Schedule Resource Policy message from args."""
  hourly_cycle, daily_cycle, weekly_cycle = _ParseCycleFrequencyArgs(
      args, messages, supports_hourly=True, supports_weekly=True)

  snapshot_properties = None
  snapshot_labels = labels_util.ParseCreateArgs(
      args,
      messages.ResourcePolicySnapshotSchedulePolicySnapshotProperties
      .LabelsValue,
      labels_dest='snapshot_labels')
  storage_location = [args.storage_location] if args.storage_location else []
  if args.IsSpecified('guest_flush') or snapshot_labels or storage_location:
    snapshot_properties = (
        messages.ResourcePolicySnapshotSchedulePolicySnapshotProperties(
            guestFlush=args.guest_flush,
            labels=snapshot_labels,
            storageLocations=storage_location))
  snapshot_policy = messages.ResourcePolicySnapshotSchedulePolicy(
      retentionPolicy=messages
      .ResourcePolicySnapshotSchedulePolicyRetentionPolicy(
          maxRetentionDays=args.max_retention_days,
          onSourceDiskDelete=flags.GetOnSourceDiskDeleteFlagMapper(
              messages).GetEnumForChoice(args.on_source_disk_delete)),
      schedule=messages.ResourcePolicySnapshotSchedulePolicySchedule(
          hourlySchedule=hourly_cycle,
          dailySchedule=daily_cycle,
          weeklySchedule=weekly_cycle),
      snapshotProperties=snapshot_properties)
  return messages.ResourcePolicy(
      name=policy_ref.Name(),
      description=args.description,
      region=policy_ref.region,
      snapshotSchedulePolicy=snapshot_policy)


def MakeDiskSnapshotSchedulePolicyForUpdate(policy_ref, args, messages):
  """Creates a Disk Snapshot Schedule Resource Policy message from args used in ResourcePolicy.Patch.
  """
  hourly_cycle, daily_cycle, weekly_cycle = _ParseCycleFrequencyArgs(
      args, messages, supports_hourly=True, supports_weekly=True)

  snapshot_properties, snapshot_schedule, description = None, None, None
  snapshot_labels = labels_util.ParseCreateArgs(
      args,
      messages.ResourcePolicySnapshotSchedulePolicySnapshotProperties
      .LabelsValue,
      labels_dest='snapshot_labels')
  if snapshot_labels:
    snapshot_properties = (
        messages.ResourcePolicySnapshotSchedulePolicySnapshotProperties(
            labels=snapshot_labels))

  if args.IsSpecified('description'):
    description = args.description

  retention_policy = None
  if (args.max_retention_days or args.on_source_disk_delete):
    retention_policy = (
        messages.ResourcePolicySnapshotSchedulePolicyRetentionPolicy(
            maxRetentionDays=args.max_retention_days,
            onSourceDiskDelete=flags.GetOnSourceDiskDeleteFlagMapper(
                messages).GetEnumForChoice(args.on_source_disk_delete)))

  if hourly_cycle or daily_cycle or weekly_cycle:
    snapshot_schedule = messages.ResourcePolicySnapshotSchedulePolicySchedule(
        hourlySchedule=hourly_cycle,
        dailySchedule=daily_cycle,
        weeklySchedule=weekly_cycle)

  snapshot_policy = None
  if snapshot_schedule or snapshot_properties or retention_policy:
    snapshot_policy = messages.ResourcePolicySnapshotSchedulePolicy(
        schedule=snapshot_schedule, snapshotProperties=snapshot_properties,
        retentionPolicy=retention_policy)

  return messages.ResourcePolicy(
      name=policy_ref.Name(),
      description=description,
      snapshotSchedulePolicy=snapshot_policy)


def MakeInstanceSchedulePolicy(policy_ref, args, messages):
  """Creates an Instance Schedule Policy message from args."""

  vm_start_schedule = None
  if args.vm_start_schedule:
    vm_start_schedule = messages.ResourcePolicyInstanceSchedulePolicySchedule(
        schedule=args.vm_start_schedule)

  vm_stop_schedule = None
  if args.vm_stop_schedule:
    vm_stop_schedule = messages.ResourcePolicyInstanceSchedulePolicySchedule(
        schedule=args.vm_stop_schedule)

  instance_schedule_policy = messages.ResourcePolicyInstanceSchedulePolicy(
      timeZone=args.timezone,
      vmStartSchedule=vm_start_schedule,
      vmStopSchedule=vm_stop_schedule)

  if args.initiation_date:
    instance_schedule_policy.startTime = times.FormatDateTime(
        args.initiation_date)

  if args.end_date:
    instance_schedule_policy.expirationTime = times.FormatDateTime(
        args.end_date)

  return messages.ResourcePolicy(
      name=policy_ref.Name(),
      description=args.description,
      region=policy_ref.region,
      instanceSchedulePolicy=instance_schedule_policy)


def MakeGroupPlacementPolicy(policy_ref, args, messages, track):
  """Creates a Group Placement Resource Policy message from args."""
  availability_domain_count = None
  if args.IsSpecified('availability_domain_count'):
    availability_domain_count = args.availability_domain_count
  collocation = None
  if args.IsSpecified('collocation'):
    collocation = flags.GetCollocationFlagMapper(
        messages, track).GetEnumForChoice(args.collocation)
  placement_policy = None
  if track == base.ReleaseTrack.ALPHA and args.IsSpecified('scope'):
    scope = flags.GetAvailabilityDomainScopeFlagMapper(
        messages).GetEnumForChoice(args.scope)
    placement_policy = messages.ResourcePolicyGroupPlacementPolicy(
        vmCount=args.vm_count,
        availabilityDomainCount=availability_domain_count,
        collocation=collocation,
        scope=scope,
    )
  elif track == base.ReleaseTrack.ALPHA and args.IsSpecified('tpu_topology'):
    placement_policy = messages.ResourcePolicyGroupPlacementPolicy(
        vmCount=args.vm_count,
        collocation=collocation,
        tpuTopology=args.tpu_topology,
    )
  elif track in (
      base.ReleaseTrack.ALPHA,
      base.ReleaseTrack.BETA,
  ) and args.IsSpecified('max_distance'):
    placement_policy = messages.ResourcePolicyGroupPlacementPolicy(
        vmCount=args.vm_count,
        collocation=collocation,
        maxDistance=args.max_distance,
    )
  else:
    placement_policy = messages.ResourcePolicyGroupPlacementPolicy(
        vmCount=args.vm_count,
        availabilityDomainCount=availability_domain_count,
        collocation=collocation,
    )

  return messages.ResourcePolicy(
      name=policy_ref.Name(),
      description=args.description,
      region=policy_ref.region,
      groupPlacementPolicy=placement_policy)


def MakeDiskConsistencyGroupPolicy(policy_ref, args, messages):
  """Creates a Disk Consistency Group Resource Policy message from args.

  Args:
    policy_ref: resource reference of the Disk Consistency Group policy.
    args: Namespace, argparse.Namespace.
    messages: message classes.

  Returns:
    A messages.ResourcePolicy object for Disk Consistency Group Resource Policy.
  """
  consistency_group_policy = messages.ResourcePolicyDiskConsistencyGroupPolicy()

  return messages.ResourcePolicy(
      name=policy_ref.Name(),
      description=args.description,
      region=policy_ref.region,
      diskConsistencyGroupPolicy=consistency_group_policy)


def _ParseCycleFrequencyArgs(args,
                             messages,
                             supports_hourly=False,
                             supports_weekly=False):
  """Parses args and returns a tuple of DailyCycle and WeeklyCycle messages."""
  _ValidateCycleFrequencyArgs(args)

  hourly_cycle, daily_cycle, weekly_cycle = None, None, None
  if args.daily_cycle:
    daily_cycle = messages.ResourcePolicyDailyCycle(
        daysInCycle=1, startTime=_FormatStartTime(args.start_time))
  if supports_weekly:
    if args.weekly_cycle:
      day_enum = messages.ResourcePolicyWeeklyCycleDayOfWeek.DayValueValuesEnum
      weekday = times.Weekday.Get(args.weekly_cycle.upper())
      day, start_time = _ParseWeeklyDayAndTime(args.start_time, weekday)
      weekly_cycle = messages.ResourcePolicyWeeklyCycle(dayOfWeeks=[
          messages.ResourcePolicyWeeklyCycleDayOfWeek(
              day=day_enum(day), startTime=start_time)
      ])
    if args.IsSpecified('weekly_cycle_from_file'):
      if args.weekly_cycle_from_file:
        weekly_cycle = _ParseWeeklyCycleFromFile(args, messages)
      else:
        raise exceptions.InvalidArgumentException(
            args.GetFlag('weekly_cycle_from_file'), 'File cannot be empty.')
  if supports_hourly and args.hourly_cycle:
    hourly_cycle = messages.ResourcePolicyHourlyCycle(
        hoursInCycle=args.hourly_cycle,
        startTime=_FormatStartTime(args.start_time))
  return hourly_cycle, daily_cycle, weekly_cycle


def _ValidateCycleFrequencyArgs(args):
  """Validates cycle frequency args."""
  if args.IsSpecified('daily_cycle') and not args.daily_cycle:
    raise exceptions.InvalidArgumentException(
        args.GetFlag('daily_cycle'), 'cannot request a non-daily cycle.')


def _ParseWeeklyCycleFromFile(args, messages):
  """Parses WeeklyCycle message from file contents specified in args."""
  weekly_cycle_dict = yaml.load(args.weekly_cycle_from_file)
  day_enum = messages.ResourcePolicyWeeklyCycleDayOfWeek.DayValueValuesEnum
  days_of_week = []
  for day_and_time in weekly_cycle_dict:
    if 'day' not in day_and_time or 'startTime' not in day_and_time:
      raise exceptions.InvalidArgumentException(
          args.GetFlag('weekly_cycle_from_file'),
          'Each JSON/YAML object in the list must have the following keys: '
          '[day, startTime].')
    day = day_and_time['day'].upper()
    try:
      weekday = times.Weekday.Get(day)
    except KeyError:
      raise exceptions.InvalidArgumentException(
          args.GetFlag('weekly_cycle_from_file'),
          'Invalid value for `day`: [{}].'.format(day))
    start_time = arg_parsers.Datetime.ParseUtcTime(day_and_time['startTime'])
    day, start_time = _ParseWeeklyDayAndTime(start_time, weekday)
    days_of_week.append(
        messages.ResourcePolicyWeeklyCycleDayOfWeek(
            day=day_enum(day), startTime=start_time))
  return messages.ResourcePolicyWeeklyCycle(dayOfWeeks=days_of_week)


def ParseResourcePolicy(resources, name, project=None, region=None):
  return resources.Parse(
      name, {
          'project': project,
          'region': region
      },
      collection='compute.resourcePolicies')


def ParseResourcePolicyWithZone(resources, name, project, zone):
  region = utils.ZoneNameToRegionName(zone)
  return ParseResourcePolicy(resources, name, project, region)


def ParseResourcePolicyWithScope(resources, name, project, location, scope):
  if scope == compute_scopes.ScopeEnum.ZONE:
    region = utils.ZoneNameToRegionName(location)
  elif scope == compute_scopes.ScopeEnum.REGION:
    region = location
  return ParseResourcePolicy(resources, name, project, region)

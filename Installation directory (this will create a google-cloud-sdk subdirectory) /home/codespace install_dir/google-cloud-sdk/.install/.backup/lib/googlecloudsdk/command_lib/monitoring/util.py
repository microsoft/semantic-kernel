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
"""Util methods for Stackdriver Monitoring Surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from apitools.base.py import encoding
from googlecloudsdk.calliope import exceptions as calliope_exc
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import times
import six


CHANNELS_FIELD_REMAPPINGS = {'channelLabels': 'labels'}

SNOOZE_FIELD_DELETIONS = ['criteria']

MIGRATED_FROM_PROMETHEUS_TEXT = (
    'Notification channel migrated from Prometheus alert manager file'
)


class YamlOrJsonLoadError(exceptions.Error):
  """Exception for when a JSON or YAML string could not loaded as a message."""


class NoUpdateSpecifiedError(exceptions.Error):
  """Exception for when user passes no arguments that specifies an update."""


class ConditionNotFoundError(exceptions.Error):
  """Indiciates the Condition the user specified does not exist."""


class ConflictingFieldsError(exceptions.Error):
  """Inidicates that the JSON or YAML string have conflicting fields."""


class MonitoredProjectNameError(exceptions.Error):
  """Inidicates that an invalid Monitored Project name has been specified."""


class MissingRequiredFieldError(exceptions.Error):
  """Inidicates that supplied policy/alert rule is missing required field(s)."""


def ValidateUpdateArgsSpecified(args, update_arg_dests, resource):
  if not any([args.IsSpecified(dest) for dest in update_arg_dests]):
    raise NoUpdateSpecifiedError(
        'Did not specify any flags for updating the {}.'.format(resource))


def _RemapFields(yaml_obj, field_remappings):
  for field_name, remapped_name in six.iteritems(field_remappings):
    if field_name in yaml_obj:
      if remapped_name in yaml_obj:
        raise ConflictingFieldsError('Cannot specify both {} and {}.'.format(
            field_name, remapped_name))
      yaml_obj[remapped_name] = yaml_obj.pop(field_name)
  return yaml_obj


def _DeleteFields(yaml_obj, field_deletions):
  for field_name in field_deletions:
    if field_name in yaml_obj:
      yaml_obj.pop(field_name)
  return yaml_obj


def MessageFromString(msg_string, message_type, display_type,
                      field_remappings=None, field_deletions=None):
  try:
    msg_as_yaml = yaml.load(msg_string)
    if field_remappings:
      msg_as_yaml = _RemapFields(msg_as_yaml, field_remappings)
    if field_deletions:
      msg_as_yaml = _DeleteFields(msg_as_yaml, field_deletions)
    msg = encoding.PyValueToMessage(message_type, msg_as_yaml)
    return msg
  except Exception as exc:  # pylint: disable=broad-except
    raise YamlOrJsonLoadError(
        'Could not parse YAML or JSON string for [{0}]: {1}'.format(
            display_type, exc))


def _FlagToDest(flag_name):
  """Converts a --flag-arg to its dest name."""
  return flag_name[len('--'):].replace('-', '_')


def _FormatDuration(duration):
  return '{}s'.format(duration)


def GetBasePolicyMessageFromArgs(args, policy_class):
  """Returns the base policy from args."""
  if args.IsSpecified('policy') or args.IsSpecified('policy_from_file'):
    # Policy and policy_from_file are in a mutex group.
    policy_string = args.policy or args.policy_from_file
    policy = MessageFromString(policy_string, policy_class, 'AlertPolicy')
  else:
    policy = policy_class()
  return policy


def CheckConditionArgs(args):
  """Checks if condition arguments exist and are specified correctly.

  Args:
    args: argparse.Namespace, the parsed arguments.
  Returns:
    bool: True, if '--condition-filter' is specified.
  Raises:
    RequiredArgumentException:
      if '--if' is not set but '--condition-filter' is specified.
    InvalidArgumentException:
      if flag in should_not_be_set is specified without '--condition-filter'.
  """

  if args.IsSpecified('condition_filter'):
    if not args.IsSpecified('if_value'):
      raise calliope_exc.RequiredArgumentException(
          '--if',
          'If --condition-filter is set then --if must be set as well.')
    return True
  else:
    should_not_be_set = [
        '--aggregation',
        '--duration',
        '--trigger-count',
        '--trigger-percent',
        '--condition-display-name',
        '--if',
        '--combiner'
    ]
    for flag in should_not_be_set:
      if flag == '--if':
        dest = 'if_value'
      else:
        dest = _FlagToDest(flag)
      if args.IsSpecified(dest):
        raise calliope_exc.InvalidArgumentException(
            flag,
            'Should only be specified if --condition-filter is also specified.')
    return False


def BuildCondition(messages, condition=None, display_name=None,
                   aggregations=None, trigger_count=None,
                   trigger_percent=None, duration=None, condition_filter=None,
                   if_value=None):
  """Populates the fields of a Condition message from args.

  Args:
    messages: module, module containing message classes for the stackdriver api
    condition: Condition or None, a base condition to populate the fields of.
    display_name: str, the display name for the condition.
    aggregations: list[Aggregation], list of Aggregation messages for the
      condition.
    trigger_count: int, corresponds to the count field of the condition trigger.
    trigger_percent: float, corresponds to the percent field of the condition
      trigger.
    duration: int, The amount of time that a time series must fail to report new
      data to be considered failing.
    condition_filter: str, A filter that identifies which time series should be
      compared with the threshold.
    if_value: tuple[str, float] or None, a tuple containing a string value
      corresponding to the comparison value enum and a float with the condition
      threshold value. None indicates that this should be an Absence condition.

  Returns:
    Condition, a condition with its fields populated from the args
  """
  if not condition:
    condition = messages.Condition()

  if display_name is not None:
    condition.displayName = display_name

  trigger = None
  if trigger_count or trigger_percent:
    trigger = messages.Trigger(
        count=trigger_count, percent=trigger_percent)

  kwargs = {
      'trigger': trigger,
      'duration': duration,
      'filter': condition_filter,
  }

  # This should be unset, not None, if empty
  if aggregations:
    kwargs['aggregations'] = aggregations

  if if_value is not None:
    comparator, threshold_value = if_value  # pylint: disable=unpacking-non-sequence
    if not comparator:
      condition.conditionAbsent = messages.MetricAbsence(**kwargs)
    else:
      comparison_enum = messages.MetricThreshold.ComparisonValueValuesEnum
      condition.conditionThreshold = messages.MetricThreshold(
          comparison=getattr(comparison_enum, comparator),
          thresholdValue=threshold_value,
          **kwargs)

  return condition


def ParseNotificationChannel(channel_name, project=None):
  project = project or properties.VALUES.core.project.Get(required=True)
  return resources.REGISTRY.Parse(
      channel_name, params={'projectsId': project},
      collection='monitoring.projects.notificationChannels')


def ModifyAlertPolicy(base_policy, messages, display_name=None, combiner=None,
                      documentation_content=None, documentation_format=None,
                      enabled=None, channels=None, field_masks=None):
  """Override and/or add fields from other flags to an Alert Policy."""
  if field_masks is None:
    field_masks = []

  if display_name is not None:
    field_masks.append('display_name')
    base_policy.displayName = display_name

  if ((documentation_content is not None or documentation_format is not None)
      and not base_policy.documentation):
    base_policy.documentation = messages.Documentation()
  if documentation_content is not None:
    field_masks.append('documentation.content')
    base_policy.documentation.content = documentation_content
  if documentation_format is not None:
    field_masks.append('documentation.mime_type')
    base_policy.documentation.mimeType = documentation_format

  if enabled is not None:
    field_masks.append('enabled')
    base_policy.enabled = enabled

  # None indicates no update and empty list indicates we want to explicitly set
  # an empty list.
  if channels is not None:
    field_masks.append('notification_channels')
    base_policy.notificationChannels = channels

  if combiner is not None:
    field_masks.append('combiner')
    combiner = arg_utils.ChoiceToEnum(
        combiner, base_policy.CombinerValueValuesEnum, item_type='combiner')
    base_policy.combiner = combiner


def ValidateAtleastOneSpecified(args, flags):
  if not any([args.IsSpecified(_FlagToDest(flag))
              for flag in flags]):
    raise calliope_exc.MinimumArgumentException(flags)


def CreateAlertPolicyFromArgs(args, messages):
  """Builds an AleryPolicy message from args."""
  policy_base_flags = ['--display-name', '--policy', '--policy-from-file']
  ValidateAtleastOneSpecified(args, policy_base_flags)

  # Get a base policy object from the flags
  policy = GetBasePolicyMessageFromArgs(args, messages.AlertPolicy)
  combiner = args.combiner if args.IsSpecified('combiner') else None
  enabled = args.enabled if args.IsSpecified('enabled') else None
  channel_refs = args.CONCEPTS.notification_channels.Parse() or []
  channels = [channel.RelativeName() for channel in channel_refs] or None
  documentation_content = args.documentation or args.documentation_from_file
  documentation_format = (
      args.documentation_format if documentation_content else None)
  ModifyAlertPolicy(
      policy,
      messages,
      display_name=args.display_name,
      combiner=combiner,
      documentation_content=documentation_content,
      documentation_format=documentation_format,
      enabled=enabled,
      channels=channels)

  if CheckConditionArgs(args):
    aggregations = None
    if args.aggregation:
      aggregations = [MessageFromString(
          args.aggregation, messages.Aggregation, 'Aggregation')]

    condition = BuildCondition(
        messages,
        display_name=args.condition_display_name,
        aggregations=aggregations,
        trigger_count=args.trigger_count,
        trigger_percent=args.trigger_percent,
        duration=_FormatDuration(args.duration),
        condition_filter=args.condition_filter,
        if_value=args.if_value)
    policy.conditions.append(condition)

  return policy


def GetConditionFromArgs(args, messages):
  """Builds a Condition message from args."""
  condition_base_flags = ['--condition-filter', '--condition',
                          '--condition-from-file']
  ValidateAtleastOneSpecified(args, condition_base_flags)

  condition = None
  condition_string = args.condition or args.condition_from_file
  if condition_string:
    condition = MessageFromString(
        condition_string, messages.Condition, 'Condition')

  aggregations = None
  if args.aggregation:
    aggregations = [MessageFromString(
        args.aggregation, messages.Aggregation, 'Aggregation')]

  return BuildCondition(
      messages,
      condition=condition,
      display_name=args.condition_display_name,
      aggregations=aggregations,
      trigger_count=args.trigger_count,
      trigger_percent=args.trigger_percent,
      duration=_FormatDuration(args.duration),
      condition_filter=args.condition_filter,
      if_value=args.if_value)


def GetConditionFromPolicy(condition_name, policy):
  for condition in policy.conditions:
    if condition.name == condition_name:
      return condition

  raise ConditionNotFoundError(
      'No condition with name [{}] found in policy.'.format(condition_name))


def RemoveConditionFromPolicy(condition_name, policy):
  for i, condition in enumerate(policy.conditions):
    if condition.name == condition_name:
      policy.conditions.pop(i)
      return policy

  raise ConditionNotFoundError(
      'No condition with name [{}] found in policy.'.format(condition_name))


def ModifyNotificationChannel(base_channel, channel_type=None, enabled=None,
                              display_name=None, description=None,
                              field_masks=None):
  """Modifies base_channel's properties using the passed arguments."""
  if field_masks is None:
    field_masks = []

  if channel_type is not None:
    field_masks.append('type')
    base_channel.type = channel_type
  if display_name is not None:
    field_masks.append('display_name')
    base_channel.displayName = display_name
  if description is not None:
    field_masks.append('description')
    base_channel.description = description
  if enabled is not None:
    field_masks.append('enabled')
    base_channel.enabled = enabled
  return base_channel


def GetNotificationChannelFromArgs(args, messages):
  """Builds a NotificationChannel message from args."""
  channels_base_flags = ['--display-name', '--channel-content',
                         '--channel-content-from-file']
  ValidateAtleastOneSpecified(args, channels_base_flags)

  channel_string = args.channel_content or args.channel_content_from_file
  if channel_string:
    channel = MessageFromString(channel_string, messages.NotificationChannel,
                                'NotificationChannel',
                                field_remappings=CHANNELS_FIELD_REMAPPINGS)
    # Without this, labels will be in a random order every time.
    if channel.labels:
      channel.labels.additionalProperties = sorted(
          channel.labels.additionalProperties, key=lambda prop: prop.key)
  else:
    channel = messages.NotificationChannel()

  enabled = args.enabled if args.IsSpecified('enabled') else None
  return ModifyNotificationChannel(channel,
                                   channel_type=args.type,
                                   display_name=args.display_name,
                                   description=args.description,
                                   enabled=enabled)


def ParseCreateLabels(labels, labels_cls):
  return encoding.DictToAdditionalPropertyMessage(
      labels, labels_cls, sort_items=True)


def ProcessUpdateLabels(args, labels_name, labels_cls, orig_labels):
  """Returns the result of applying the diff constructed from args.

  This API doesn't conform to the standard patch semantics, and instead does
  a replace operation on update. Therefore, if there are no updates to do,
  then the original labels must be returned as writing None into the labels
  field would replace it.

  Args:
    args: argparse.Namespace, the parsed arguments with update_labels,
      remove_labels, and clear_labels
    labels_name: str, the name for the labels flag.
    labels_cls: type, the LabelsValue class for the new labels.
    orig_labels: message, the original LabelsValue value to be updated.

  Returns:
    LabelsValue: The updated labels of type labels_cls.

  Raises:
    ValueError: if the update does not change the labels.
  """
  labels_diff = labels_util.Diff(
      additions=getattr(args, 'update_' + labels_name),
      subtractions=getattr(args, 'remove_' + labels_name),
      clear=getattr(args, 'clear_' + labels_name))
  if not labels_diff.MayHaveUpdates():
    return None

  return labels_diff.Apply(labels_cls, orig_labels).GetOrNone()


def ParseMonitoredProject(monitored_project_name, project_fallback):
  """Returns the metrics scope and monitored project.

  Parse the specified monitored project name and return the metrics scope and
  monitored project.

  Args:
    monitored_project_name: The name of the monitored project to create/delete.
    project_fallback: When set, allows monitored_project_name to be just a
      project id or number.

  Raises:
    MonitoredProjectNameError: If an invalid monitored project name is
    specified.

  Returns:
     (metrics_scope_def, monitored_project_def): Project parsed metrics scope
       project id, Project parsed metrics scope project id
  """
  matched = re.match(
      'locations/global/metricsScopes/([a-z0-9:\\-]+)/projects/([a-z0-9:\\-]+)',
      monitored_project_name)
  if matched:
    if matched.group(0) != monitored_project_name:
      raise MonitoredProjectNameError(
          'Invalid monitored project name has been specified.')
    # full name
    metrics_scope_def = projects_util.ParseProject(matched.group(1))
    monitored_project_def = projects_util.ParseProject(matched.group(2))
  else:
    metrics_scope_def = projects_util.ParseProject(
        properties.VALUES.core.project.Get(required=True))
    monitored_resource_container_matched = re.match(
        'projects/([a-z0-9:\\-]+)', monitored_project_name
    )
    if monitored_resource_container_matched:
      monitored_project_def = projects_util.ParseProject(
          monitored_resource_container_matched.group(1)
      )
    elif project_fallback:
      log.warning(
          'Received an incorrectly formatted project name. Expected '
          '"projects/{identifier}" received "{identifier}". Assuming '
          'given resource is a project.'.format(
              identifier=monitored_project_name
          )
      )
      monitored_project_def = projects_util.ParseProject(monitored_project_name)
    else:
      raise MonitoredProjectNameError(
          'Invalid monitored project name has been specified.'
      )
  return metrics_scope_def, monitored_project_def


def ParseMonitoredResourceContainer(
    monitored_resource_container_name, project_fallback
):
  """Returns the monitored resource container identifier.

  Parse the specified monitored_resource_container_name and return the
  identifier.

  Args:
    monitored_resource_container_name: The monitored resource container. Ex -
      projects/12345.
    project_fallback: When set, allows monitored_resource_container_name to be
      just a project id or number.

  Raises:
    MonitoredProjectNameError: If an invalid monitored project name is
    specified.

  Returns:
     resource_type, monitored_resource_container_identifier: Monitored resource
     container type and identifier
  """
  matched = re.match(
      '(projects)/([a-z0-9:\\-]+)', monitored_resource_container_name
  )
  if matched:
    return matched.group(1), matched.group(2)
  elif project_fallback:
    log.warning(
        'Received an incorrectly formatted project name. Expected '
        '"projects/{identifier}" received "{identifier}". Assuming '
        'given resource is a project.'.format(
            identifier=monitored_resource_container_name
        )
    )
    return (
        'projects',
        projects_util.ParseProject(monitored_resource_container_name).Name(),
    )
  else:
    raise MonitoredProjectNameError(
        'Invalid monitored project name has been specified.'
    )


def ParseSnooze(snooze_name, project=None):
  project = project or properties.VALUES.core.project.Get(required=True)
  return resources.REGISTRY.Parse(
      snooze_name,
      params={'projectsId': project},
      collection='monitoring.projects.snoozes',
  )


def GetBaseSnoozeMessageFromArgs(args, snooze_class, update=False):
  """Returns the base snooze from args."""
  if args.IsSpecified('snooze_from_file'):
    snooze_string = args.snooze_from_file
    if update:
      snooze = MessageFromString(
          snooze_string,
          snooze_class,
          'Snooze',
          field_deletions=SNOOZE_FIELD_DELETIONS,
      )
    else:
      snooze = MessageFromString(
          snooze_string,
          snooze_class,
          'Snooze',
      )
  else:
    snooze = snooze_class()
  return snooze


def ModifySnooze(
    base_snooze,
    messages,
    display_name=None,
    criteria_policies=None,
    start_time=None,
    end_time=None,
    field_masks=None,
):
  """Override and/or add fields from other flags to an Snooze."""
  if field_masks is None:
    field_masks = []

  start_time_target = None
  start_time_from_base = False
  if start_time is not None:
    field_masks.append('interval.start_time')
    start_time_target = start_time
  else:
    try:
      start_time_target = times.ParseDateTime(base_snooze.interval.startTime)
      start_time_from_base = True
    except AttributeError:
      pass

  end_time_target = None
  end_time_from_base = False
  if end_time is not None:
    field_masks.append('interval.end_time')
    end_time_target = end_time
  else:
    try:
      end_time_target = times.ParseDateTime(base_snooze.interval.endTime)
      end_time_from_base = True
    except AttributeError:
      pass

  try:
    if start_time_target is not None and not start_time_from_base:
      base_snooze.interval.startTime = times.FormatDateTime(start_time_target)
    if end_time_target is not None and not end_time_from_base:
      base_snooze.interval.endTime = times.FormatDateTime(end_time_target)
  except AttributeError:
    interval = messages.TimeInterval()
    interval.startTime = times.FormatDateTime(start_time_target)
    interval.endTime = times.FormatDateTime(end_time_target)
    base_snooze.interval = interval

  if display_name is not None:
    field_masks.append('display_name')
    base_snooze.displayName = display_name

  if criteria_policies is not None:
    field_masks.append('criteria_policies')
    criteria = messages.Criteria()
    criteria.policies = criteria_policies
    base_snooze.criteria = criteria


def CreateSnoozeFromArgs(args, messages):
  """Builds a Snooze message from args."""
  snooze_base_flags = ['--display-name', '--snooze-from-file']
  ValidateAtleastOneSpecified(args, snooze_base_flags)

  # Get a base snooze object from the flags
  snooze = GetBaseSnoozeMessageFromArgs(args, messages.Snooze)

  ModifySnooze(
      snooze,
      messages,
      display_name=args.display_name,
      criteria_policies=args.criteria_policies,
      start_time=args.start_time,
      end_time=args.end_time)

  return snooze


# Conversions from interval suffixes to number of seconds.
# (m => 60s, d => 86400s, etc)
_INTERVAL_CONV_DICT = {'s': 1}
_INTERVAL_CONV_DICT['ms'] = 0.001 * _INTERVAL_CONV_DICT['s']
_INTERVAL_CONV_DICT['m'] = 60 * _INTERVAL_CONV_DICT['s']
_INTERVAL_CONV_DICT['h'] = 60 * _INTERVAL_CONV_DICT['m']
_INTERVAL_CONV_DICT['d'] = 24 * _INTERVAL_CONV_DICT['h']
_INTERVAL_CONV_DICT['w'] = 7 * _INTERVAL_CONV_DICT['d']
_INTERVAL_CONV_DICT['y'] = 365 * _INTERVAL_CONV_DICT['d']
_INTERVAL_PART_REGEXP = re.compile(
    '^([0-9]+)(%s)' % '|'.join(_INTERVAL_CONV_DICT)
)


def ConvertIntervalToSeconds(interval):
  """Forked from datelib.py.

  Convert a formatted Prometheus string representing an interval into seconds.

  The accepted interval string syntax is:
    interval: (interval_part)*
    interval_part: decimal_integer unit
    unit: "ms"       # Milliseconds
        | "s"        # Seconds
        | "m"        # Minutes
        | "h"        # Hours
        | "d"        # Days
        | "w"        # Weeks (7 days)
        | "y"        # Years (365 days)

  No whitespace is allowed.
  The empty string is valid (and equivalent to 0 seconds).
  |decimal_integer| cannot include a sign.
  No endianness ordering is required when using multiple interval_part-s. For
  example, "1s1Y" and "1Y1s" are both valid.

  Examples:
    "45m" = 45 minutes
    "14d12h" = 14 days + 12 hours
    "5d12h30m" = 5 days + 12 hours + 30 minutes

  Args:
    interval: String to interpret as an interval.  See above for a description
      of the syntax.

  Raises:
    ValueError: If the provided time_string contains unexpected
    characters.

  Returns:
    A non-negative integer representing the number of seconds represented by the
    interval string.
  """
  total = 0
  original_interval = interval
  # The initial value of "previous_multiplier" is larger than any valid
  # multiplier.
  previous_multiplier = _INTERVAL_CONV_DICT.get('y') + 1
  while interval:
    # Match the interval_part at the prefix of "interval".
    match = _INTERVAL_PART_REGEXP.match(interval)
    if not match:
      raise ValueError(
          '{} is invalid due to missing unit of time or unexpected'
          ' character(s).'.format(original_interval)
      )

    try:
      num = int(match.group(1))
    except ValueError:
      raise ValueError(
          'Found invalid character in {}, which is neither an integer nor unit'
          ' of time.'.format(original_interval)
      )

    # The time unit suffix should always exist. Otherwise, the previous match()
    # would have failed.
    suffix = match.group(2)
    multiplier = _INTERVAL_CONV_DICT.get(suffix)
    if multiplier >= previous_multiplier:
      # Time units must be ordered from largest to smallest.
      raise ValueError(
          'Time units not ordered from largest to smallest in {}.'.format(
              original_interval
          )
      )

    previous_multiplier = multiplier
    num *= multiplier

    total += num
    # Remove the interval_part prefix from "interval".
    interval = interval[match.end(0) :]
  return total


def ConvertPrometheusTimeStringToEvaluationDurationInSeconds(time_string):
  """Converts Prometheus time to duration JSON string.

  Args:
    time_string: String provided by the alert rule YAML file defining time
      (ex:1h30m)

  Raises:
    ValueError: If the provided time_string is not a multiple of 30 seconds or
    is less than 30 seconds.

  Returns:
    Duration proto string representing the adjusted seconds (multiple of 30
    seconds) value of the provided time_string
  """
  seconds = ConvertIntervalToSeconds(time_string)
  if seconds < 30:
    raise ValueError(
        '{time_string} converted to {seconds}s is less than 30 seconds.'.format(
            time_string=time_string,
            seconds=seconds,
        )
    )
  elif seconds % 30 != 0:
    raise ValueError(
        '{} converted to {}s is not a multiple of 30 seconds.'.format(
            time_string, seconds,
        )
    )
  return _FormatDuration(seconds)


# Regular expressions for matching common Prometheus templating language
# constructs.
_VALUE_VARIABLE_REGEXP = re.compile(r'\{\{ *(humanize )? *\$value *\}\}')
_LABELS_VARIABLE_REGEXP = re.compile(r'\{\{ *(humanize )? *\$labels *\}\}')
_LABELS_KEY_REGEXP = re.compile(
    r'\{\{ *(humanize )? *\$labels\.([a-zA-Z_][a-zA-Z0-9_]*) *\}\}')


def TranslatePromQLTemplateToDocumentVariables(template):
  """Translate Prometheus templating language constructs to document variables.

  TranslatePromQLTemplateToDocumentVariables translates common Prometheus
  templating language constructs to their equivalent Cloud Alerting document
  variables. See:
  https://prometheus.io/docs/prometheus/latest/configuration/template_reference/
  and https://cloud.google.com/monitoring/alerts/doc-variables.

  Only the following constructs will be translated:

  "{{ $value }}" will be translated to "${metric.label.value}".
  "{{ humanize $value }}" will be translated to "${metric.label.value}".
  "{{ $labels.<name> }}" will be translated to
  "${metric_or_resource.label.<name>}".
  "{{ humanize $labels.<name> }}" will be translated to
  "${metric_or_resource.label.<name>}".
  "{{ $labels }}" will be translated to
  "${metric_or_resource.labels}".
  "{{ humanize $labels }}" will be translated to
  "${metric_or_resource.labels}".

  The number of spaces inside the curly braces is immaterial.

  All other Prometheus templating language constructs are not translated.

  Notes:
  1. A document variable reference that does not match a variable
     will be rendered as "(none)".
  2. We do not know whether a {{ $labels.<name> }} construct refers to
     a Cloud Alerting metric or a resource label. Thus we translate it to
     "${metric_or_resource.label.<name>}".
     Note that a reference to a non-existent label will be rendered as "(none)".

  Examples:
  1. "[{{$labels.a}}] VALUE = {{ $value }}" will be translated to
     "[${metric_or_resource.label.a}] VALUE = ${metric.label.value}".

  2. "[{{humanize $labels.a}}] VALUE = {{ humanize $value }}"
     will be translated to
     "[${metric_or_resource.label.a}] VALUE = ${metric.label.value}".

  Args:
    template: String contents of the "subject" or "content" fields of an
    AlertPolicy protoco buffer. The contents of these fields is a template
    which may contain Prometheus templating language constructs.

  Returns:
    The translated template.
  """
  return _LABELS_KEY_REGEXP.sub(
      r'${metric_or_resource.label.\2}',
      _LABELS_VARIABLE_REGEXP.sub(
          r'${metric_or_resource.labels}',
          _VALUE_VARIABLE_REGEXP.sub(
              r'${metric.label.value}', template)))


# A regular expression matching a valid Prometheus label name.
# See: https://prometheus.io/docs/concepts/data_model/#metric-names-and-labels
_VALID_LABEL_REGEXP = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')


def BuildPrometheusCondition(messages, group, rule):
  """Populates Alert Policy conditions translated from a Prometheus alert rule.

  Args:
    messages: Object containing information about all message types allowed.
    group: Information about the parent group of the current rule.
    rule: The current alert rule being translated into an Alert Policy.

  Raises:
    MissingRequiredFieldError: If the provided group/rule is missing an required
    field needed for translation.
    ValueError: If the provided rule name is not a valid Prometheus label name.

  Returns:
     The Alert Policy condition corresponding to the Prometheus group and rule
     provided.
  """
  condition = messages.Condition()
  condition.conditionPrometheusQueryLanguage = (
      messages.PrometheusQueryLanguageCondition()
  )
  if group.get('name') is None:
    raise MissingRequiredFieldError(
        'Missing rule group name in field group.name'
    )
  if rule.get('alert') is None:
    raise MissingRequiredFieldError(
        'Missing alert rule name in field group.rules.alert'
    )
  if _VALID_LABEL_REGEXP.fullmatch(rule.get('alert')) is None:
    raise ValueError(
        'An invalid alert rule name in field group.rules.alert '
        '(not a valid PromQL label name)'
    )
  if rule.get('expr') is None:
    raise MissingRequiredFieldError(
        'Missing a PromQL expression in field groups.rules.expr'
    )
  condition.conditionPrometheusQueryLanguage.ruleGroup = group.get('name')
  condition.displayName = rule.get('alert')
  condition.conditionPrometheusQueryLanguage.alertRule = rule.get('alert')
  condition.conditionPrometheusQueryLanguage.query = rule.get('expr')

  # optional fields
  if rule.get('for') is not None:
    condition.conditionPrometheusQueryLanguage.duration = _FormatDuration(
        ConvertIntervalToSeconds(rule.get('for'))
    )
  if group.get('interval') is not None:
    condition.conditionPrometheusQueryLanguage.evaluationInterval = (
        ConvertPrometheusTimeStringToEvaluationDurationInSeconds(
            group.get('interval')
        )
    )
  if rule.get('labels') is not None:
    condition.conditionPrometheusQueryLanguage.labels = (
        messages.PrometheusQueryLanguageCondition.LabelsValue()
    )
    for k, v in rule.get('labels').items():
      condition.conditionPrometheusQueryLanguage.labels.additionalProperties.append(
          messages.PrometheusQueryLanguageCondition.LabelsValue.AdditionalProperty(
              key=k, value=v
          )
      )

  return condition


def PrometheusMessageFromString(rule_yaml, messages, channels):
  """Populates Alert Policies translated from Prometheus alert rules.

  Args:
    rule_yaml: Opened object of the Prometheus YAML file provided.
    messages: Object containing information about all message types allowed.
    channels: List of Notification Channel names to be added to the translated
      policies.

  Raises:
    YamlOrJsonLoadError: If the YAML file cannot be loaded.

  Returns:
     A list of the Alert Policies corresponding to the Prometheus rules YAML
     file provided.
  """
  try:
    contents = yaml.load(rule_yaml)
    if contents is None:
      raise ValueError('Failed to load YAML file. Is it empty?')

    policies = []
    if contents.get('groups') is None:
      raise ValueError('No groups')

    for group in contents.get('groups'):
      if group.get('rules') is None:
        raise ValueError('No rules in group "%s"' % group.get('name'))

      for rule in group.get('rules'):
        condition = BuildPrometheusCondition(messages, group, rule)
        policy = messages.AlertPolicy()
        policy.conditions.append(condition)
        if rule.get('annotations') is not None:
          policy.documentation = messages.Documentation()
          if rule.get('annotations').get('subject') is not None:
            policy.documentation.subject = (
                TranslatePromQLTemplateToDocumentVariables(
                    rule.get('annotations').get('subject')))
          if rule.get('annotations').get('description') is not None:
            policy.documentation.content = (
                TranslatePromQLTemplateToDocumentVariables(
                    rule.get('annotations').get('description')))
          policy.documentation.mimeType = 'text/markdown'

        if _VALID_LABEL_REGEXP.fullmatch(group.get('name')) is not None:
          # The rule group name is a valid Prometheus label name.
          policy.displayName = '{0}/{1}'.format(
              group.get('name'), rule.get('alert')
          )
        else:
          # The rule group name is NOT a valid Prometheus label name.
          policy.displayName = '"{0}"/{1}'.format(
              group.get('name'), rule.get('alert')
          )

        policy.combiner = arg_utils.ChoiceToEnum(
            'OR', policy.CombinerValueValuesEnum, item_type='combiner'
        )

        if channels is not None:
          policy.notificationChannels = channels

        policies.append(policy)

    return policies
  except Exception as exc:  # pylint: disable=broad-except
    raise YamlOrJsonLoadError('Could not parse YAML: {0}'.format(exc))


def CreateBasePromQLNotificationChannel(channel_name, messages):
  """Helper function for creating a basic Notification Channel translated from a Prometheus alert_manager YAML.

  Args:
    channel_name: The display name of the desired channel.
    messages: Object containing information about all message types allowed.

  Returns:
     A base Notification Channel containing the requested display_name and
     other basic fields.
  """
  channel = messages.NotificationChannel()
  channel.displayName = channel_name
  channel.description = MIGRATED_FROM_PROMETHEUS_TEXT
  channel.labels = messages.NotificationChannel.LabelsValue()
  return channel


def BuildChannelsFromPrometheusReceivers(receiver_config, messages):
  """Populates a Notification Channel translated from Prometheus alert manager.

  Args:
    receiver_config: Object containing information the Prometheus receiver. For
      example receiver_configs, see
      https://github.com/prometheus/alertmanager/blob/main/doc/examples/simple.yml
    messages: Object containing information about all message types allowed.

  Raises:
    MissingRequiredFieldError: If the provided alert manager file contains
    receivers with missing required field(s).

  Returns:
     The Notification Channel corresponding to the Prometheus alert manager
     provided.
  """
  channels = []
  channel_name = receiver_config.get('name')
  if channel_name is None:
    raise MissingRequiredFieldError(
        'Supplied alert manager file contains receiver without a required field'
        ' "name"'
    )

  if receiver_config.get('email_configs') is not None:
    for fields in receiver_config.get('email_configs'):
      if fields.get('to') is not None:
        channel = CreateBasePromQLNotificationChannel(channel_name, messages)
        channel.type = 'email'
        channel.labels.additionalProperties.append(
            messages.NotificationChannel.LabelsValue.AdditionalProperty(
                key='email_address', value=fields.get('to')
            )
        )
        channels.append(channel)

  if receiver_config.get('pagerduty_configs') is not None:
    for fields in receiver_config.get('pagerduty_configs'):
      if fields.get('service_key') is not None:
        channel = CreateBasePromQLNotificationChannel(channel_name, messages)
        channel.type = 'pagerduty'
        channel.labels.additionalProperties.append(
            messages.NotificationChannel.LabelsValue.AdditionalProperty(
                key='service_key', value=fields.get('service_key')
            )
        )
        channels.append(channel)

  if receiver_config.get('webhook_configs') is not None:
    for fields in receiver_config.get('webhook_configs'):
      if fields.get('url') is not None:
        channel = CreateBasePromQLNotificationChannel(channel_name, messages)
        channel.type = 'webhook_tokenauth'
        channel.labels.additionalProperties.append(
            messages.NotificationChannel.LabelsValue.AdditionalProperty(
                key='url', value=fields.get('url')
            )
        )
        channels.append(channel)

  # Tell users that their defined receiver type is not supported by the
  # migration tool and will not be translated.
  # TODO(b/277099361): Have a continue prompt telling users that certain
  # receiver types are not supported.
  supported_receiver_fields = set(
      ['name', 'email_configs', 'pagerduty_configs', 'webhook_configs']
  )
  for field in receiver_config.keys():
    if field not in supported_receiver_fields:
      log.out.Print(
          'Found unsupported receiver type {field}. {name}.{field} will not be'
          ' translated.'.format(field=field, name=receiver_config.get('name'))
      )

  return channels


def NotificationChannelMessageFromString(alert_manager_yaml, messages):
  """Populates Alert Policies translated from Prometheus alert rules.

  Args:
    alert_manager_yaml: Opened object of the Prometheus YAML file provided.
    messages: Object containing information about all message types allowed.

  Raises:
    YamlOrJsonLoadError: If the YAML file cannot be loaded.

  Returns:
     The Alert Policies corresponding to the Prometheus rules YAML file
     provided.
  """
  try:
    contents = yaml.load(alert_manager_yaml)
  except Exception as exc:  # pylint: disable=broad-except
    raise YamlOrJsonLoadError('Could not parse YAML: {0}'.format(exc))

  channels = []
  for receiver_config in contents.get('receivers'):
    channels += BuildChannelsFromPrometheusReceivers(receiver_config, messages)
  return channels


def CreatePromQLPoliciesFromArgs(args, messages, channels=None):
  """Builds a PromQL policies message from args.

  Args:
    args: Flags provided by the user.
    messages: Object containing information about all message types allowed.
    channels: List of full Notification Channel names ("projects/<>/...") to be
      added to the translated policies.

  Returns:
     The Alert Policies corresponding to the Prometheus rules YAML file
     provided. In the case that no file is specified, the default behavior is to
     return an empty list.
  """

  if args.IsSpecified('policies_from_prometheus_alert_rules_yaml'):
    all_rule_yamls = args.policies_from_prometheus_alert_rules_yaml
    policies = []
    for rule_yaml in all_rule_yamls:
      policies += PrometheusMessageFromString(rule_yaml, messages, channels)
  else:
    policies = []

  return policies


def CreateNotificationChannelsFromArgs(args, messages):
  """Builds a notification channel message from args.

  Args:
    args: Flags provided by the user.
    messages: Object containing information about all message types allowed.

  Returns:
     The notification channels corresponding to the Prometheus alert manager
     YAML file provided. In the case that no file is specified, the default
     behavior is to return an empty list.
  """

  if args.IsSpecified('channels_from_prometheus_alertmanager_yaml'):
    alert_manager_yaml = args.channels_from_prometheus_alertmanager_yaml
    channels = NotificationChannelMessageFromString(
        alert_manager_yaml, messages
    )
  else:
    channels = []
  return channels


def ParseUptimeCheck(uptime_check_name, project=None):
  project = project or properties.VALUES.core.project.Get(required=True)
  return resources.REGISTRY.Parse(
      uptime_check_name,
      params={'projectsId': project},
      collection='monitoring.projects.uptimeCheckConfigs',
  )


def ModifyUptimeCheck(
    uptime_check,
    messages,
    args,
    regions,
    user_labels,
    headers,
    status_classes,
    status_codes,
    update=False,
):
  """Modifies an UptimeCheckConfig based on the args and other inputs.

  Args:
    uptime_check: UptimeCheckConfig that is being modified.
    messages: Object containing information about all message types allowed.
    args: Flags provided by the user.
    regions: Potentially updated selected regions.
    user_labels: Potentially updated user labels.
    headers: Potentially updated HTTP headers.
    status_classes: Potentially updated allowed status classes.
    status_codes: Potentially updated allowed status codes.
    update: If this is an update operation (true) or a create operation (false).

  Returns:
     The updated UptimeCheckConfig object.
  """
  if args.display_name is not None:
    uptime_check.displayName = args.display_name
  if args.timeout is not None:
    uptime_check.timeout = str(args.timeout) + 's'
  if args.period is not None:
    period_mapping = {
        '1': '60s',
        '5': '300s',
        '10': '600s',
        '15': '900s',
    }
    uptime_check.period = period_mapping.get(args.period)
  if regions is not None:
    if uptime_check.syntheticMonitor is not None:
      raise calliope_exc.InvalidArgumentException(
          'regions', 'Should not be set or updated for Synthetic Monitor.'
      )
    region_mapping = {
        'usa-oregon': (
            messages.UptimeCheckConfig.SelectedRegionsValueListEntryValuesEnum.USA_OREGON
        ),
        'usa-iowa': (
            messages.UptimeCheckConfig.SelectedRegionsValueListEntryValuesEnum.USA_IOWA
        ),
        'usa-virginia': (
            messages.UptimeCheckConfig.SelectedRegionsValueListEntryValuesEnum.USA_VIRGINIA
        ),
        'europe': (
            messages.UptimeCheckConfig.SelectedRegionsValueListEntryValuesEnum.EUROPE
        ),
        'south-america': (
            messages.UptimeCheckConfig.SelectedRegionsValueListEntryValuesEnum.SOUTH_AMERICA
        ),
        'asia-pacific': (
            messages.UptimeCheckConfig.SelectedRegionsValueListEntryValuesEnum.ASIA_PACIFIC
        ),
    }
    uptime_check.selectedRegions = []
    for region in regions:
      uptime_check.selectedRegions.append(region_mapping.get(region))
    uptime_check.userLabels = user_labels

  SetUptimeCheckMatcherFields(args, messages, uptime_check)
  SetUptimeCheckProtocolFields(
      args,
      messages,
      uptime_check,
      headers,
      status_classes,
      status_codes,
      update,
  )
  return uptime_check


def CreateUptimeFromArgs(args, messages):
  """Builds an Uptime message from args."""
  uptime_base_flags = ['--resource-labels', '--group-id', '--synthetic-target']
  ValidateAtleastOneSpecified(args, uptime_base_flags)

  uptime_check = messages.UptimeCheckConfig()

  if args.IsSpecified('resource_labels'):
    SetUptimeCheckMonitoredResourceFields(args, messages, uptime_check)
  elif args.IsSpecified('group_id'):
    SetUptimeCheckGroupFields(args, messages, uptime_check)
  else:
    SetUptimeCheckSyntheticFields(args, messages, uptime_check)

  user_labels = None
  if args.IsSpecified('user_labels'):
    user_labels = messages.UptimeCheckConfig.UserLabelsValue()
    for k, v in args.user_labels.items():
      user_labels.additionalProperties.append(
          messages.UptimeCheckConfig.UserLabelsValue.AdditionalProperty(
              key=k, value=v
          )
      )
  headers = None
  if args.IsSpecified('headers'):
    headers = messages.HttpCheck.HeadersValue()
    if headers is not None:
      for k, v in args.headers.items():
        headers.additionalProperties.append(
            messages.HttpCheck.HeadersValue.AdditionalProperty(key=k, value=v)
        )
  uptime_check.timeout = '60s'
  uptime_check.period = '60s'

  ModifyUptimeCheck(
      uptime_check,
      messages,
      args,
      regions=args.regions,
      user_labels=user_labels,
      headers=headers,
      status_classes=args.status_classes,
      status_codes=args.status_codes,
  )

  return uptime_check


def SetUptimeCheckMonitoredResourceFields(args, messages, uptime_check):
  """Set Monitored Resource fields based on args."""
  resource_mapping = {
      'uptime-url': 'uptime_url',
      'gce-instance': 'gce_instance',
      'gae-app': 'gae_app',
      'aws-ec2-instance': 'aws_ec2_instance',
      'aws-elb-load-balancer': 'aws_elb_load_balancer',
      'servicedirectory-service': 'servicedirectory_service',
      'cloud-run-revision': 'cloud_run_revision',
      None: 'uptime_url',
  }
  uptime_check.monitoredResource = messages.MonitoredResource()
  uptime_check.monitoredResource.type = resource_mapping.get(args.resource_type)
  uptime_check.monitoredResource.labels = (
      messages.MonitoredResource.LabelsValue()
  )
  for k, v in args.resource_labels.items():
    uptime_check.monitoredResource.labels.additionalProperties.append(
        messages.MonitoredResource.LabelsValue.AdditionalProperty(
            key=k, value=v
        )
    )


def SetUptimeCheckGroupFields(args, messages, uptime_check):
  """Set Group fields based on args."""
  group_mapping = {
      'gce-instance': 'INSTANCE',
      'aws-elb-load-balancer': 'AWS_ELB_LOAD_BALANCER',
      None: 'INSTANCE',
  }
  uptime_check.resourceGroup = messages.ResourceGroup()
  uptime_check.resourceGroup.groupId = args.group_id
  uptime_check.resourceGroup.resourceType = arg_utils.ChoiceToEnum(
      group_mapping.get(args.group_type),
      messages.ResourceGroup.ResourceTypeValueValuesEnum,
      item_type='group type',
  )


def SetUptimeCheckSyntheticFields(args, messages, uptime_check):
  """Set Synthetic Monitor fields based on args."""
  uptime_check.syntheticMonitor = messages.SyntheticMonitorTarget()
  uptime_check.syntheticMonitor.cloudFunctionV2 = (
      messages.CloudFunctionV2Target()
  )
  uptime_check.syntheticMonitor.cloudFunctionV2.name = args.synthetic_target


def SetUptimeCheckMatcherFields(args, messages, uptime_check):
  """Set Matcher fields based on args."""
  if args.IsSpecified('matcher_content'):
    if uptime_check.syntheticMonitor is not None:
      raise calliope_exc.InvalidArgumentException(
          '--matcher_content', 'Should not be set for Synthetic Monitor.'
      )

    content_matcher = messages.ContentMatcher()
    content_matcher.content = args.matcher_content
    matcher_mapping = {
        'contains-string': (
            messages.ContentMatcher.MatcherValueValuesEnum.CONTAINS_STRING
        ),
        'not-contains-string': (
            messages.ContentMatcher.MatcherValueValuesEnum.NOT_CONTAINS_STRING
        ),
        'matches-regex': (
            messages.ContentMatcher.MatcherValueValuesEnum.MATCHES_REGEX
        ),
        'not-matches-regex': (
            messages.ContentMatcher.MatcherValueValuesEnum.NOT_MATCHES_REGEX
        ),
        'matches-json-path': (
            messages.ContentMatcher.MatcherValueValuesEnum.MATCHES_JSON_PATH
        ),
        'not-matches-json-path': (
            messages.ContentMatcher.MatcherValueValuesEnum.NOT_MATCHES_JSON_PATH
        ),
        None: messages.ContentMatcher.MatcherValueValuesEnum.CONTAINS_STRING,
    }
    content_matcher.matcher = matcher_mapping.get(args.matcher_type)
    if args.IsSpecified('json_path'):
      if content_matcher.matcher not in (
          messages.ContentMatcher.MatcherValueValuesEnum.MATCHES_JSON_PATH,
          messages.ContentMatcher.MatcherValueValuesEnum.NOT_MATCHES_JSON_PATH,
      ):
        raise calliope_exc.InvalidArgumentException(
            '--json-path', 'Should only be used with JSON_PATH matcher types.'
        )

      content_matcher.jsonPathMatcher = messages.JsonPathMatcher()
      content_matcher.jsonPathMatcher.jsonPath = args.json_path
      jsonpath_matcher_mapping = {
          'exact-match': (
              messages.JsonPathMatcher.JsonMatcherValueValuesEnum.EXACT_MATCH
          ),
          'regex-match': (
              messages.JsonPathMatcher.JsonMatcherValueValuesEnum.REGEX_MATCH
          ),
          None: messages.JsonPathMatcher.JsonMatcherValueValuesEnum.EXACT_MATCH,
      }
      content_matcher.jsonPathMatcher.jsonMatcher = (
          jsonpath_matcher_mapping.get(args.json_path_matcher_type)
      )
    # Content matcher is always full replace
    uptime_check.contentMatchers = []
    uptime_check.contentMatchers.append(content_matcher)


def SetUptimeCheckProtocolFields(
    args,
    messages,
    uptime_check,
    headers,
    status_classes,
    status_codes,
    update=False,
):
  """Set Protocol fields based on args."""
  if (
      not update and args.IsSpecified('synthetic_target')
  ) or uptime_check.syntheticMonitor is not None:
    # Cannot set HTTP or TCP field for Synthetic Monitor
    should_not_be_set = [
        '--path',
        '--validate-ssl',
        '--mask-headers',
        '--custom-content-type',
        '--username',
        '--password',
        '--body',
        '--request-method',
        '--content-type',
        '--port',
        '--pings-count',
    ]
    for flag in should_not_be_set:
      dest = _FlagToDest(flag)
      if args.IsSpecified(dest):
        raise calliope_exc.InvalidArgumentException(
            flag, 'Should not be set for Synthetic Monitor.'
        )
    if headers:
      raise calliope_exc.InvalidArgumentException(
          'headers', 'Should not be set or updated for Synthetic Monitor.'
      )
    if status_classes:
      raise calliope_exc.InvalidArgumentException(
          'status-classes',
          'Should not be set or updated for Synthetic Monitor.',
      )
    if status_codes:
      raise calliope_exc.InvalidArgumentException(
          'status-codes', 'Should not be set or updated for Synthetic Monitor.'
      )
    return

  if (
      not update and args.protocol == 'tcp'
  ) or uptime_check.tcpCheck is not None:
    if args.port is None and uptime_check.tcpCheck is None:
      raise MissingRequiredFieldError('Missing required field "port"')

    if uptime_check.tcpCheck is None:
      uptime_check.tcpCheck = messages.TcpCheck()
    tcp_check = uptime_check.tcpCheck
    if args.port is not None:
      tcp_check.port = args.port
    if args.pings_count is not None:
      tcp_check.pingConfig = messages.PingConfig()
      tcp_check.pingConfig.pingsCount = args.pings_count
    # Cannot set HTTP field when using TCP protocol
    should_not_be_set = [
        '--path',
        '--validate-ssl',
        '--mask-headers',
        '--custom-content-type',
        '--username',
        '--password',
        '--body',
        '--request-method',
        '--content-type',
    ]
    for flag in should_not_be_set:
      dest = _FlagToDest(flag)
      if args.IsSpecified(dest):
        raise calliope_exc.InvalidArgumentException(
            flag, 'Should not be set for TCP Uptime Check.'
        )
    if headers:
      raise calliope_exc.InvalidArgumentException(
          'headers', 'Should not be set or updated for TCP Uptime Check.'
      )
    if status_classes:
      raise calliope_exc.InvalidArgumentException(
          'status-classes', 'Should not be set or updated for TCP Uptime Check.'
      )
    if status_codes:
      raise calliope_exc.InvalidArgumentException(
          'status-codes', 'Should not be set or updated for TCP Uptime Check.'
      )
  else:
    if uptime_check.httpCheck is None:
      uptime_check.httpCheck = messages.HttpCheck()
    http_check = uptime_check.httpCheck
    if args.path is not None:
      http_check.path = args.path
    if args.validate_ssl is not None:
      http_check.validateSsl = args.validate_ssl
    if args.mask_headers is not None:
      http_check.maskHeaders = args.mask_headers
    if args.custom_content_type is not None:
      http_check.customContentType = args.custom_content_type
    if http_check.authInfo is None:
      http_check.authInfo = messages.BasicAuthentication()
    if args.username is not None:
      http_check.authInfo.username = args.username
    if args.password is not None:
      http_check.authInfo.password = args.password
    if args.pings_count is not None:
      http_check.pingConfig = messages.PingConfig()
      http_check.pingConfig.pingsCount = args.pings_count
    if args.body is not None:
      http_check.body = args.body.encode()
    if (not update and args.protocol == 'https') or http_check.useSsl:
      http_check.useSsl = True
      if args.port is not None:
        http_check.port = args.port
      if http_check.port is None:
        http_check.port = 443
    else:
      http_check.useSsl = False
      if args.port is not None:
        http_check.port = args.port
      if http_check.port is None:
        http_check.port = 80
    method_mapping = {
        'get': messages.HttpCheck.RequestMethodValueValuesEnum.GET,
        'post': messages.HttpCheck.RequestMethodValueValuesEnum.POST,
        None: messages.HttpCheck.RequestMethodValueValuesEnum.GET,
    }
    if http_check.requestMethod is None or args.request_method is not None:
      http_check.requestMethod = method_mapping.get(args.request_method)
    content_mapping = {
        'unspecified': (
            messages.HttpCheck.ContentTypeValueValuesEnum.TYPE_UNSPECIFIED
        ),
        'url-encoded': (
            messages.HttpCheck.ContentTypeValueValuesEnum.URL_ENCODED
        ),
        'user-provided': (
            messages.HttpCheck.ContentTypeValueValuesEnum.USER_PROVIDED
        ),
        None: messages.HttpCheck.ContentTypeValueValuesEnum.TYPE_UNSPECIFIED,
    }
    if http_check.contentType is None or args.content_type is not None:
      http_check.contentType = content_mapping.get(args.content_type)
    http_check.headers = headers
    status_mapping = {
        '1xx': (
            messages.ResponseStatusCode.StatusClassValueValuesEnum.STATUS_CLASS_1XX
        ),
        '2xx': (
            messages.ResponseStatusCode.StatusClassValueValuesEnum.STATUS_CLASS_2XX
        ),
        '3xx': (
            messages.ResponseStatusCode.StatusClassValueValuesEnum.STATUS_CLASS_3XX
        ),
        '4xx': (
            messages.ResponseStatusCode.StatusClassValueValuesEnum.STATUS_CLASS_4XX
        ),
        '5xx': (
            messages.ResponseStatusCode.StatusClassValueValuesEnum.STATUS_CLASS_5XX
        ),
        'any': (
            messages.ResponseStatusCode.StatusClassValueValuesEnum.STATUS_CLASS_ANY
        ),
        None: (
            messages.ResponseStatusCode.StatusClassValueValuesEnum.STATUS_CLASS_UNSPECIFIED
        ),
    }
    if status_classes is not None:
      http_check.acceptedResponseStatusCodes = []
      for status in status_classes:
        http_check.acceptedResponseStatusCodes.append(
            messages.ResponseStatusCode(statusClass=status_mapping.get(status))
        )
    elif status_codes is not None:
      http_check.acceptedResponseStatusCodes = []
      for status in status_codes:
        http_check.acceptedResponseStatusCodes.append(
            messages.ResponseStatusCode(statusValue=status)
        )
    elif http_check.acceptedResponseStatusCodes is None:
      http_check.acceptedResponseStatusCodes = []
      http_check.acceptedResponseStatusCodes.append(
          messages.ResponseStatusCode(statusClass=status_mapping.get('2xx'))
      )

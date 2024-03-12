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
"""Shared resource flags for Cloud Monitoring commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.monitoring import completers
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import repeated
from googlecloudsdk.core.util import times


COMPARISON_TO_ENUM = {
    '>': 'COMPARISON_GT',
    '<': 'COMPARISON_LT',
    '>=': 'COMPARISON_GE',
    '<=': 'COMPARISON_LE',
    '==': 'COMPARISON_EQ',
    '=': 'COMPARISON_EQ',
    '!=': 'COMPARISON_NE',
}

UPTIME_MONITORED_RESOURCES = {
    'uptime-url': 'Uptime check against a URL.',
    'gce-instance': 'Uptime check against a Compute Engine instance.',
    'gae-app': 'Uptime check against an App Engine module.',
    'aws-ec2-instance': 'Uptime check against an AWS EC2 instance.',
    'aws-elb-load-balancer': 'Uptime check against an ElasticLoadBalancer.',
    'servicedirectory-service': (
        'Uptime check against a Service Directory service.'
    ),
    'cloud-run-revision': 'Uptime check against a Cloud Run revision.',
}

UPTIME_GROUP_RESOURCES = {
    'gce-instance': (
        'Uptime check against a group of instances from Google Cloud'
        ' or Amazon Web Services.'
    ),
    'aws-elb-load-balancer': (
        'Uptime check against a group of Amazon ELB load balancers.'
    ),
}

UPTIME_PROTOCOLS = {
    'http': 'An HTTP check.',
    'https': 'An HTTPS check.',
    'tcp': 'A TCP check.',
}

UPTIME_REQUEST_METHODS = {
    'get': 'HTTP GET method',
    'post': 'HTTP POST method',
}

UPTIME_CONTENT_TYPES = {
    'unspecified': 'Not specified',
    'url-encoded': 'URL encoded',
    'user-provided': 'User provided',
}

UPTIME_STATUS_CLASSES = {
    '1xx': 'Any response code from 100-199 inclusive',
    '2xx': 'Any response code from 200-299 inclusive',
    '3xx': 'Any response code from 300-399 inclusive',
    '4xx': 'Any response code from 400-499 inclusive',
    '5xx': 'Any response code from 500-599 inclusive',
    'any': 'Any response code',
}

UPTIME_PERIODS = {
    '1': 'One minute',
    '5': 'Five minutes',
    '10': 'Ten minutes',
    '15': 'Fifteen minutes',
}

UPTIME_REGIONS = {
    'usa-oregon': 'us-west1',
    'usa-virginia': 'us-east4',
    'usa-iowa': 'us-central1',
    'europe': 'europe-west1',
    'south-america': 'southamerica-east1',
    'asia-pacific': 'asia-southeast1',
}

UPTIME_MATCHER_TYPES = {
    'contains-string': 'Response contains string',
    'not-contains-string': 'Response does not contain string',
    'matches-regex': 'Response matches regex',
    'not-matches-regex': 'Response does not match regex',
    'matches-json-path': 'Response matches at JSONPath',
    'not-matches-json-path': 'Response does not match at JSONPath',
}

UPTIME_JSON_MATCHER_TYPES = {
    'exact-match': 'Response matches exact string at JSONPath',
    'regex-match': 'Response matches regex at JSONPath',
}


def AddFileMessageFlag(parser, resource, flag=None):
  """Adds flags for specifying a message as a file to the parser."""
  parser.add_argument(
      '--{}-from-file'.format(flag or resource),
      type=arg_parsers.FileContents(),
      help='The path to a JSON or YAML file containing the {}.'.format(
          resource))


def AddMessageFlags(parser, resource, flag=None):
  """Adds flags for specifying a message as a string/file to the parser."""
  message_group = parser.add_group(mutex=True)
  message_group.add_argument(
      '--{}'.format(flag or resource),
      help='The {} as a string. In either JSON or YAML format.'.format(
          resource))
  message_group.add_argument(
      '--{}-from-file'.format(flag or resource),
      type=arg_parsers.FileContents(),
      help='The path to a JSON or YAML file containing the {}.'.format(
          resource))


def AddDisplayNameFlag(parser, resource, positional=False):
  if positional:
    base.Argument(
        'display_name',
        metavar='DISPLAY_NAME',
        help='Display name for the uptime check or synthetic monitor.',
    ).AddToParser(parser)
  else:
    parser.add_argument(
        '--display-name', help='The display name for the {}.'.format(resource)
    )


def AddCombinerFlag(parser, resource):
  """Adds flags for specifying a combiner, which defines how to combine the results of multiple conditions."""
  parser.add_argument(
      '--combiner',
      choices={
          'COMBINE_UNSPECIFIED': 'An unspecified combiner',
          'AND': 'An incident is created only if '
                 'all conditions are met simultaneously. '
                 'This combiner is satisfied if all conditions are met, '
                 'even if they are met on completely different resources.',
          'OR': 'An incident is created if '
                'any of the listed conditions is met.',
          'AND_WITH_MATCHING_RESOURCE': 'Combine conditions using '
                                        'logical AND operator, '
                                        'but unlike the regular AND option, '
                                        'an incident is created '
                                        'only if all conditions '
                                        'are met simultaneously '
                                        'on at least one resource.',
      },
      help='The combiner for the {}.'.format(resource))


def AddPolicySettingsFlags(parser, update=False):
  """Adds policy settings flags to the parser."""
  policy_settings_group = parser.add_group(help="""\
      Policy Settings.
      If any of these are specified, they will overwrite fields in the
      `--policy` or `--policy-from-file` flags if specified.""")
  AddDisplayNameFlag(policy_settings_group, resource='Alert Policy')
  AddCombinerFlag(policy_settings_group, resource='Alert Policy')
  enabled_kwargs = {
      'action': arg_parsers.StoreTrueFalseAction if update else 'store_true'
  }
  if not update:
    # Can't specify default if using StoreTrueFalseAction.
    enabled_kwargs['default'] = True
  policy_settings_group.add_argument(
      '--enabled', help='If the policy is enabled.', **enabled_kwargs)

  documentation_group = policy_settings_group.add_group(help='Documentation')
  documentation_group.add_argument(
      '--documentation-format',
      default='text/markdown' if not update else None,
      help='The MIME type that should be used with `--documentation` or '
           '`--documentation-from-file`. Currently, only "text/markdown" is '
           'supported.')
  documentation_string_group = documentation_group.add_group(mutex=True)
  documentation_string_group.add_argument(
      '--documentation',
      help='The documentation to be included with the policy.')
  documentation_string_group.add_argument(
      '--documentation-from-file',
      type=arg_parsers.FileContents(),
      help='The path to a file containing the documentation to be included '
           'with the policy.')
  if update:
    repeated.AddPrimitiveArgs(
        policy_settings_group,
        'Alert Policy',
        'notification-channels',
        'Notification Channels')
    AddUpdateLabelsFlags(
        'user-labels', policy_settings_group, group_text='User Labels')
  else:
    AddCreateLabelsFlag(policy_settings_group, 'user-labels', 'policy')


def AddFieldsFlagsWithMutuallyExclusiveSettings(parser,
                                                fields_help,
                                                add_settings_func,
                                                fields_choices=None,
                                                **kwargs):
  """Adds fields flags with mutually excludisve settings."""
  update_group = parser.add_group(mutex=True)
  update_group.add_argument(
      '--fields',
      metavar='field',
      type=arg_parsers.ArgList(choices=fields_choices),
      help=fields_help)
  add_settings_func(update_group, **kwargs)


def ValidateAlertPolicyUpdateArgs(args):
  """Validate alert policy update args."""
  if args.fields and not (args.policy or args.policy_from_file):
    raise exceptions.OneOfArgumentsRequiredException(
        ['--policy', '--policy-from-file'],
        'If --fields is specified.')


def ComparisonValidator(if_value):
  """Validates and returns the comparator and value."""
  if if_value.lower() == 'absent':
    return (None, None)
  if len(if_value) < 2:
    raise exceptions.BadArgumentException('--if', 'Invalid value for flag.')
  comparator_part = if_value[0]
  threshold_part = if_value[1:]
  try:
    comparator = COMPARISON_TO_ENUM[comparator_part]
    threshold_value = float(threshold_part)

    # currently only < and > are supported
    if comparator not in ['COMPARISON_LT', 'COMPARISON_GT']:
      raise exceptions.BadArgumentException('--if',
                                            'Comparator must be < or >.')
    return comparator, threshold_value
  except KeyError:
    raise exceptions.BadArgumentException('--if',
                                          'Comparator must be < or >.')
  except ValueError:
    raise exceptions.BadArgumentException('--if',
                                          'Threshold not a value float.')


def AddConditionSettingsFlags(parser):
  """Adds policy condition flags to the parser."""
  condition_group = parser.add_group(help="""\
        Condition Settings.
        This will add a condition to the created policy. If any conditions are
        already specified, this condition will be appended.""")
  condition_group.add_argument(
      '--condition-display-name',
      help='The display name for the condition.')
  condition_group.add_argument(
      '--condition-filter',
      help='Specifies the "filter" in a metric absence or metric threshold '
           'condition.')
  condition_group.add_argument(
      '--aggregation',
      help='Specifies an Aggregation message as a JSON/YAML value to be '
           'applied to the condition. For more information about the format: '
           'https://cloud.google.com/monitoring/api/ref_v3/rest/v3/'
           'projects.alertPolicies')
  condition_group.add_argument(
      '--duration',
      type=arg_parsers.Duration(),
      help='The duration (e.g. "60s", "2min", etc.) that the condition '
           'must hold in order to trigger as true.')
  AddUpdateableConditionFlags(condition_group)


def AddUpdateableConditionFlags(parser):
  """Adds flags for condition settings that are updateable to the parser."""
  parser.add_argument(
      '--if',
      dest='if_value',  # To avoid specifying args.if.
      type=ComparisonValidator,
      help='One of "absent", "< THRESHOLD", "> THRESHOLD" where "THRESHOLD" is '
           'an integer or float.')
  trigger_group = parser.add_group(mutex=True)
  trigger_group.add_argument(
      '--trigger-count',
      type=int,
      help='The absolute number of time series that must fail the predicate '
           'for the condition to be triggered.')
  trigger_group.add_argument(
      '--trigger-percent',
      type=float,
      help='The percentage of time series that must fail the predicate for '
           'the condition to be triggered.')


def ValidateNotificationChannelUpdateArgs(args):
  """Validate notification channel update args."""
  if (args.fields and
      not (args.channel_content or args.channel_content_from_file)):
    raise exceptions.OneOfArgumentsRequiredException(
        ['--channel-content', '--channel-content-from-file'],
        'If --fields is specified.')


def AddNotificationChannelSettingFlags(parser, update=False):
  """Adds flags for channel settings to the parser."""
  channel_group = parser.add_group(help='Notification channel settings')
  AddDisplayNameFlag(channel_group, 'channel')
  channel_group.add_argument(
      '--description',
      help='An optional description for the channel.')
  channel_group.add_argument(
      '--type',
      help='The type of the notification channel. This field matches the '
           'value of the NotificationChannelDescriptor type field.')

  enabled_kwargs = {
      'action': arg_parsers.StoreTrueFalseAction if update else 'store_true'
  }
  if not update:
    # Can't specify default if using StoreTrueFalseAction.
    enabled_kwargs['default'] = True
  channel_group.add_argument(
      '--enabled',
      help='Whether notifications are forwarded to the described channel.',
      **enabled_kwargs)
  if update:
    AddUpdateLabelsFlags(
        'user-labels', channel_group, group_text='User Labels')
    AddUpdateLabelsFlags(
        'channel-labels', channel_group, validate_values=False,
        group_text='Configuration Fields: Key-Value pairs that define the '
                   'channel and its behavior.')
  else:
    AddCreateLabelsFlag(channel_group, 'user-labels', 'channel')
    AddCreateLabelsFlag(
        channel_group, 'channel-labels', 'channel', validate_values=False,
        extra_message='These are configuration fields that define the channel '
                      'and its behavior.')


def AddCreateLabelsFlag(parser, labels_name, resource_name, extra_message='',
                        validate_values=True, skip_extra_message=False):
  """Add create labels flags."""
  if not skip_extra_message:
    extra_message += ('If the {0} was given as a JSON/YAML object from a '
                      'string or file, this flag will replace the labels value '
                      'in the given {0}.'.format(resource_name))
  labels_util.GetCreateLabelsFlag(
      extra_message=extra_message,
      labels_name=labels_name,
      validate_values=validate_values).AddToParser(parser)


def AddUpdateLabelsFlags(labels_name, parser, group_text='',
                         validate_values=True):
  """Add update labels flags."""
  labels_group = parser.add_group(group_text)
  labels_util.GetUpdateLabelsFlag(
      '', labels_name=labels_name,
      validate_values=validate_values).AddToParser(labels_group)
  remove_group = labels_group.add_group(mutex=True)
  labels_util.GetRemoveLabelsFlag(
      '', labels_name=labels_name).AddToParser(remove_group)
  labels_util.GetClearLabelsFlag(
      labels_name=labels_name).AddToParser(remove_group)


def GetMonitoredResourceContainerNameFlag(verb):
  """Flag for managing a monitored resource container."""
  return base.Argument(
      'monitored_resource_container_name',
      metavar='MONITORED_RESOURCE_CONTAINER_NAME',
      completer=completers.MonitoredResourceContainerCompleter,
      help=(
          'Monitored resource container (example - projects/PROJECT_ID) project'
          ' you want to {0}.'.format(verb)
      ),
  )


def AddCriteriaPoliciesFlag(parser, resource):
  parser.add_argument(
      '--criteria-policies',
      metavar='CRITERIA_POLICIES',
      type=arg_parsers.ArgList(min_length=1, max_length=16),
      help='The policies that the {} applies to.'.format(resource))


def AddStartTimeFlag(parser, resource):
  parser.add_argument(
      '--start-time',
      type=arg_parsers.Datetime.Parse,
      help='The start time for the {}.'.format(resource))


def AddEndTimeFlag(parser, resource):
  parser.add_argument(
      '--end-time',
      type=arg_parsers.Datetime.Parse,
      help='The start time for the {}.'.format(resource))


def AddSnoozeSettingsFlags(parser, update=False):
  """Adds snooze settings flags to the parser."""
  snooze_settings_group = parser.add_group(help="""\
      Snooze Settings.
      If any of these are specified, they will overwrite fields in the
      `--snooze-from-file` flags if specified.""")
  AddDisplayNameFlag(snooze_settings_group, resource='Snooze')
  if not update:
    AddCriteriaPoliciesFlag(snooze_settings_group, resource='Snooze')
  AddStartTimeFlag(snooze_settings_group, resource='Snooze')
  AddEndTimeFlag(snooze_settings_group, resource='Snooze')


def AddUptimeSettingsFlags(parser, update=False):
  """Adds uptime check settings flags to the parser."""
  if not update:
    AddUptimeResourceFlags(parser)

  AddUptimeProtocolFlags(parser, update)
  AddUptimeRunFlags(parser, update)
  AddUptimeMatcherFlags(parser)


def AddUptimeResourceFlags(parser):
  """Adds uptime check resource settings flags to the parser."""
  uptime_resource_group = parser.add_group(
      help='Uptime check resource.',
      mutex=True,
      required=True,
  )
  monitored_resource_group = uptime_resource_group.add_group(
      help='Monitored resource'
  )
  monitored_resource_group.add_argument(
      '--resource-type',
      help='Type of monitored resource, defaults to `uptime-url`.',
      choices=UPTIME_MONITORED_RESOURCES,
  )
  base.Argument(
      '--resource-labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(key_type=str, value_type=str),
      action=arg_parsers.UpdateAction,
      required=True,
      help=(
          """Values for all of the labels listed in the associated monitored resource descriptor.
            See https://cloud.google.com/monitoring/api/resources for more information and allowed
            keys."""
      ),
  ).AddToParser(monitored_resource_group)
  group_resource_group = uptime_resource_group.add_group(
      help='Monitored resource group'
  )
  group_resource_group.add_argument(
      '--group-type',
      help=(
          'The resource type of the group members, defaults to `gce-instance`.'
      ),
      choices=UPTIME_GROUP_RESOURCES,
  )
  group_resource_group.add_argument(
      '--group-id',
      help='The group of resources being monitored.',
      required=True,
      type=str,
  )
  uptime_resource_group.add_argument(
      '--synthetic-target',
      help="""The target of the Synthetic Monitor.
        This is the fully qualified GCFv2 resource name.
        """,
      type=str,
  )


def AddUptimeProtocolFlags(parser, update=False):
  """Adds uptime check protocol settings flags to the parser."""
  uptime_protocol_group = parser.add_group(
      help='Uptime check protocol settings.'
  )
  if not update:
    uptime_protocol_group.add_argument(
        '--protocol',
        help='The protocol of the request, defaults to `http`.',
        choices=UPTIME_PROTOCOLS,
    )
  uptime_protocol_group.add_argument(
      '--port',
      help="""The port on the server against which to run the check.
        Defaults to `80` when `--protocol` is `http`.
        Defaults to `443` when `--protocol` is `https`.
        Required if `--protocol` is `tcp`.""",
      type=arg_parsers.BoundedInt(lower_bound=1, upper_bound=65535),
  )
  uptime_protocol_group.add_argument(
      '--pings-count',
      help='Number of ICMP pings to send alongside the request.',
      type=arg_parsers.BoundedInt(lower_bound=1, upper_bound=3),
  )
  uptime_protocol_group.add_argument(
      '--request-method',
      help="""The HTTP request method to use, defaults to `get`.
        Can only be set if `--protocol` is `http` or `https`.""",
      choices=UPTIME_REQUEST_METHODS,
  )
  uptime_protocol_group.add_argument(
      '--path',
      help="""The path to the page against which to run the check, defaults to `/`.
        Can only be set if `--protocol` is `http` or `https`.""",
      type=str,
  )
  uptime_protocol_group.add_argument(
      '--username',
      help="""The username to use when authenticating with the HTTP server.
        Can only be set if `--protocol` is `http` or `https`.""",
      type=str,
  )
  uptime_protocol_group.add_argument(
      '--password',
      help="""The password to use when authenticating with the HTTP server.
        Can only be set if `--protocol` is `http` or `https`.""",
      type=str,
  )
  uptime_protocol_group.add_argument(
      '--mask-headers',
      help="""Whether to encrypt the header information, defaults to `false`.
        Can only be set if `--protocol` is `http` or `https`.""",
      type=bool,
  )
  if update:
    uptime_headers_group = uptime_protocol_group.add_group(
        help='Uptime check headers.'
    )
    base.Argument(
        '--update-headers',
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(key_type=str, value_type=str),
        action=arg_parsers.UpdateAction,
        help=("""The list of headers to add to the uptime check. Any existing
              headers with matching "key" are overridden by the provided
              values."""),
    ).AddToParser(uptime_headers_group)
    uptime_remove_header_group = uptime_headers_group.add_group(
        help='Uptime check remove headers.',
        mutex=True,
    )
    uptime_remove_header_group.add_argument(
        '--remove-headers',
        metavar='KEY',
        help="""The list of header keys to remove from the uptime check.""",
        type=arg_parsers.ArgList(str),
    )
    uptime_remove_header_group.add_argument(
        '--clear-headers',
        help="""Clear all headers on the uptime check.""",
        type=bool,
    )
  else:
    base.Argument(
        '--headers',
        metavar='KEY=VALUE',
        type=arg_parsers.ArgDict(key_type=str, value_type=str),
        action=arg_parsers.UpdateAction,
        help=(
            """The list of headers to send as part of the uptime check
              request. Can only be set if `--protocol` is `http` or `https`."""
        ),
    ).AddToParser(uptime_protocol_group)
  uptime_protocol_group.add_argument(
      '--content-type',
      help="""The content type header to use for the check, defaults to `unspecified`.
        Can only be set if `--protocol` is `http` or `https`.""",
      choices=UPTIME_CONTENT_TYPES,
  )
  uptime_protocol_group.add_argument(
      '--custom-content-type',
      help="""A user-provided content type header to use for the check.
        Can only be set if `--protocol` is `http` or `https`.""",
      type=str,
  )
  uptime_protocol_group.add_argument(
      '--validate-ssl',
      help="""Whether to include SSL certificate validation as a part of the uptime check,
        defaults to `false`.
        Can only be set if `--protocol` is `http` or `https`.""",
      type=bool,
  )
  uptime_protocol_group.add_argument(
      '--body',
      help="""The request body associated with the HTTP POST request.
        Can only be set if `--protocol` is `http` or `https`.""",
      type=str,
  )
  uptime_status_group = uptime_protocol_group.add_group(
      help='Uptime check status.',
      mutex=True,
  )
  if update:
    uptime_status_classes_group = uptime_status_group.add_group(
        help='Uptime check status classes.',
        mutex=True,
    )
    uptime_status_classes_group.add_argument(
        '--set-status-classes',
        metavar='status-class',
        help="""List of HTTP status classes. The uptime check will only pass if the response
                code is contained in this list.""",
        type=arg_parsers.ArgList(choices=UPTIME_STATUS_CLASSES),
    )
    uptime_status_classes_group.add_argument(
        '--add-status-classes',
        metavar='status-class',
        help="""The list of HTTP status classes to add to the uptime check.""",
        type=arg_parsers.ArgList(choices=UPTIME_STATUS_CLASSES),
    )
    uptime_status_classes_group.add_argument(
        '--remove-status-classes',
        metavar='status-class',
        help="""The list of HTTP status classes to remove from the uptime check.""",
        type=arg_parsers.ArgList(choices=UPTIME_STATUS_CLASSES),
    )
    uptime_status_classes_group.add_argument(
        '--clear-status-classes',
        help="""Clear all HTTP status classes on the uptime check. Setting this
            flag is the same as selecting only the `2xx` status class.""",
        type=bool,
    )
    uptime_status_codes_group = uptime_status_group.add_group(
        help='Uptime check status codes.',
        mutex=True,
    )
    uptime_status_codes_group.add_argument(
        '--set-status-codes',
        metavar='status-code',
        help="""List of HTTP status codes. The uptime check will only pass if the response
                code is present in this list.""",
        type=arg_parsers.ArgList(int),
    )
    uptime_status_codes_group.add_argument(
        '--add-status-codes',
        metavar='status-code',
        help="""The list of HTTP status codes to add to the uptime check.""",
        type=arg_parsers.ArgList(int),
    )
    uptime_status_codes_group.add_argument(
        '--remove-status-codes',
        metavar='status-code',
        help="""The list of HTTP status codes to remove from the uptime check.""",
        type=arg_parsers.ArgList(int),
    )
    uptime_status_codes_group.add_argument(
        '--clear-status-codes',
        help="""Clear all HTTP status codes on the uptime check. Setting this
            flag is the same as selecting only the `2xx` status class.""",
        type=bool,
    )
  else:
    uptime_status_group.add_argument(
        '--status-classes',
        metavar='status-class',
        help="""List of HTTP status classes. The uptime check only passes when the response
              code is contained in this list. Defaults to `2xx`.
              Can only be set if `--protocol` is `http` or `https`.""",
        type=arg_parsers.ArgList(choices=UPTIME_STATUS_CLASSES),
    )
    uptime_status_group.add_argument(
        '--status-codes',
        metavar='status-code',
        help="""List of HTTP Status Codes. The uptime check will only pass if the response code
              is present in this list.
              Can only be set if `--protocol` is `http` or `https`.""",
        type=arg_parsers.ArgList(int),
    )


def AddUptimeRunFlags(parser, update=False):
  """Adds uptime check run flags to the parser."""
  uptime_settings_group = parser.add_group(help='Settings.')
  uptime_settings_group.add_argument(
      '--period',
      help='''The time between uptime check or synthetic monitor executions in
              minutes, defaults to `1`. Can be set for synthetic monitors.''',
      choices=UPTIME_PERIODS,
  )
  uptime_settings_group.add_argument(
      '--timeout',
      help=(
          'The maximum amount of time in seconds to wait for the request to'
          ' complete, defaults to `60`. Can be set for synthetic monitors.'
      ),
      type=arg_parsers.BoundedInt(lower_bound=1, upper_bound=60),
  )
  if update:
    AddDisplayNameFlag(
        uptime_settings_group,
        resource='uptime check or synthetic monitor',
        positional=False,
    )
    uptime_regions_group = uptime_settings_group.add_group(
        help="""Uptime check selected regions.""",
        mutex=True,
    )
    uptime_regions_group.add_argument(
        '--set-regions',
        metavar='region',
        help="""The list of regions from which the check is run. At least 3 regions must be
            selected.""",
        type=arg_parsers.ArgList(choices=UPTIME_REGIONS),
    )
    uptime_regions_group.add_argument(
        '--add-regions',
        metavar='region',
        help="""The list of regions to add to the uptime check.""",
        type=arg_parsers.ArgList(choices=UPTIME_REGIONS),
    )
    uptime_regions_group.add_argument(
        '--remove-regions',
        metavar='region',
        help="""The list of regions to remove from the uptime check.""",
        type=arg_parsers.ArgList(choices=UPTIME_REGIONS),
    )
    uptime_regions_group.add_argument(
        '--clear-regions',
        help="""Clear all regions on the uptime check. This setting acts the same as if all available
            regions were selected.""",
        type=bool,
    )
  else:
    uptime_settings_group.add_argument(
        '--regions',
        metavar='field',
        help="""The list of regions from which the check is run. At least 3 regions must be selected.
            Defaults to all available regions.""",
        type=arg_parsers.ArgList(choices=UPTIME_REGIONS),
    )
  if update:
    AddUpdateLabelsFlags(
        'user-labels',
        uptime_settings_group,
        'User labels. Can be set for synthetic monitors.',
    )
  else:
    AddCreateLabelsFlag(
        uptime_settings_group,
        'user-labels',
        'User labels. Can be set for synthetic monitors.',
        skip_extra_message=True,
    )


def AddUptimeMatcherFlags(parser):
  """Adds uptime check matcher flags to the parser."""
  uptime_matcher_group = parser.add_group(help='Uptime check matcher settings.')
  uptime_matcher_group.add_argument(
      '--matcher-content',
      required=True,
      type=str,
      help='String, regex or JSON content to match.',
  )
  uptime_matcher_group.add_argument(
      '--matcher-type',
      choices=UPTIME_MATCHER_TYPES,
      help="""The type of content matcher that is applied to the server output, defaults to
        `contains-string`.""",
  )
  uptime_json_matcher_group = uptime_matcher_group.add_group(
      help='Uptime check matcher settings for JSON responses.'
  )
  uptime_json_matcher_group.add_argument(
      '--json-path',
      type=str,
      required=True,
      help="""JSONPath within the response output pointing to the expected content to match.
            Only used if `--matcher-type` is `matches-json-path` or `not-matches-json-path`.""",
  )
  uptime_json_matcher_group.add_argument(
      '--json-path-matcher-type',
      choices=UPTIME_JSON_MATCHER_TYPES,
      help="""The type of JSONPath match that is applied to the JSON output, defaults to
            `exact-match`.
            Only used if `--matcher-type` is `matches-json-path` or `not-matches-json-path`.""",
  )


def ValidateSnoozeUpdateArgs(args):
  """Validate snooze update args."""
  if args.fields and not args.snooze_from_file:
    raise exceptions.OneOfArgumentsRequiredException(
        ['--snooze-from-file'], 'If --fields is specified.'
    )


def ValidateSnoozeInterval(
    snooze,
    display_name=None,
    start_time=None,
    end_time=None,
):
  """Validate snooze reference interval."""
  snooze_past = False
  end_time_ref = times.ParseDateTime(snooze.interval.endTime)
  if end_time_ref < times.Now():
    snooze_past = True

  if snooze_past:
    if display_name is not None:
      raise exceptions.InvalidArgumentException(
          '--display-name',
          'Expired snoozes can no longer be updated.',
      )
    elif start_time is not None:
      raise exceptions.InvalidArgumentException(
          '--start-time',
          'Expired snoozes can no longer be updated.',
      )
    elif end_time is not None:
      raise exceptions.InvalidArgumentException(
          '--end-time',
          'Expired snoozes can no longer be updated.',
      )


def AddMigrateFlags(parser):
  """Adds migrate flags to the parser."""
  migrate_group = parser.add_group()
  migrate_group.add_argument(
      '--policies-from-prometheus-alert-rules-yaml',
      metavar='PROMETHEUS_ALERT_RULE_FILE_PATHS',
      type=arg_parsers.ArgList(arg_parsers.FileContents()),
      help=(
          'One or more Prometheus alert rule YAML files (separated by commas if'
          ' multiple) to be converted to Cloud Alerting Policies. Example: '
          '--policies-from-prometheus-alert-rules-yaml=rules_1.yaml,rules_2.yaml'
      ),
  )
  migrate_group.add_argument(
      '--channels-from-prometheus-alertmanager-yaml',
      metavar='PROMETHEUS_ALERT_MANAGER_FILE_PATH',
      type=arg_parsers.FileContents(),
      help=(
          'Prometheus alert manager YAML file to be converted to Cloud'
          ' Monitoring notification channels. Specifying this flag with the'
          ' --policies-from-prometheus-alert-rules-yaml flag puts the newly'
          " created notification channels into the translated Alert Policies'"
          ' definition.'
      ),
  )

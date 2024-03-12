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

"""Flags for the compute resource-policies commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util


def MakeResourcePolicyArg():
  return compute_flags.ResourceArgument(
      resource_name='resource policy',
      regional_collection='compute.resourcePolicies',
      region_explanation=compute_flags.REGION_PROPERTY_EXPLANATION)


def AddMaintenanceParentGroup(parser):
  return parser.add_argument_group('Maintenance configuration.',
                                   required=True,
                                   mutex=True)


def AddConcurrentControlGroupArgs(parent_group):
  concurrent_group = parent_group.add_argument_group("""\
  Concurrent Maintenance Controls Group. Defines a group config that, when
  attached to an instance, recognizes that instance as a part of a group of
  instances where only up the configured amount of instances in that group can
  undergo simultaneous maintenance.
  """)
  concurrent_group.add_argument('--concurrency-limit-percent', type=int,
                                help="""\
  Defines the max percentage of instances in a concurrency group that go to
  maintenance simultaneously. Value must be greater or equal to 1 and less or
  equal to 100.
  Usage examples:
  `--concurrency-limit=1` sets to 1%.
  `--concurrency-limit=55` sets to 55%.""")


def AddCycleFrequencyArgs(parser,
                          flag_suffix,
                          start_time_help,
                          cadence_help,
                          supports_hourly=False,
                          has_restricted_start_times=False,
                          supports_weekly=False,
                          required=True):
  """Add Cycle Frequency args for Resource Policies."""
  freq_group = parser.add_argument_group(
      'Cycle Frequency Group.', required=required, mutex=True)
  if has_restricted_start_times:
    start_time_help += """\
        Valid choices are 00:00, 04:00, 08:00, 12:00,
        16:00 and 20:00 UTC. For example, `--start-time="08:00"`."""
  freq_flags_group = freq_group.add_group(
      'Using command flags:' if supports_weekly else '')
  freq_flags_group.add_argument(
      '--start-time', required=True,
      type=arg_parsers.Datetime.ParseUtcTime,
      help=start_time_help)
  cadence_group = freq_flags_group.add_group(mutex=True, required=True)
  cadence_group.add_argument(
      '--daily-{}'.format(flag_suffix),
      dest='daily_cycle',
      action='store_true',
      help='{} starts daily at START_TIME.'.format(cadence_help))

  if supports_hourly:
    cadence_group.add_argument(
        '--hourly-{}'.format(flag_suffix),
        metavar='HOURS',
        dest='hourly_cycle',
        type=arg_parsers.BoundedInt(lower_bound=1),
        help='{} occurs every n hours starting at START_TIME.'.format(
            cadence_help))

  if supports_weekly:
    base.ChoiceArgument(
        '--weekly-{}'.format(flag_suffix),
        dest='weekly_cycle',
        choices=['monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                 'saturday', 'sunday'],
        help_str='{} occurs weekly on WEEKLY_{} at START_TIME.'.format(
            cadence_help, flag_suffix.upper())).AddToParser(cadence_group)
    freq_file_group = freq_group.add_group('Using a file:')
    freq_file_group.add_argument(
        '--weekly-{}-from-file'.format(flag_suffix),
        dest='weekly_cycle_from_file',
        type=arg_parsers.FileContents(),
        help="""\
        A JSON/YAML file which specifies a weekly schedule. The file should
        contain the following fields:

        day: Day of the week with the same choices as `--weekly-{}`.
        startTime: Start time of the snapshot schedule with
        the same format as --start-time.

        For more information about using a file,
        see https://cloud.google.com/compute/docs/disks/scheduled-snapshots#create_snapshot_schedule
        """.format(flag_suffix))


def AddMaxPercentArg(parser):
  parser.add_argument(
      '--max-percent',
      help='Sets maximum percentage of instances in the group that can '
           'undergo simultaneous maintenance. If this flag is not specified '
           'default value of 1% will be set. Usage example: `--max-percent=10` '
           'sets to 10%.',
      type=arg_parsers.BoundedInt(lower_bound=1, upper_bound=100),
      default=1
  )


def AddCommonArgs(parser):
  parser.add_argument(
      '--description',
      help='An optional, textual description for the backend.')


def GetOnSourceDiskDeleteFlagMapper(messages):
  return arg_utils.ChoiceEnumMapper(
      '--on-source-disk-delete',
      messages.ResourcePolicySnapshotSchedulePolicyRetentionPolicy
      .OnSourceDiskDeleteValueValuesEnum,
      custom_mappings={
          'KEEP_AUTO_SNAPSHOTS': (
              'keep-auto-snapshots',
              'Keep automatically-created snapshots when the source disk is '
              'deleted. This is the default behavior.'),
          'APPLY_RETENTION_POLICY': (
              'apply-retention-policy',
              'Continue to apply the retention window to automatically-created '
              'snapshots when the source disk is deleted.')
      },
      default=None,
      help_str='Retention behavior of automatic snapshots in the event of '
      'source disk deletion.')


def AddSnapshotScheduleArgs(parser, messages):
  """Adds flags specific to snapshot schedule resource policies."""
  AddSnapshotMaxRetentionDaysArgs(parser)
  AddOnSourceDiskDeleteArgs(parser, messages)
  snapshot_properties_group = parser.add_group('Snapshot properties')
  AddSnapshotLabelArgs(snapshot_properties_group)
  snapshot_properties_group.add_argument(
      '--guest-flush',
      action='store_true',
      help='Create an application consistent snapshot by informing the OS to '
           'prepare for the snapshot process.')
  compute_flags.AddStorageLocationFlag(snapshot_properties_group, 'snapshot')


def AddSnapshotMaxRetentionDaysArgs(parser, required=True):
  """Adds max retention days flag for snapshot schedule resource policies."""
  parser.add_argument(
      '--max-retention-days',
      required=required,
      type=arg_parsers.BoundedInt(lower_bound=1),
      help='Maximum number of days snapshot can be retained.')


def AddOnSourceDiskDeleteArgs(parser, messages):
  """Adds onSourceDiskDelete flag for snapshot schedule resource policies."""
  GetOnSourceDiskDeleteFlagMapper(messages).choice_arg.AddToParser(parser)


def AddSnapshotLabelArgs(parser):
  labels_util.GetCreateLabelsFlag(
      extra_message=(
          'The label is added to each snapshot created by the schedule.'
      ),
      labels_name='snapshot-labels',
  ).AddToParser(parser)


def AddGroupPlacementArgs(parser, messages, track):
  """Adds flags specific to group placement resource policies."""
  parser.add_argument(
      '--vm-count',
      type=arg_parsers.BoundedInt(lower_bound=1),
      help='Number of instances targeted by the group placement policy. '
           'Google does not recommend that you use this flag unless you use a '
           'compact policy and you want your policy to work only if it '
           'contains this exact number of VMs.')
  parser.add_argument(
      '--availability-domain-count',
      type=arg_parsers.BoundedInt(lower_bound=1),
      help='Number of availability domain in the group placement policy.')
  GetCollocationFlagMapper(messages, track).choice_arg.AddToParser(parser)
  if track == base.ReleaseTrack.ALPHA:
    GetAvailabilityDomainScopeFlagMapper(messages).choice_arg.AddToParser(
        parser)
    parser.add_argument(
        '--tpu-topology',
        type=str,
        help='Specifies the shape of the TPU pod slice.')
  if track in (base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA):
    parser.add_argument(
        '--max-distance',
        type=arg_parsers.BoundedInt(lower_bound=1, upper_bound=3),
        help='Specifies the number of max logical switches between VMs.'
    )


def GetCollocationFlagMapper(messages, track):
  """Gets collocation flag mapper for resource policies."""
  custom_mappings = {
      'UNSPECIFIED_COLLOCATION':
          ('unspecified-collocation',
           'Unspecified network latency between VMs placed on the same '
           'availability domain. This is the default behavior.'),
      'COLLOCATED':
          ('collocated', 'Low network latency between more VMs placed on the '
           'same availability domain.')
  }
  if track == base.ReleaseTrack.ALPHA:
    custom_mappings.update({
        'CLUSTERED':
            ('clustered', 'Lowest network latency between VMs placed on the '
             'same availability domain.')
    })
  return arg_utils.ChoiceEnumMapper(
      '--collocation',
      messages.ResourcePolicyGroupPlacementPolicy.CollocationValueValuesEnum,
      custom_mappings=custom_mappings,
      default=None,
      help_str='Collocation specifies whether to place VMs inside the same'
      'availability domain on the same low-latency network.')


def GetAvailabilityDomainScopeFlagMapper(messages):
  """Gets availability domain scope flag mapper for resource policies."""
  custom_mappings = {
      'UNSPECIFIED_SCOPE':
          ('unspecified-scope',
           'Instances will be spread across different instrastructure to not '
           'share power, host and networking.'),
      'HOST': ('host', 'Specifies availability domain scope across hosts. '
               'Instances will be spread across different hosts.')
  }
  return arg_utils.ChoiceEnumMapper(
      '--scope',
      messages.ResourcePolicyGroupPlacementPolicy.ScopeValueValuesEnum,
      custom_mappings=custom_mappings,
      default=None,
      help_str='Scope specifies the availability domain to which the VMs '
      'should be spread.')


def AddResourcePoliciesArgs(parser, action, resource, required=False):
  """Adds arguments related to resource policies."""
  if resource == 'instance-template':
    help_text = ('A list of resource policy names (not URLs) to be {action} '
                 'each instance created using this instance template. '
                 'If you attach any resource policies to an instance template, '
                 'you can only use that instance template to create instances '
                 'that are in the same region as the resource policies. '
                 'Do not include resource policies that are located '
                 'in different regions in the same instance template.')
  else:
    help_text = (
        'A list of resource policy names to be {action} the {resource}. '
        'The policies must exist in the same region as the {resource}.')

  parser.add_argument(
      '--resource-policies',
      metavar='RESOURCE_POLICY',
      type=arg_parsers.ArgList(),
      required=required,
      help=help_text.format(action=action, resource=resource))

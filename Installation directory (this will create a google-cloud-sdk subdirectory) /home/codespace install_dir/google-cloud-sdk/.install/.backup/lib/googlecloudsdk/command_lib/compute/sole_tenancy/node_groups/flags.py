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
"""Flags for the `compute sole-tenancy node-groups` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.util.apis import arg_utils

_MAINTENANCE_POLICY_CHOICES = {
    'default': 'VM instances on the host are live migrated to a new physical '
               ' server. This is the default setting.',
    'restart-in-place': 'VM instances on the host are terminated and then '
                        'restarted on the same physical server after the '
                        'maintenance event has completed.',
    'migrate-within-node-group': 'VM instances on the host are live migrated '
                                 'to another node within the same node group.',
}

_MAINTENANCE_POLICY_MAPPINGS = {
    'DEFAULT': 'default',
    'RESTART_IN_PLACE': 'restart-in-place',
    'MIGRATE_WITHIN_NODE_GROUP': 'migrate-within-node-group',
}

_MAINTENANCE_INTERVAL_CHOICES = {
    'as-needed': (
        ' hosts are eligible to receive infrastructure and hypervisor updates'
        ' as they become available.'
    ),
    'recurrent': (
        'hosts receive planned infrastructure and hypervisor updates on a'
        ' periodic basis, but not more frequently than every 28 days. This'
        ' minimizes the number of planned maintenance operations on individual'
        ' hosts and reduces the frequency of disruptions, both live migrations'
        ' and terminations, on individual VMs.'
    ),
}

_MAINTENANCE_INTERVAL_MAPPINGS = {
    'AS_NEEDED': 'as-needed',
    'RECURRENT': 'recurrent',
}


def MakeNodeGroupArg():
  return compute_flags.ResourceArgument(
      resource_name='node group',
      zonal_collection='compute.nodeGroups',
      zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION)


def AddNoteTemplateFlagToParser(parser, required=True):
  parser.add_argument(
      '--node-template',
      required=required,
      help='The name of the node template resource to be set for this node '
           'group.')


def AddCreateArgsToParser(parser):
  """Add flags for creating a node group to the argument parser."""
  parser.add_argument(
      '--description',
      help='An optional description of this resource.')
  AddNoteTemplateFlagToParser(parser)
  parser.add_argument(
      '--target-size',
      required=True,
      type=int,
      help='The target initial number of nodes in the node group.')
  parser.add_argument(
      '--maintenance-policy',
      choices=_MAINTENANCE_POLICY_CHOICES,
      type=lambda policy: policy.lower(),
      help=(
          'Determines the maintenance behavior during host maintenance '
          'events. For more information, see '
          'https://cloud.google.com/compute/docs/nodes#maintenance_policies.'))


def AddUpdateArgsToParser(parser):
  """Add flags for updating a node group to the argument parser."""
  update_node_count_group = parser.add_group(mutex=True)
  update_node_count_group.add_argument(
      '--add-nodes',
      type=int,
      help='The number of nodes to add to the node group.')
  update_node_count_group.add_argument(
      '--delete-nodes',
      metavar='NODE',
      type=arg_parsers.ArgList(),
      help='The names of the nodes to remove from the group.')
  AddNoteTemplateFlagToParser(parser, required=False)


def AddMaintenanceWindowArgToParser(parser):
  """Add flag for adding maintenance window start time to node group."""
  parser.add_argument(
      '--maintenance-window-start-time',
      metavar='START_TIME',
      help=('The time (in GMT) when planned maintenance operations window '
            'begins. The possible values are 00:00, 04:00, 08:00, 12:00, '
            '16:00, 20:00.'))


def AddLocationHintArgToParser(parser):
  """Add --location-hint flag."""
  parser.add_argument(
      '--location-hint',
      hidden=True,
      help=(
          'Used by internal tools to control sub-zone location of node groups.'
      ))


def AddShareSettingArgToParser(parser):
  """Add share setting configuration arguments to parser."""
  group = parser.add_group(help='Manage the properties of a shared setting')
  group.add_argument(
      '--share-setting',
      required=True,
      choices=['projects', 'organization', 'local'],
      help="""
Specify if this node group is shared; and if so, the type of sharing:
share with specific projects or folders.
""")
  group.add_argument(
      '--share-with',
      type=arg_parsers.ArgList(min_length=1),
      metavar='PROJECT',
      help='A list of specific projects this node group should be shared with.')


def AddListingShareSettingsArgToParser(parser):
  """Add --share-setting flag."""
  parser.add_argument(
      '--share-settings',
      action='store_true',
      help='If provided, shows details for the share setting')


def AddSimulateMaintenanceEventNodesArgToParser(parser):
  """Add --nodes flag."""
  parser.add_argument(
      '--nodes',
      metavar='NODE',
      type=arg_parsers.ArgList(),
      help='The names of the nodes to simulate maintenance event.')


def AddPerformMaintenanceNodesArgToParser(parser):
  """Add --nodes flag."""
  parser.add_argument(
      '--nodes',
      required=True,
      metavar='NODE',
      type=arg_parsers.ArgList(min_length=1),
      help='The names of the nodes to perform maintenance on.')


def AddPerformMaintenanceStartTimeArgToParser(parser):
  """Add --start-time flag."""
  parser.add_argument(
      '--start-time',
      metavar='START_TIME',
      type=arg_parsers.Datetime.Parse,
      help=(
          'The requested time for the maintenance window to start. The'
          ' timestamp must be an RFC3339 valid string.'
      ))


def GetMaintenancePolicyEnumMapper(messages):
  return arg_utils.ChoiceEnumMapper(
      '--maintenance-policy',
      messages.NodeGroup.MaintenancePolicyValueValuesEnum,
      custom_mappings=_MAINTENANCE_POLICY_MAPPINGS,
  )


def GetMaintenanceIntervalEnumMapper(messages):
  return arg_utils.ChoiceEnumMapper(
      '--maintenance-interval',
      messages.NodeGroup.MaintenanceIntervalValueValuesEnum,
      custom_mappings=_MAINTENANCE_INTERVAL_MAPPINGS,
  )


def AddAutoscalingPolicyArgToParser(parser, required_mode=False):
  """Add autoscaling configuration  arguments to parser."""

  group = parser.add_group(help='Autoscaling policy for node groups.')
  group.add_argument('--autoscaler-mode',
                     required=required_mode,
                     choices=
                     {
                         'on': 'to permit autoscaling to scale in and out.',
                         'only-scale-out': 'to permit autoscaling to scale only'
                                           ' out and not in.',
                         'off': 'to turn off autoscaling.'
                     },
                     help='Set the mode of an autoscaler for a node group.')
  group.add_argument('--min-nodes',
                     type=int,
                     help="""
The minimum size of the node group. Default is 0 and must be an integer value
smaller than or equal to `--max-nodes`.
""")
  group.add_argument('--max-nodes',
                     type=int,
                     help="""
The maximum size of the node group. Must be smaller or equal to 100 and larger
than or equal to `--min-nodes`. Must be specified if `--autoscaler-mode` is not
``off''.
""")


def AddMaintenanceIntervalArgToParser(parser):
  """Add flag for adding maintenance interval to node group."""
  parser.add_argument(
      '--maintenance-interval',
      choices=_MAINTENANCE_INTERVAL_CHOICES,
      type=lambda policy: policy.lower(),
      help='Specifies the frequency of planned maintenance events.',
  )

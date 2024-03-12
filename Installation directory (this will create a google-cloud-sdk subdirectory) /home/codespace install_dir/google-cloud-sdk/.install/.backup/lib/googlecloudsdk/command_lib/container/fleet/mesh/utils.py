# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utils for GKE Hub Service Mesh commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.anthos.common import file_parsers
from googlecloudsdk.command_lib.container.fleet.features import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class FleetDefaultMemberConfigObject(file_parsers.YamlConfigObject):
  """Fleet Default Member Config abstraction."""

  MANAGEMENT_KEY = 'management'

  def GetManagement(self):
    try:
      management = self[self.MANAGEMENT_KEY]
    except KeyError:
      return None

    return management


def ParseFleetDefaultMemberConfig(yaml_config, msg):
  """Parses the ASM Fleet Default MEmber Config from a yaml file.

  Args:
    yaml_config: object containing arguments passed as flags with the command
    msg: The gkehub messages package.

  Returns:
    member_config: The Membership spec configuration
  """

  if len(yaml_config.data) != 1:
    raise exceptions.Error('Input config file must contain one YAML document.')
  config = yaml_config.data[0]

  management = config.GetManagement()

  if management is None:
    raise exceptions.Error('Missing required field .management')

  # Create empty MemberConfig.
  member_config = msg.ServiceMeshMembershipSpec()

  # The config must contain a value of 'automatic' or 'manual' for the
  # 'management' field.
  if management == 'automatic':
    member_config.management = (
        msg.ServiceMeshMembershipSpec.ManagementValueValuesEnum(
            'MANAGEMENT_AUTOMATIC'
        )
    )
  # Provision Google proto from Google ClientConfig dictionary.
  elif management == 'manual':
    member_config.management = (
        msg.ServiceMeshMembershipSpec.ManagementValueValuesEnum(
            'MANAGEMENT_MANUAL'
        )
    )
  elif management is None or management == 'unspecified':
    member_config.management = (
        msg.ServiceMeshMembershipSpec.ManagementValueValuesEnum(
            'MANAGEMENT_UNSPECIFIED'
        )
    )
  # Unsupported configuration found.
  else:
    status_msg = ('management [{}] is not supported.').format(management)
    log.status.Print(status_msg)

  return member_config


def ParseMemberships(args):
  """Returns a list of memberships to which to apply the command, given the arguments.

  When membership regionalization is complete, this will be deleted and replaced
  with resources.ParseMemberships.

  Args:
    args: object containing arguments passed as flags with the command

  Returns:
    memberships: A list of membership name strings
  """
  memberships = []
  all_memberships = base.ListMemberships()

  if not all_memberships:
    raise exceptions.Error('No Memberships available in the fleet.')

  if hasattr(args, 'membership') and args.membership:
    memberships.append(args.membership)
  elif args.memberships:
    memberships = args.memberships.split(',')
  else:
    if console_io.CanPrompt():
      index = console_io.PromptChoice(
          options=all_memberships,
          message='Please specify a Membership:\n',
          cancel_option=True)
      memberships.append(all_memberships[index])
    else:
      raise calliope_exceptions.RequiredArgumentException(
          '--membership',
          ('Cannot prompt a console for membership. Membership is required. '
           'Please specify `--memberships` to select at least one membership.'))

  if not memberships:
    raise exceptions.Error(
        'At least one membership is required for this command.')

  for membership in memberships:
    if membership not in all_memberships:
      raise exceptions.Error(
          'Membership {} does not exist in the fleet.'.format(membership))

  return memberships

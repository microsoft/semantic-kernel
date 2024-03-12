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
"""Utilities for working with update mask."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from typing import Dict, Union

from googlecloudsdk.calliope import parser_extensions

# FLEET_MESSAGE_TO_FLAGS structure strictly follows proto message definition.
# A message path segment either directly maps to a flag,
# or it maps to a dictionary that has its child fields as keys,
# path structure as values.
FLEET_MESSAGE_TO_FLAGS = {
    'display_name': '--display-name',
    'default_cluster_config': {
        'security_posture_config': {
            'mode': '--security-posture',
            'vulnerability_mode': '--workload-vulnerability-scanning',
        },
        'binary_authorization_config': {
            'evaluation_mode': '--binauthz-evaluation-mode',
            'policy_bindings': '--binauthz-policy-bindings',
        },
    },
}


# Define recursive type for update mask structure.
Level = Dict[str, Union[str, 'Level']]


def FlagToUpdateMaskPaths(
    message_to_flags: Dict[str, Level]
) -> Dict[str, str]:
  """Construct flag to update mask paths during runtime.

  From top level field, combine the string up to the leave dict.

  Flag fields are unique.

  Args:
    message_to_flags: Receive value from MESSAGE_TO_FLAGS.

  Returns:
    A dictionary that maps each flag to the corresponding field update path.

  Given the below message to flag structure,

    {
      parent: {
        child1: {
          foo: '--flag-for-foo',
          child2: {
            bar: '--flag-for-bar'
          }
        }
      }
    }

  It should produce the following flag to update path mapping:

    {
      '--flag-for-foo': parent.child1.foo,
      '--flag-for-bar': parent.child1.child2.bar,
    }
  """

  def Recursive(level: Level) -> Dict[str, str]:
    ret = {}
    for curr_path, flag_or_level in level.items():
      if isinstance(flag_or_level, str):  # The value is a plain flag.
        ret[flag_or_level] = curr_path
      else:  # The value is of Level type.
        for key, remain_path in Recursive(flag_or_level).items():
          ret[key] = curr_path + '.' + remain_path
    else:
      return ret

  return Recursive(message_to_flags)


def GetUpdateMask(
    args: parser_extensions.Namespace, flag_to_update_mask_paths: Dict[str, str]
) -> str:
  """Maps specified flags to API field paths of mutable fields.

  args.GetSpecifiedArgNames() returns a list of specified flags.

  For example, `gcloud alpha container fleet create --display-name my-fleet
  --format 'yaml(displayName)'`
  args.GetSpecifiedArgNames() = ['--display-name', '--format']

  Args:
    args: All arguments passed from CLI.
    flag_to_update_mask_paths: Mapping for a specific resource, such as user
      cluster, or node pool.

  Returns:
    A string that contains yaml field paths to be used in the API update
    request.
  """
  ret = []
  for flag, update_mask in flag_to_update_mask_paths.items():
    if flag in args.GetSpecifiedArgNames():
      ret.append(update_mask)
  else:
    return ','.join(sorted(set(ret)))


def GetFleetUpdateMask(args):
  fleet_flag_to_update_mask_paths = FlagToUpdateMaskPaths(
      FLEET_MESSAGE_TO_FLAGS
  )
  return GetUpdateMask(args, fleet_flag_to_update_mask_paths)


def HasBinauthzConfig(args) -> bool:
  return args.IsKnownAndSpecified(
      'binauthz_evaluation_mode'
  ) or args.IsKnownAndSpecified('binauthz_policy_bindings')

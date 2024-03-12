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
"""Shared resource arguments and flags."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.policy_intelligence import orgpolicy_simulator
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


def _GetPolicyMessage():
  """Returns the organization policy message."""
  return 'GoogleCloudOrgpolicy' + 'V2' + 'Policy'


def _GetCustomConstraintMessage():
  """Returns the organization custom constraint message."""
  return 'GoogleCloudOrgpolicy' + 'V2' + 'CustomConstraint'


def GetParentFromOrganization(org_id):
  """Returns the parent for orgpolicy simulator based on the organization id."""
  return org_id + '/locations/global'


def GetPolicyMessageFromFile(filepath, release_track):
  """Returns a message populated from the JSON or YAML file on the specified filepath.

  Args:
    filepath: str, A local path to an object specification in JSON or YAML
      format.
    release_track: calliope.base.ReleaseTrack, Release track of the command.
  """
  file_contents = files.ReadFileContents(filepath)

  try:
    yaml_obj = yaml.load(file_contents)
    json_str = json.dumps(yaml_obj)
  except yaml.YAMLParseError:
    json_str = file_contents

  op_simulator_api = orgpolicy_simulator.OrgPolicySimulatorApi(
      release_track)
  message = getattr(op_simulator_api.messages,
                    _GetPolicyMessage())
  try:
    return encoding.JsonToMessage(message, json_str)
  except Exception as e:
    raise exceptions.BadFileException(
        'Unable to parse file [{}]: {}.'.format(filepath, e))


def GetCustomConstraintMessageFromFile(filepath, release_track):
  """Returns a message populated from the JSON or YAML file on the specified filepath.

  Args:
    filepath: str, A local path to an object specification in JSON or YAML
      format.
    release_track: calliope.base.ReleaseTrack, Release track of the command.
  """
  file_contents = files.ReadFileContents(filepath)

  try:
    yaml_obj = yaml.load(file_contents)
    json_str = json.dumps(yaml_obj)
  except yaml.YAMLParseError:
    json_str = file_contents

  op_simulator_api = orgpolicy_simulator.OrgPolicySimulatorApi(
      release_track)
  message = getattr(op_simulator_api.messages,
                    _GetCustomConstraintMessage())
  try:
    return encoding.JsonToMessage(message, json_str)
  except Exception as e:
    raise exceptions.BadFileException(
        'Unable to parse file [{}]: {}.'.format(filepath, e))

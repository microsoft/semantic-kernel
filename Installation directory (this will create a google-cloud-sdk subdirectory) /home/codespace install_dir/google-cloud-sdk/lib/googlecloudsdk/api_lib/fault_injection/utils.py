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
"""Util for Fault Injection Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
import six


VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1alpha1'
}

_API_NAME = 'faultinjectiontesting'


# The messages module can also be accessed from client.MESSAGES_MODULE
def GetMessagesModule(release_track=base.ReleaseTrack.ALPHA):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetMessagesModule(_API_NAME, api_version)


def GetClientInstance(release_track=base.ReleaseTrack.ALPHA):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetClientInstance(_API_NAME, api_version)


class InvalidFaultConfigurationError(exceptions.Error):
  """Error if a fault configuration is improperly specified."""


class InvalidExperimentConfigurationError(exceptions.Error):
  """Error if a Experiment configuration is improperly specified."""


def ParseCreateFaultFromYaml(fault, fault_config, parent):
  """Converts the given fault dict to the corresponding import request.

  Args:
    fault: faultId, fault name
    fault_config: dict, fault configuation of the create fault request.
    parent: parent for fault resource

  Returns:
    FaultinjectiontestingProjectsLocationsFaultsCreateRequest
  Raises:
    InvalidFaultConfigurationError: If the fault config is invalid.
  """
  messages = GetMessagesModule(release_track=base.ReleaseTrack.ALPHA)
  request = messages.FaultinjectiontestingProjectsLocationsFaultsCreateRequest
  try:
    import_request_message = encoding.DictToMessage(
        {'fault': fault_config, 'faultId': fault, 'parent': parent}, request
    )
  except AttributeError:
    raise InvalidFaultConfigurationError(
        'An error occurred while parsing the '
        'serialized fault. Please check your '
        'input file.'
    )
  unrecognized_field_paths = _GetUnrecognizedFieldPaths(import_request_message)
  if unrecognized_field_paths:
    error_msg_lines = [
        'Invalid fault config, the following fields are ' + 'unrecognized:'
    ]
    error_msg_lines += unrecognized_field_paths
    raise InvalidFaultConfigurationError('\n'.join(error_msg_lines))

  return import_request_message


def ParseUpdateFaultFromYaml(fault, fault_config):
  """Converts the given fault dict to the corresponding import request.

  Args:
    fault: faultId, fault name
    fault_config: dict, fault configuation of the create fault request.

  Returns:
    FaultinjectiontestingProjectsLocationsFaultsPatchRequest
  Raises:
    InvalidFaultConfigurationError: If the fault config is invalid.
  """
  messages = GetMessagesModule(release_track=base.ReleaseTrack.ALPHA)
  request = messages.FaultinjectiontestingProjectsLocationsFaultsPatchRequest
  try:
    import_request_message = encoding.DictToMessage(
        {'fault': fault_config, 'name': fault}, request
    )
  except AttributeError:
    raise InvalidFaultConfigurationError(
        'An error occurred while parsing the '
        'serialized fault. Please check your '
        'input file.'
    )
  unrecognized_field_paths = _GetUnrecognizedFieldPaths(import_request_message)
  if unrecognized_field_paths:
    error_msg_lines = [
        'Invalid fault config, the following fields are ' + 'unrecognized:'
    ]
    error_msg_lines += unrecognized_field_paths
    raise InvalidFaultConfigurationError('\n'.join(error_msg_lines))

  return import_request_message


def ParseCreateExperimentFromYaml(experiment, experiment_config, parent):
  """Converts the given fault dict to the corresponding import request.

  Args:
    experiment: ExperimentId, Experiment name
    experiment_config: dict, experiment config of the create experiment request.
    parent: parent for experiment resource

  Returns:
    FaultinjectiontestingProjectsLocationsExperimentsCreateRequest
  Raises:
    InvalidExperimentConfigurationError: If the experiment config is invalid.
  """
  messages = GetMessagesModule(release_track=base.ReleaseTrack.ALPHA)
  req = messages.FaultinjectiontestingProjectsLocationsExperimentsCreateRequest
  try:
    import_request_message = encoding.DictToMessage(
        {
            'experiment': experiment_config,
            'experimentId': experiment,
            'parent': parent,
        },
        req,
    )
  except AttributeError:
    raise InvalidExperimentConfigurationError(
        'An error occurred while parsing the '
        'serialized experiment. Please check your '
        'input file.'
    )
  unrecognized_field_paths = _GetUnrecognizedFieldPaths(import_request_message)
  if unrecognized_field_paths:
    error_msg_lines = [
        'Invalid experiment config, the following fields are ' + 'unrecognized:'
    ]
    error_msg_lines += unrecognized_field_paths
    raise InvalidExperimentConfigurationError('\n'.join(error_msg_lines))

  return import_request_message


def ParseUpdateExperimentFromYaml(experiment, experiment_config):
  """Converts the given fault dict to the corresponding import request.

  Args:
    experiment: experimentId, experiment name
    experiment_config: dict, fault configuation of the create fault request.

  Returns:
    FaultinjectiontestingProjectsLocationsExperimentsPatchRequest
  Raises:
    InvalidExperimentConfigurationError: If the experiment config is invalid.
  """
  messages = GetMessagesModule(release_track=base.ReleaseTrack.ALPHA)
  request = (
      messages.FaultinjectiontestingProjectsLocationsExperimentsPatchRequest
  )
  try:
    import_request_message = encoding.DictToMessage(
        {'experiment': experiment_config, 'name': experiment}, request
    )
  except AttributeError:
    raise InvalidExperimentConfigurationError(
        'An error occurred while parsing the '
        'serialized experiment. Please check your '
        'input file.'
    )
  unrecognized_field_paths = _GetUnrecognizedFieldPaths(import_request_message)
  if unrecognized_field_paths:
    error_msg_lines = [
        'Invalid experiment config, the following fields are ' + 'unrecognized:'
    ]
    error_msg_lines += unrecognized_field_paths
    raise InvalidExperimentConfigurationError('\n'.join(error_msg_lines))

  return import_request_message


def _GetUnrecognizedFieldPaths(message):
  """Returns the field paths for unrecognized fields in the message."""
  errors = encoding.UnrecognizedFieldIter(message)
  unrecognized_field_paths = []
  for edges_to_message, field_names in errors:
    message_field_path = '.'.join(six.text_type(e) for e in edges_to_message)
    for field_name in field_names:
      unrecognized_field_paths.append(
          '{}.{}'.format(message_field_path, field_name)
      )
  return sorted(unrecognized_field_paths)

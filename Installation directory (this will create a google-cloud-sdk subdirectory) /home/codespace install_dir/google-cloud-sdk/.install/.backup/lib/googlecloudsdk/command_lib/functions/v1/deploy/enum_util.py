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
"""Enum utilities for 'functions deploy...'."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.functions import flags
from googlecloudsdk.command_lib.util.apis import arg_utils


def ParseDockerRegistry(docker_registry_str):
  """Converts string value of the docker_registry enum to its enum equivalent.

  Args:
    docker_registry_str: a string representing the enum value

  Returns:
    Corresponding DockerRegistryValueValuesEnum value or None for invalid values
  """
  func_message = core_apis.GetMessagesModule('cloudfunctions', 'v1')
  return arg_utils.ChoiceEnumMapper(
      arg_name='docker_registry',
      message_enum=func_message.CloudFunction.DockerRegistryValueValuesEnum,
      custom_mappings=flags.DOCKER_REGISTRY_MAPPING,
  ).GetEnumForChoice(docker_registry_str)

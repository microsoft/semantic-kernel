# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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

"""Factory for EnvironmentConfig message."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.dataproc.shared_messages import (
    execution_config_factory as ecf)
from googlecloudsdk.command_lib.dataproc.shared_messages import (
    peripherals_config_factory as pcf)


class EnvironmentConfigFactory(object):
  """Factory for EnvironmentConfig message.

  Add arguments related to EnvironmentConfig to argument parser and create
  EnvironmentConfig message from parsed arguments.
  """

  def __init__(self, dataproc, execution_config_factory_override=None,
               peripherals_config_factory_override=None):
    """Factory for EnvironmentConfig message.

    Args:
      dataproc: A api_lib.dataproc.Dataproc instance.
      execution_config_factory_override: Override the default
      ExecutionConfigFactory instance. This is a keyword argument.
      peripherals_config_factory_override: Override the default
      PeripheralsConfigFactory instance.
    """
    self.dataproc = dataproc

    self.execution_config_factory = execution_config_factory_override
    if not self.execution_config_factory:
      self.execution_config_factory = ecf.ExecutionConfigFactory(self.dataproc)

    self.peripherals_config_factory = peripherals_config_factory_override
    if not self.peripherals_config_factory:
      self.peripherals_config_factory = (
          pcf.PeripheralsConfigFactory(self.dataproc))

  def GetMessage(self, args):
    """Builds an EnvironmentConfig message instance.

    Args:
      args: Parsed arguments.

    Returns:
      EnvironmentConfig: An environmentConfig message instance. Returns none
      if all fields are None.
    """
    kwargs = {}

    execution_config = self.execution_config_factory.GetMessage(args)
    if execution_config:
      kwargs['executionConfig'] = execution_config

    peripherals_config = (
        self.peripherals_config_factory.GetMessage(args))
    if peripherals_config:
      kwargs['peripheralsConfig'] = peripherals_config

    if not kwargs:
      return None

    return self.dataproc.messages.EnvironmentConfig(**kwargs)


def AddArguments(parser):
  """Adds EnvironmentConfig arguments to parser."""
  # This message doesn't add new arguments.
  _AddDependency(parser)


def _AddDependency(parser):
  ecf.AddArguments(parser)
  pcf.AddArguments(parser)

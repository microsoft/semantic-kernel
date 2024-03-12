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
"""API helpers for interacting with Continuous Validation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis

# Use this format string to exclude irrelevant parts of
# ContinuousValidationConfig when printing it. Note that any new fields will
# not be shown unless explicitly added here.
CV_CONFIG_OUTPUT_FORMAT = (
    'yaml(name,updateTime,enforcementPolicyConfig.enabled)')


class Client(object):
  """API helpers for interacting with ContinuousValidationConfigs."""

  def __init__(self, api_version=None):
    self.client = apis.GetClientInstance(api_version)
    self.messages = apis.GetMessagesModule(api_version)

  def Get(self, cv_config_ref):
    """Get the current project's ContinuousValidationConfig."""
    return self.client.projects.GetContinuousValidationConfig(
        self.messages
        .BinaryauthorizationProjectsGetContinuousValidationConfigRequest(
            name=cv_config_ref.RelativeName()))

  def Set(self, cv_config_ref, cv_config):
    """Set the current project's ContinuousValidationConfig."""
    cv_config.name = cv_config_ref.RelativeName()
    return self.client.projects.UpdateContinuousValidationConfig(cv_config)


def EnsureEnabledFalseIsShown(cv_config):
  """Ensures that "enabled" is shown when printing ContinuousValidationConfig.

  Explicitly sets ContinuousValidationConfig.enforcementPolicyConfig.enabled
  to False when it's unset, so the field is printed as "enabled: false",
  instead of omitting the "enabled" key when CV is not enabled.

  Args:
    cv_config: A ContinuousValidationConfig.

  Returns:
    The modified cv_config.
  """
  if (not cv_config.enforcementPolicyConfig or
      not cv_config.enforcementPolicyConfig.enabled):
    cv_config.enforcementPolicyConfig.enabled = False
  return cv_config

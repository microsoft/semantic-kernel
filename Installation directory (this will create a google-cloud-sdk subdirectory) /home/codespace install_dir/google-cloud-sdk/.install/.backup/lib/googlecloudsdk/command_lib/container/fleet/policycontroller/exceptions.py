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
"""Policy Controller-Specific exceptions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class InvalidMonitoringBackendError(exceptions.Error):
  """For when the API message for the monitoring backend isn't available.

  This may be due to a mismatch between what the API proto supports and what
  the gcloud SDK expects to support (constants.MONITORING_BACKEND).
  """


class InvalidPocoMembershipError(exceptions.Error):
  """For when the Policy Controller feature is not enabled for a membership."""


class MultiInvalidPocoMembershipsError(exceptions.MultiError):
  """For when multiple memberships do not have Policy Controller enabled."""


class MutexError(exceptions.Error):
  """For when two mutually exclusive flags are specified."""


class NoSuchContentError(exceptions.Error):
  """For when trying to configure unsupported or missing content.

  For instance, if the user attempts to install a bundle that doesn't exist or
  isn't supported, this error should be thrown.
  """


class SafetyError(exceptions.Error):
  """For when a safety check is required, but redundent.

  If this is thrown it means some other check failed. For example, a required
  argparse argument should never be None - argparse should throw an error if it
  is not passed - but safety requires we rule out the None value in later code.
  """


class InvalidConfigYaml(exceptions.Error):
  """For when a membership configuration is invalid or could not be parsed."""


class MissingFleetDefaultMemberConfig(exceptions.Error):
  """For when the fleet default member config is required but missing."""

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
"""This module holds exceptions raised by Runapps commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class ConfigurationError(exceptions.Error):
  """Indicates an error in configuration."""


class ServiceNotFoundError(exceptions.Error):
  """Indicates that a provided service name was not found."""


class IntegrationNotFoundError(exceptions.Error):
  """Indicates that a provided integration name was not found."""


class PlatformError(exceptions.Error):
  """Command not supported for the platform."""


class ArgumentError(exceptions.Error):
  pass


class FieldMismatchError(exceptions.Error):
  """Given field value doesn't match the expected type."""


class IntegrationsOperationError(exceptions.Error):
  """An error encountered when waiting for LRO to finish."""


class UnsupportedIntegrationsLocationError(exceptions.Error):
  """An error encountered when an unsupported location is provided."""

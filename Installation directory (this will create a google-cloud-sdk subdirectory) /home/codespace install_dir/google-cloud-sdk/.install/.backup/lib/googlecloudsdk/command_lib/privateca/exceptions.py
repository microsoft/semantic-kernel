# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Helpers for raising exceptions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class FileOutputError(exceptions.Error):
  """Error thrown for issues with writing to files."""


class InvalidCertificateAuthorityTypeError(exceptions.Error):
  """Error thrown for performing a command on the wrong CA type."""


class NoUpdateException(exceptions.Error):
  """Error thrown when an update command is run resulting in no updates."""


class UserAbortException(exceptions.Error):
  """Error thrown when an a user aborts the command."""


class InsufficientPermissionException(exceptions.Error):
  """Indicates that a user is missing required permissions for an operation."""

  def __init__(self, resource, missing_permissions):
    """Create a new InsufficientPermissionException.

    Args:
      resource: str, The resource on which the user needs permissions.
      missing_permissions: iterable, The missing permissions.
    """
    super(InsufficientPermissionException, self).__init__(
        'The current user does not have permissions for this operation. '
        'Please ensure you have {} permissions on the {} and that '
        'you are logged-in as the correct user and try again.'.format(
            ','.join(missing_permissions), resource))


class UnsupportedKmsKeyTypeException(exceptions.Error):
  """Indicates that a user is using an unsupported KMS key type."""

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

"""Storage client-side error classes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions as core_exceptions


class Error(core_exceptions.Error):
  """Base exception for command_lib.storage modules."""


class FatalError(Error):
  """Error raised when future execution should stop."""


class HashMismatchError(Error):
  """Error raised when hashes don't match after operation."""


class InvalidPythonVersionError(Error):
  """Error raised for an invalid Python version."""


class InvalidUrlError(Error):
  """Error raised when the url string is not in the expected format."""


class SystemPermissionError(Error):
  """Error raised when encountering a systems-permissions-related issue."""


class ValueCannotBeDeterminedError(Error):
  """Error raised when attempting to access unknown information."""

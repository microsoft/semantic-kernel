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
"""Wrapper for user-visible error exceptions to raise in the CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class FunctionsError(exceptions.Error):
  """Exceptions for Functions errors."""


class InvalidArgumentException(exceptions.Error):
  """InvalidArgumentException is for malformed arguments."""

  def __init__(self, parameter_name, message):
    """Creates InvalidArgumentException.

    Args:
      parameter_name: str, the parameter flag or argument name
      message: str, the exception message
    """
    super(InvalidArgumentException, self).__init__(
        'Invalid value for [{0}]: {1}'.format(parameter_name, message)
    )
    self.parameter_name = parameter_name


class RequiredArgumentException(exceptions.Error):
  """An exception for when a usually optional argument is required in this case."""

  def __init__(self, parameter_name, message):
    super(RequiredArgumentException, self).__init__(
        'Missing required argument [{0}]: {1}'.format(parameter_name, message)
    )
    self.parameter_name = parameter_name


def StatusToFunctionsError(status, error_message=None):
  """Convert a google.rpc.Status (used for LRO errors) into a FunctionsError."""
  if error_message:
    return FunctionsError(error_message)
  return FunctionsError(status.message)

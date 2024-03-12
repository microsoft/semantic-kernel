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
"""Version-agnostic errors to raise for gcloud functions commands."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.core import exceptions


class FunctionsError(exceptions.Error):
  """Base exception for user recoverable Functions errors."""


class SourceArgumentError(calliope_exceptions.InvalidArgumentException):
  """Exception for errors related to using the --source argument."""

  def __init__(self, message):
    super(SourceArgumentError, self).__init__('--source', message)


class OversizedDeploymentError(FunctionsError):
  """Exception to indicate the deployment is too big."""

  def __init__(self, actual_size, max_allowed_size):
    super(OversizedDeploymentError, self).__init__(
        'Uncompressed deployment is {}, bigger than maximum allowed size of {}.'
        .format(actual_size, max_allowed_size)
    )


class IgnoreFileNotFoundError(calliope_exceptions.InvalidArgumentException):
  """Exception for when file specified by --ignore-file is not found."""

  def __init__(self, message):
    super(IgnoreFileNotFoundError, self).__init__('--ignore-file', message)


class SourceUploadError(FunctionsError):
  """Exception for source upload failures."""

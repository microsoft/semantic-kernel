# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Common utility functions for sql errors and exceptions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class Error(exceptions.Error):
  """Base exception for all sql errors."""


class ArgumentError(Error):
  """Command argument error."""


class CancelledError(Error):
  """An exception raised if the user chooses not to continue."""


class OperationError(Error):
  """An exception raised if an operation encounters an error."""


class ResourceNotFoundError(Error):
  """An exception raised when a resource could not be found by the server."""


class SqlClientNotFoundError(Error):
  """An exception raised when a locally installed sql client cannot be found."""


class ConnectionError(Error):
  """An exception raised when a connection could not be made to a sql instance.
  """


class UpdateError(Error):
  """An error raised when a connection could not be made to a sql instance."""


class CloudSqlProxyError(Error):
  """An error raised when the Cloud SQL Proxy fails to start."""


class InvalidStateError(Error):
  """An error raised when a Cloud SQL resource is in an invalid state."""


class SqlProxyNotFound(Error):
  """An error raised when no sql proxy found."""

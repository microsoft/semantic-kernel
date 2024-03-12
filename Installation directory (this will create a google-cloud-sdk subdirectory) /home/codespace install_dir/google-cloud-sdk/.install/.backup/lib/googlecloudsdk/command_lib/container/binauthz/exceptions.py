# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Exceptions for user-visible binauthz CLI errors."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class Error(exceptions.Error):
  """Base error for binary authorization."""


class NotFoundError(Error):
  """Indicates a resource could not be found."""


class AlreadyExistsError(Error):
  """Indicates a resource to be added already exists."""


class InvalidStateError(Error):
  """Indicates a resource is in an invalid state."""


class InvalidArgumentError(Error):
  """Indicates a flag/argument is invalid."""

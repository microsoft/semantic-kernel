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
"""Exceptions for concept args."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class Error(exceptions.Error):
  """Base class for errors in this module."""


class ConstraintError(Error):
  """Error when converting a constraint."""

  def __init__(self, concept_name, kind, string, message):
    super(ConstraintError, self).__init__(
        'Invalid {} [{}] for [{}]. {}'.format(
            kind, string, concept_name, message))


class ParseError(Error):
  """Error when parsing a concept."""

  def __init__(self, concept_name, message):
    super(ParseError, self).__init__(
        'Failed to parse [{}]. {}'.format(concept_name, message))


class ValidationError(Error):
  """Error when validating a concept."""

  def __init__(self, concept_name, message):
    super(ValidationError, self).__init__(
        'Failed to validate [{}]. {}'.format(concept_name, message))


class InitializationError(Error):
  """Error when a concept was initialized with an invalid value."""


class MissingRequiredArgumentError(Error):
  """Error when a required concept can't be found."""

  def __init__(self, concept_name, message):
    super(MissingRequiredArgumentError, self).__init__(
        'No value was provided for [{}]: {}'.format(concept_name, message))


class ModalGroupError(Error):
  """Error when a modal group was not specified correctly."""

  def __init__(self, concept_name, specified, missing):
    super(ModalGroupError, self).__init__(
        'Failed to specify [{}]: '
        '{specified}: {missing} must be specified.'
        .format(concept_name, specified=specified, missing=missing))


class OptionalMutexGroupError(Error):
  """Error when an optional mutex group was not specified correctly."""

  def __init__(self, concept_name, conflict):
    super(OptionalMutexGroupError, self).__init__(
        'Failed to specify [{}]: At most one of {conflict} can be specified.'
        .format(concept_name, conflict=conflict))


class RequiredMutexGroupError(Error):
  """Error when a required mutex group was not specified correctly."""

  def __init__(self, concept_name, conflict):
    super(RequiredMutexGroupError, self).__init__(
        'Failed to specify [{}]: Exactly one of {conflict} must be specified.'
        .format(concept_name, conflict=conflict))

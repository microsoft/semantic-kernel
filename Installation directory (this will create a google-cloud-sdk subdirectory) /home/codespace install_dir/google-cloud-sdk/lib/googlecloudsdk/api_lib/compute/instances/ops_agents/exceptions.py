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
"""Errors for the compute VM instances Ops Agents commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions

import six


class Error(exceptions.Error):
  """Base exception for Ops Agents exceptions."""


class PolicyError(Error):
  """Base exception for Ops Agents policy exceptions."""


class PolicyMalformedError(PolicyError):
  """Raised when the specified Ops Agents policy is malformed."""

  def __init__(self, policy_id):
    message = (
        'Encountered a malformed policy. The Ops Agents policy [{policy_id}] '
        'may have been modified directly by the OS Config guest policy API / '
        'gcloud commands. If so, please delete and re-create with the Ops '
        'Agents policy gcloud commands. If not, this may be an internal error.'
        .format(policy_id=policy_id))
    super(PolicyMalformedError, self).__init__(message)


class PolicyNotFoundError(PolicyError):
  """Raised when the specified Ops Agents policy is not found."""

  def __init__(self, policy_id):
    message = (
        'Ops Agents policy [{policy_id}] not found.'
        .format(policy_id=policy_id))
    super(PolicyNotFoundError, self).__init__(message)


class PolicyValidationError(PolicyError):
  """Raised when Ops Agents policy validation fails."""


class PolicyValidationMultiError(PolicyValidationError):
  """Raised when multiple Ops Agents policy validations fail."""

  def __init__(self, errors):
    super(PolicyValidationMultiError, self).__init__(
        ' | '.join(six.text_type(error) for error in errors))
    self.errors = errors

# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Exceptions thrown by Org Policy commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class OrgPolicyError(exceptions.Error):
  """Top-level exception for Org Policy errors."""


class InvalidInputError(OrgPolicyError):
  """Exception for invalid input."""


class OrgPolicyRuleNotFoundError(OrgPolicyError):
  """Exception for a nonexistent rule on an organization policy."""


class OrgPolicyValuesNotFoundError(OrgPolicyError):
  """Exception for nonexistent values on an organization policy rule."""


class BooleanPolicyValidationError(OrgPolicyError):
  """Exception for an invalid boolean policy."""


class ConcurrencyError(OrgPolicyError):
  """Exception for a concurrency issue."""


class OperationNotSupportedError(OrgPolicyError):
  """Exception for an operation that is not supported."""

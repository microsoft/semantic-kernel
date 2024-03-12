# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Convenience functions for dealing with gaia accounts."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties

# API restriction: account names cannot be greater than 32 characters.
_MAX_ACCOUNT_NAME_LENGTH = 32


class GaiaException(core_exceptions.Error):
  """GaiaException is for non-code-bug errors in gaia."""


def MapGaiaEmailToDefaultAccountName(email):
  """Returns the default account name given a GAIA email."""
  # Maps according to following rules:
  # 1) Remove all characters following and including '@'.
  # 2) Lowercase all alpha characters.
  # 3) Replace all non-alphanum characters with '_'.
  # 4) Prepend with 'g' if the username does not start with an alpha character.
  # 5) Truncate the username to 32 characters.
  account_name = email.partition('@')[0].lower()
  if not account_name:
    raise GaiaException('Invalid email address [{email}].'
                        .format(email=email))
  account_name = ''.join(
      [char if char.isalnum() else '_' for char in account_name])
  if not account_name[0].isalpha():
    account_name = 'g' + account_name
  return account_name[:_MAX_ACCOUNT_NAME_LENGTH]


def GetDefaultAccountName():
  return MapGaiaEmailToDefaultAccountName(properties.VALUES.core.account.Get())

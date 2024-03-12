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
"""Helpers for naming concepts and attributes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def StripFlagPrefix(name):
  """Strip the flag prefix from a name, if present."""
  if name.startswith('--'):
    return name[2:]
  return name


def AddFlagPrefix(name):
  """Add the flag prefix to a name, if not present."""
  if name.startswith('--'):
    return name
  # Does not guarantee a valid flag name.
  return '--' + name


def ConvertToFlagName(name):
  """Convert name to flag format (e.g. '--foo-bar')."""
  return AddFlagPrefix(name).lower().replace('_', '-').replace(' ', '-')


def ConvertToNamespaceName(name):
  """Convert name to namespace format (e.g. 'foo_bar')."""
  name = StripFlagPrefix(name)
  return name.lower().replace('-', '_').replace(' ', '_')


def ConvertToPositionalName(name):
  """Convert name to positional format (e.g. 'FOO_BAR')."""
  name = StripFlagPrefix(name)
  return name.upper().replace('-', '_').replace(' ', '_')


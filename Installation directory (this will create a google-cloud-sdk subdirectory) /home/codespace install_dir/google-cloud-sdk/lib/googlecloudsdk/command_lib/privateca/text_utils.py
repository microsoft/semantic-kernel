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
"""Helpers for dealing with text."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from dateutil import tz
from googlecloudsdk.core.util import times


def SnakeCaseToCamelCase(name):
  words = name.split('_')
  return words[0].lower() + ''.join(
      [w[0].upper() + w[1:].lower() for w in words[1:]])


def ToSnakeCaseDict(dictionary):
  """Recursively convert all keys in nested dictionaries to snakeCase."""
  new_dict = {}
  for key, val in dictionary.items():
    snaked_key = SnakeCaseToCamelCase(key)
    if isinstance(val, dict):
      new_dict[snaked_key] = ToSnakeCaseDict(val)
    else:
      new_dict[snaked_key] = val

  return new_dict


def TransformNotBeforeTime(subject_description):
  """Use this function in a display transform to truncate anything smaller than minutes from ISO8601 timestamp."""
  if subject_description and 'notBeforeTime' in subject_description:
    return times.ParseDateTime(
        subject_description.get('notBeforeTime')).astimezone(
            tz.tzutc()).strftime('%Y-%m-%dT%H:%MZ')
  return ''


def TransformNotAfterTime(subject_description):
  """Use this function in a display transform to truncate anything smaller than minutes from ISO8601 timestamp."""
  if subject_description and 'notAfterTime' in subject_description:
    return times.ParseDateTime(
        subject_description.get('notAfterTime')).astimezone(
            tz.tzutc()).strftime('%Y-%m-%dT%H:%MZ')
  return ''

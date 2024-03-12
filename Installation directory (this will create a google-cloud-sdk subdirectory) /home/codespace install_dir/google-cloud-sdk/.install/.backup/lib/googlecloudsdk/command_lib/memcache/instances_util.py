# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Utilities for `gcloud memcache instances` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
import six

MEMCACHE_EXTENDED_OPTIONS = ('track-sizes', 'watcher-logbuf-size',
                             'worker-logbuf-size', 'lru-crawler',
                             'idle-timeout', 'lru-maintainer', 'maxconns-fast',
                             'hash-algorithm')


class Error(Exception):
  """Exceptions for this module."""


class InvalidTimeOfDayError(Error):
  """Error for passing invalid time of day."""


def CheckMaintenanceWindowStartTimeField(maintenance_window_start_time):
  if maintenance_window_start_time < 0 or maintenance_window_start_time > 23:
    raise InvalidTimeOfDayError(
        'A valid time of day must be specified (0, 23) hours.'
    )
  return maintenance_window_start_time


def ConvertDurationToJsonFormat(maintenance_window_duration):
  duration_in_seconds = maintenance_window_duration * 3600
  return six.text_type(duration_in_seconds) + 's'


def NodeMemory(value):
  """Declarative command argument type for node-memory flag."""
  size = arg_parsers.BinarySize(
      suggested_binary_size_scales=['MB', 'GB'], default_unit='MB')
  return int(size(value) / 1024 / 1024)


def Parameters(value):
  """Declarative command argument type for parameters flag."""
  return arg_parsers.ArgDict(key_type=_FormatExtendedOptions)(value)


def _FormatExtendedOptions(key):
  """Replaces dash with underscore for extended options parameters."""
  if key in MEMCACHE_EXTENDED_OPTIONS:
    return key.replace('-', '_')
  return key

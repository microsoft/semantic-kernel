# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities for reschedule Memcache instances maintenance window."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


class Error(Exception):
  """Exceptions for this module."""


class NoScheduleTimeSpecifiedError(Error):
  """Error for calling update command with no args that represent fields."""


def CheckSpecificTimeField(unused_instance_ref, args, patch_request):
  """Hook to check specific time field of the request."""
  if args.IsSpecified('reschedule_type'):
    if args.reschedule_type.lower() == 'specific-time':
      if args.IsSpecified('schedule_time'):
        return patch_request
      else:
        raise NoScheduleTimeSpecifiedError('Must specify schedule time')
  return patch_request

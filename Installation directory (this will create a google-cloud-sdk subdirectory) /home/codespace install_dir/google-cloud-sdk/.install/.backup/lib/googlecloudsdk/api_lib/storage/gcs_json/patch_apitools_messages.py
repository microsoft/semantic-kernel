# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Patches for pickling isssues in apitools.

The storage surface needs to be able to serialize apitools messages to support
multiprocessing; however, there are a number of bugs with pickling apitools
messages that need to be patched, pending more permanent fixes.
"""

# TODO(b/171296237): Remove this file when fixes are submitted in apitools.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.protorpclite import messages


def _time_zone_offset_init_args(self):
  """Implements apitools.base.protorpclite.util.TimeZoneOffset.__getinitargs__.

  The apitools TimeZoneOffset class inherits from datetime.datetime, which
  implements custom picking behavior in __reduce__. This reduce method cannot
  handle the additional argument that TimeZoneOffset adds to __init__, which
  makes TimeZoneOffset unpicklable without implementing __getinitargs__ as
  we do here.

  Args:
    self (TimeZoneOffset): an instance of TimeZoneOffset.

  Returns:
    A tuple of arguments passed to TimeZoneOffset.__init__ when unpickling.
  """
  # pylint: disable=protected-access
  return (self._TimeZoneOffset__offset,)
  # pylint: enable=protected-access


def patch():
  messages.util.TimeZoneOffset.__getinitargs__ = _time_zone_offset_init_args

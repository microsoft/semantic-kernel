# -*- coding: utf-8 -*-
# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Provides a tzinfo subclass to represent the UTC timezone."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from datetime import timedelta
from datetime import tzinfo


class UTC(tzinfo):
  """Timezone information class used to convert datetime timestamps to UTC.

  This class is necessary to convert timestamps to UTC. By default Python
  datetime objects are timezone unaware. This created problems when interacting
  with cloud object timestamps which are timezone-aware. This issue appeared
  when handling the timeCreated metadata attribute; the values returned by the
  service were placed in RFC 3339 format in the storage_v1_messages module. RFC
  3339 requires a timezone in any timestamp. This caused problems as the
  datetime object elsewhere in the code was timezone unaware and was different
  by exactly one hour. The main problem was that the local system used daylight
  savings time which adjusted the timestamp ahead by one hour.
  """

  def utcoffset(self, _):
    """An offset of the number of minutes away from UTC this tzinfo object is.

    Returns:
      A time duration of zero. UTC is zero minutes away from UTC.
    """
    return timedelta(0)

  def tzname(self, _):
    """A method to retrieve the name of this timezone object.

    Returns:
      The name of the timezone (i.e. 'UTC').
    """
    return 'UTC'

  def dst(self, _):
    """A fixed offset to handle daylight savings time (DST).

    Returns:
      A time duration of zero as UTC does not use DST.
    """
    return timedelta(0)

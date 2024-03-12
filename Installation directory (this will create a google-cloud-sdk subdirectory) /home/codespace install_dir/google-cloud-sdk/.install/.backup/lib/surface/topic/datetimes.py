# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Date/time input format supplementary help."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


# NOTE: If the name of this topic is modified, please make sure to update all
# references to it in error messages and other help messages as there are no
# tests to catch such changes.
class DateTimes(base.TopicCommand):
  """Date/time input format supplementary help.

  *gcloud* command line flags and filter expressions that expect date/time
  string values support common input formats. These formats fall into two main
  categories: absolute date/times and relative durations.

  ### Absolute date/time formats

  Absolute date/time input formats minimally support
  [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) and
  [RFC 822](https://www.ietf.org/rfc/rfc0822.txt) date/times. When omitted the
  date/time value defaults are:

  * year, month, day - current value
  * hour, minute, second, fractional second - 0

  The supported absolute date/time input formats are listed here.

  ISO 8601 / RFC 3339 zulu:

      2003-09-25T10:49:41.519Z
      2003-09-25T10:49:41Z

  ISO 8601 numeric timezone offset:

      2003-09-25T10:49:41.5-0000
      2003-09-25T10:49:41.5-03:00
      2003-09-25T10:49:41.5+0300

  ISO with omitted parts:

      2003-09-25T10:49:41
      2003-09-25T10:49
      2003-09-25T10
      2003-09-25

  RFC 822:

      Thu, 25 Sep 2003 10:49:41 -0300

  UNIX date command, explicit timezone:

      Thu Sep 25 10:36:28 EDT 2003
      2003 10:36:28 EDT 25 Sep Thu

  local timezone:

      Thu Sep 25 10:36:28 2003

  omitted parts (date parts default to the current date, time parts default
  to 0):

      Thu Sep 25 10:36:28
      Thu Sep 10:36:28
      Thu 10:36:28
      Thu 10:36
      10:36

  omitted parts with different order:

      Thu Sep 25 2003
      Sep 25 2003
      Sep 2003
      Sep
      2003

  ISO no separators:

      20030925T104941.5-0300
      20030925T104941-0300
      20030925T104941
      20030925T1049
      20030925T10
      20030925

  no T separator:

      20030925104941
      200309251049

  other date orderings:

      2003-09-25
      2003-Sep-25
      25-Sep-2003
      Sep-25-2003
      09-25-2003

  other date separators:

      2003.Sep.25
      2003/09/25
      2003 Sep 25
      2003 09 25

  ### Relative duration date/time formats

  A relative duration specifies a date/time relative to the current time.
  Relative durations are based on
  [ISO 8601 durations](https://en.wikipedia.org/wiki/ISO_8601#Durations).
  They are case-insensitive and must be prefixed with +P or -P.

  A fully qualified duration string contains year, month, day, hour, minute,
  second, and fractional second parts. Each part is a number followed by a
  single character suffix:

  * P - period (the duration designator)
  * Y - year
  * M - minute if after T or H, month otherwise
  * D - day
  * T - separates date parts from time parts
  * H - hour
  * M - minute if after T or H, month otherwise
  * S - second (for fractional seconds, use decimal value for seconds)

  At least one part must be specified. Omitted parts default to 0.

    -P1Y2M3DT4H5M6.7S
    +p1y2m3dT4h5m6.7s

  A relative duration may be used in any context that expects a date/time
  string.

  For example:

  * 1 month ago: -p1m
  * 30 minutes from now: +pt30m
  * 2 hours and 30 minutes ago: -p2h30m

  ### Absolute duration formats

  An absolute duration specifies a period of time. It has the same syntax as
  a relative duration except that there is no leading *+* or *-*, and the
  leading *P* is optional.

  For example:

  * 1 month: 1m
  * 1 hour 30 minutes: 1h30m
  * 30 minutes: t30m
  """

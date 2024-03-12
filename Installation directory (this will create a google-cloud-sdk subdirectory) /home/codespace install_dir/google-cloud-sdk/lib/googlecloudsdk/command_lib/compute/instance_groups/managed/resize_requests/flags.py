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

"""Flags for instance group manager resize requests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core.util import iso_duration
from googlecloudsdk.core.util import times


DEFAULT_CREATE_OR_LIST_FORMAT_BETA = """\
    table(
      name,
      location():label=LOCATION,
      location_scope():label=SCOPE,
      resize_by,
      state,
      requestedRunDuration()
    )
"""

DEFAULT_CREATE_OR_LIST_FORMAT_ALPHA = """\
    table(
      name,
      location():label=LOCATION,
      location_scope():label=SCOPE,
      resize_by,
      state,
      status.queuingPolicy.validUntilTime,
      requestedRunDuration()
    )
"""

_RELEASE_TRACK_TO_LIST_FORMAT = {
    base.ReleaseTrack.BETA: DEFAULT_CREATE_OR_LIST_FORMAT_BETA,
    base.ReleaseTrack.ALPHA: DEFAULT_CREATE_OR_LIST_FORMAT_ALPHA,
}


def _TransformRequestedRunDuration(resource):
  """Properly format requested_run_duration field."""

  # Use get with dictionary optional return value to skip existence checking.
  run_duration = resource.get('requestedRunDuration', {})
  if not run_duration:
    return ''
  seconds = int(run_duration.get('seconds'))
  days = seconds // 86400  # 60 * 60 * 24
  seconds -= days * 86400
  hours = seconds // 3600  # 60 * 60
  seconds -= hours * 3600
  minutes = seconds // 60
  seconds -= minutes * 60
  duration = iso_duration.Duration(
      days=days, hours=hours, minutes=minutes, seconds=seconds)
  return times.FormatDuration(duration, parts=-1)


def AddOutputFormat(parser, release_track):
  parser.display_info.AddFormat(_RELEASE_TRACK_TO_LIST_FORMAT[release_track])
  parser.display_info.AddTransforms({
      'requestedRunDuration': _TransformRequestedRunDuration,
  })

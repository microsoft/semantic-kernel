# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Utilities for gcloud ml video-intelligence commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import iso_duration
from googlecloudsdk.core.util import times

VIDEO_API = 'videointelligence'
VIDEO_API_VERSION = 'v1'


INPUT_ERROR_MESSAGE = ('[{}] is not a valid format for video input. Must be a '
                       'local path or a Google Cloud Storage URI '
                       '(format: gs://bucket/file).')

OUTPUT_ERROR_MESSAGE = ('[{}] is not a valid format for result output. Must be '
                        'a Google Cloud Storage URI '
                        '(format: gs://bucket/file).')

SEGMENT_ERROR_MESSAGE = ('Could not get video segments from [{0}]. '
                         'Please make sure you give the desired '
                         'segments in the form: START1:END1,START2:'
                         'END2, etc.: [{1}]')


class Error(exceptions.Error):
  """Base error class for this module."""


class SegmentError(Error):
  """Error for poorly formatted video segment messages."""


class VideoUriFormatError(Error):
  """Error if the video input URI is invalid."""


class AudioTrackError(Error):
  """Error if the audio tracks setting is invalid."""


def ValidateAndParseSegments(given_segments):
  """Get VideoSegment messages from string of form START1:END1,START2:END2....

  Args:
    given_segments: [str], the list of strings representing the segments.

  Raises:
    SegmentError: if the string is malformed.

  Returns:
    [GoogleCloudVideointelligenceXXXVideoSegment], the messages
      representing the segments or None if no segments are specified.
  """
  if not given_segments:
    return None

  messages = apis.GetMessagesModule(VIDEO_API, VIDEO_API_VERSION)
  segment_msg = messages.GoogleCloudVideointelligenceV1VideoSegment
  segment_messages = []
  segments = [s.split(':') for s in given_segments]
  for segment in segments:
    if len(segment) != 2:
      raise SegmentError(SEGMENT_ERROR_MESSAGE.format(
          ','.join(given_segments), 'Missing start/end segment'))
    start, end = segment[0], segment[1]
    # v1beta2 requires segments as a duration string representing the
    # count of seconds and fractions of seconds to nanosecond resolution
    # e.g. offset "42.596413s". To perserve backward compatibility with v1beta1
    # we will parse any segment timestamp with out a duration unit as an
    # int representing microseconds.
    try:
      start_duration = _ParseSegmentTimestamp(start)
      end_duration = _ParseSegmentTimestamp(end)
    except ValueError as ve:
      raise SegmentError(SEGMENT_ERROR_MESSAGE.format(
          ','.join(given_segments), ve))

    sec_fmt = '{}s'
    segment_messages.append(segment_msg(
        endTimeOffset=sec_fmt.format(end_duration.total_seconds),
        startTimeOffset=sec_fmt.format(start_duration.total_seconds)))
  return segment_messages


def _ParseSegmentTimestamp(timestamp_string):
  """Parse duration formatted segment timestamp into a Duration object.

  Assumes string with no duration unit specified (e.g. 's' or 'm' etc.) is
  an int representing microseconds.

  Args:
    timestamp_string: str, string to convert

  Raises:
    ValueError: timestamp_string is not a properly formatted duration, not a
    int or int value is <0

  Returns:
    Duration object represented by timestamp_string
  """
  # Assume timestamp_string passed as int number of microseconds if no unit
  # e.g. 4566, 100, etc.
  try:
    microseconds = int(timestamp_string)
  except ValueError:
    try:
      duration = times.ParseDuration(timestamp_string)
      if duration.total_seconds < 0:
        raise times.DurationValueError()
      return duration
    except (times.DurationSyntaxError, times.DurationValueError):
      raise ValueError('Could not parse timestamp string [{}]. Timestamp must '
                       'be a properly formatted duration string with time '
                       'amount and units (e.g. 1m3.456s, 2m, 14.4353s)'.format(
                           timestamp_string))
  else:
    log.warning("Time unit missing ('s', 'm','h') for segment timestamp [{}], "
                "parsed as microseconds.".format(timestamp_string))

  if microseconds < 0:
    raise ValueError('Could not parse duration string [{}]. Timestamp must be'
                     'greater than >= 0)'.format(timestamp_string))

  return iso_duration.Duration(microseconds=microseconds)


def ValidateOutputUri(output_uri):
  """Validates given output URI against validator function.

  Args:
    output_uri: str, the output URI for the analysis.

  Raises:
    VideoUriFormatError: if the URI is not valid.

  Returns:
    str, The same output_uri.
  """
  if output_uri and not storage_util.ObjectReference.IsStorageUrl(output_uri):
    raise VideoUriFormatError(OUTPUT_ERROR_MESSAGE.format(output_uri))
  return output_uri


def UpdateRequestWithInput(unused_ref, args, request):
  """The Python hook for yaml commands to inject content into the request."""
  path = args.input_path
  if os.path.isfile(path):
    request.inputContent = files.ReadBinaryFileContents(path)
  elif storage_util.ObjectReference.IsStorageUrl(path):
    request.inputUri = path
  else:
    raise VideoUriFormatError(INPUT_ERROR_MESSAGE.format(path))
  return request


# Argument Processors


def AudioTrackProcessor(tracks):
  """Verify at most two tracks, convert to [int, int]."""
  if len(tracks) > 2:
    raise AudioTrackError('Can not specify more than two audio tracks.')
  return tracks

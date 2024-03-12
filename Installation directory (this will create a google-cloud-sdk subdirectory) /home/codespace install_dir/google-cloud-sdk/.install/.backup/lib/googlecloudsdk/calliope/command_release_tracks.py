# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Helpers to separate release tracks in declarative commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from googlecloudsdk.calliope import base

ALL_TRACKS = [t.id for t in base.ReleaseTrack.AllValues()]
RELEASE_TRACKS = 'release_tracks'
GROUP = 'group'


class DoesNotExistForTrackError(Exception):
  pass


# This function should be kept in sync with function in
# cloud/sdk/surface_specs/release_tracks.py
def _SetValuesForTrack(obj, track):
  """Recursively modify an object to have only values for the provided track.

  Args:
    obj: The object to modify.
    track: The track to extract the values for.
  Returns:
    The modified object
  Raises:
    DoesNotExistForTrackError: if the object does not exist for the track.
  """
  if isinstance(obj, dict):
    is_group = GROUP in obj
    # Check if it exists for this track, and raise an Exception if it doesn't.
    if RELEASE_TRACKS in obj:
      if track not in obj[RELEASE_TRACKS]:
        raise DoesNotExistForTrackError()
      del obj[RELEASE_TRACKS]
    # Copy tracked properties for this track to the object itself.
    if track in obj:
      for key, value in obj[track].items():
        obj[key] = value
    # Remove all tracked properties
    for track_key in ALL_TRACKS:
      if track_key in obj:
        del obj[track_key]
    # Recursively update all children.
    # Remove them if they don't exist for the track.
    for key, child in list(obj.items()):
      try:
        _SetValuesForTrack(child, track)
      except DoesNotExistForTrackError:
        del obj[key]
    if is_group and not obj:
      # All of the children have been omitted for an arg group nested under the
      # `group` key.
      raise DoesNotExistForTrackError()
  elif isinstance(obj, list):
    # Recursively update all children.
    # Remove them if they don't exist for the track.
    children = list(obj)
    obj[:] = []
    for child in children:
      try:
        obj.append(_SetValuesForTrack(child, track))
      except DoesNotExistForTrackError:
        pass
  return obj


def SeparateDeclarativeCommandTracks(command_impls):
  """Separate combined track definitions.

  If a file does not specify tracks, the same implementation may be used for
  all track implementations the command is present in.

  Args:
    command_impls: A single or list of declarative command implementation(s).
  Yields:
    One implementation for each distinct track implmentation in a file.
  """
  if not isinstance(command_impls, list):
    command_impls = [command_impls]
  for impl in command_impls:
    release_tracks = impl.get(RELEASE_TRACKS)
    if not release_tracks:
      release_tracks = ['ALPHA', 'BETA', 'GA']
    for track in release_tracks:
      track_impl = copy.deepcopy(impl)
      try:
        _SetValuesForTrack(track_impl, track)
      except DoesNotExistForTrackError:
        # The implementation doesn't have any keys left.
        # continue
        pass
      track_impl[RELEASE_TRACKS] = [track]
      yield track_impl

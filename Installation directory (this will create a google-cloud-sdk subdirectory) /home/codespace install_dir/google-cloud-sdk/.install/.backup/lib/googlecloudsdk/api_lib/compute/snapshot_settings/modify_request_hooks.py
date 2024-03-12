# -*- coding: utf-8 -*- #
# Copyright 2023 Google Inc. All Rights Reserved.
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
"""Create request hook for snapshot settings."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import exceptions


def validate_single_location(_, args, req):
  """Validates that only a single location name is specified."""
  if args.storage_location_names is None:
    pass
  elif len(args.storage_location_names) != 1:
    raise exceptions.InvalidArgumentException(
        "only a single location name is permitted"
    )

  return req


def maybe_add_locations(version):
  """Adds locations to the request if they are specified."""
  messages = _get_message_module(version)

  def _maybe_add_locations(_, args, req):
    if not args.storage_location_names:
      return req

    locations_msg = (
        messages.SnapshotSettingsStorageLocationSettings.LocationsValue(
            additionalProperties=[
                _wrap_location_name(location, messages)
                for location in args.storage_location_names
            ]
        )
    )

    _ensure_location_field(req, messages)

    req.snapshotSettings.storageLocation.locations = locations_msg
    return req

  return _maybe_add_locations


def _wrap_location_name(location, messages):
  """Wraps a location name into the appropriate proto message."""

  return messages.SnapshotSettingsStorageLocationSettings.LocationsValue.AdditionalProperty(
      key=location,
      value=messages.SnapshotSettingsStorageLocationSettingsStorageLocationPreference(
          name=location
      ),
  )


def _get_message_module(version):
  """Returns the message module for the Compute API."""

  return apis.GetMessagesModule(
      "compute", apis.ResolveVersion("compute", version)
  )


def _ensure_location_field(req, messages):
  """Ensures that the location field is set."""

  if not req.snapshotSettings:
    req.snapshotSettings = messages.SnapshotSettings()

  if not req.snapshotSettings.storageLocation:
    req.snapshotSettings.storageLocation = (
        messages.SnapshotSettingsStorageLocationSettings()
    )


def adjust_storage_location_update_mask(_, args, req):
  """Adjusts the update mask for storage locations.

  If storage location policy is specified, then the update mask is adjusted so
  that the whole storage location structure is replaced.

  If a storage location name is specified, then the update mask is specified so
  that other storage location names are clearead.

  Args:
    _: this is ignored
    args: the parsed CLI args.
    req: the request message, partially populated.

  Returns:
    the request message with modified update mask.
  """
  if args.storage_location_policy:
    # if policy is specified, then whatever that is stored in storageLocation
    # needs to be cleared.
    req.updateMask = ",".join(
        _remove_all_storage_location_masks(req.updateMask) + ["storageLocation"]
    )
  elif args.storage_location_names:
    # In the similar vein, if a new storage location name is specified, other
    # locations need to be cleared.
    req.updateMask = ",".join(
        (
            mask
            for mask in req.updateMask.split(",")
            + ["storageLocation.locations"]
            if mask
        )
    )

  return req


def _remove_all_storage_location_masks(mask):
  return [
      mask
      for mask in mask.split(",")
      if mask and not mask.startswith("storageLocation")
  ]

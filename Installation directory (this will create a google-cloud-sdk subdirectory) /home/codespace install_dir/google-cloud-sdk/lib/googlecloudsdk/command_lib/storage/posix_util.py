# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""POSIX utilities for storage commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import datetime
import os
import stat

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.core import log
from googlecloudsdk.core.cache import function_result_cache
from googlecloudsdk.core.util import platforms

_MISSING_UID_FORMAT = (
    "UID in {} metadata doesn't exist on current system. UID: {}")
_MISSING_GID_FORMAT = (
    "GID in {} metadata doesn't exist on current system. GID: {}")
_INSUFFICIENT_USER_READ_ACCESS_FORMAT = (
    'Insufficient access to local destination to apply {}. User {} owns'
    ' file, but owner does not have read permission in mode {}.'
)
_INSUFFICIENT_GROUP_READ_ACCESS_FORMAT = (
    'Insufficient access to local destination to apply {}. Group {}'
    ' would own file, but group does not have read permission in mode {}.'
)
_INSUFFICIENT_OTHER_READ_ACCESS_FORMAT = (
    'Insufficient access to local destination to apply {}. UID {} is not'
    ' owner of file, and user is not in a group that owns the file. Users in'
    ' "other" category do not have read permission in mode {}.'
)

# For transporting POSIX info through an object's custom metadata.
ATIME_METADATA_KEY = 'goog-reserved-file-atime'
GID_METADATA_KEY = 'goog-reserved-posix-gid'
MODE_METADATA_KEY = 'goog-reserved-posix-mode'
MTIME_METADATA_KEY = 'goog-reserved-file-mtime'
UID_METADATA_KEY = 'goog-reserved-posix-uid'

_SECONDS_PER_DAY = 86400


def convert_base_ten_to_base_eight_str(base_ten_int):
  """Takes base ten integer, converts to octal, and removes extra chars."""
  # Example: 73 -> '0o111' -> '111'.
  # Remove leading '0o'.
  oct_string = oct(base_ten_int)[2:]
  # Take trailing three digits. For example, '0' -> '0' or '123' -> '11123'.
  permission_bytes = oct_string[-3:]
  # Add leading zero padding. For example, '1' -> '001'.
  return '0' * (3 - len(permission_bytes)) + permission_bytes


def convert_base_eight_str_to_base_ten_int(base_eight_str):
  """Takes string representing integer in octal and converts to base ten int."""
  # Example: '111' -> 73.
  return int(base_eight_str, 8)


class PosixMode:
  """Stores POSIX mode in all useful formats."""

  def __init__(self, base_ten_int, base_eight_str):
    """Initializes class. Prefer the 'from' constructors below."""
    self.base_ten_int = base_ten_int
    self.base_eight_str = base_eight_str

  @classmethod
  def from_base_ten_int(cls, base_ten_int):
    """Initializes class from base ten int. E.g. 73."""
    base_eight_str = convert_base_ten_to_base_eight_str(base_ten_int)
    # Not using original base_ten_int because str version removes unwanted bits.
    return PosixMode(
        convert_base_eight_str_to_base_ten_int(base_eight_str), base_eight_str)

  @classmethod
  def from_base_eight_str(cls, base_eight_str):
    """Initializes class from base eight (octal) string. E.g. '111'."""
    return PosixMode(
        convert_base_eight_str_to_base_ten_int(base_eight_str), base_eight_str)

  def __eq__(self, other):
    if not isinstance(other, type(self)):
      return NotImplemented
    return (self.base_ten_int == other.base_ten_int and
            self.base_eight_str == other.base_eight_str)

  def __repr__(self):
    return '(base-ten int: {}, base-eight str: {})'.format(
        self.base_ten_int, self.base_eight_str)


# Holds system-wide POSIX information.
#
# Attributes:
#   default_mode (PosixMode): The default permissions assigned to files.
#   user_groups (set): The set of Unix groups the user belongs to. Should
#     include one primary group and a variable number of secondary groups.
SystemPosixData = collections.namedtuple('SystemPosixData',
                                         ['default_mode', 'user_groups'])


def _get_default_mode():
  """Gets default permissions files are created with as PosixMode object."""
  # umask returns the permissions that should not be granted, so they must be
  # subtracted from the maximum set of permissions.
  max_permissions = 0o777
  # This call temporarily sets the process's umask to 177 while fetching the
  # the default umask. Not thread-safe. Run only in places where concurrent
  # file operations are not possible like a command surface.
  current_umask = os.umask(0o177)
  # Reset to the default umask.
  os.umask(current_umask)
  mode = max_permissions - current_umask
  # Files are not given execute privileges by default. Therefore we need to
  # subtract one from every odd permissions value. This is done via a bitmask.
  mode_without_execution = mode & 0o666
  return PosixMode.from_base_ten_int(mode_without_execution)


def _get_user_groups():
  """Gets set of POSIX groups the user is part of."""
  # POSIX modules and os.getuid not available on Windows.
  # pylint:disable=g-import-not-at-top
  import grp
  import pwd
  # pylint:enable=g-import-not-at-top
  user_id = os.getuid()
  user_name = pwd.getpwuid(user_id).pw_name
  return set(
      # Primary group.
      [pwd.getpwuid(user_id).pw_gid] +
      # Secondary groups.
      [g.gr_gid for g in grp.getgrall() if user_name in g.gr_mem])


@function_result_cache.lru(maxsize=1)
def get_system_posix_data():
  """Gets POSIX info that should only be fetched once."""
  if platforms.OperatingSystem.IsWindows():
    return SystemPosixData(None, None)

  default_mode = _get_default_mode()
  user_groups = _get_user_groups()
  return SystemPosixData(default_mode, user_groups)


def _raise_error_and_maybe_delete_file(error, delete_path):
  """Deletes file before raising error if file path provided."""
  if delete_path:
    os.remove(delete_path)
  raise error


def raise_if_invalid_file_permissions(
    system_posix_data,
    resource,
    delete_path=None,
    known_posix=None,
):
  """Detects permissions causing inaccessibility.

  Can delete invalid file.

  Args:
    system_posix_data (SystemPosixData): Helps determine if file will be made
      inaccessible in local environment.
    resource (ObjectResource): Contains URL used for messages and custom POSIX
      metadata used to determine if setting invalid file permissions.
    delete_path (str|None): If present, will delete file before raising error.
      Useful if file has been downloaded and needs to be cleaned up.
    known_posix (PosixAttributes|None): Use pre-parsed POSIX data instead of
      extracting from source. Not super important here because the source is a
      cloud object and doesn't require an `os.stat` call to harvest metadata,
      but it would be strange if we used `known_posix` for callers and only
      `resource` here, especially if the values were different (which they
      shouldn't be). Be careful using this because, if the data is wrong, it
      could mess with these safety checks.

  Raises:
    SystemPermissionError: Has explanatory message about issue.
  """
  _, _, uid, gid, mode = (
      known_posix or get_posix_attributes_from_cloud_resource(resource)
  )
  if (uid is gid is mode is None) or platforms.OperatingSystem.IsWindows():
    # If the user isn't setting anything, the system's new file defaults
    # are used, which we assume are valid.
    # Windows doesn't use POSIX for file permissions, so files will validate.
    return

  # POSIX modules, os.geteuid, and os.getuid not available on Windows.
  if os.geteuid() == 0:
    # The root user can access files regardless of their permissions.
    return

  # pylint:disable=g-import-not-at-top
  import grp
  import pwd
  # pylint:enable=g-import-not-at-top

  url_string = resource.storage_url.url_string
  if uid is not None:
    try:
      pwd.getpwuid(uid)
    except KeyError:
      error = errors.SystemPermissionError(
          _MISSING_UID_FORMAT.format(url_string, uid)
      )
      _raise_error_and_maybe_delete_file(error, delete_path)
  if gid is not None:
    try:
      grp.getgrgid(gid)
    except (KeyError, OverflowError):
      error = errors.SystemPermissionError(
          _MISSING_GID_FORMAT.format(url_string, gid)
      )
      _raise_error_and_maybe_delete_file(error, delete_path)

  if mode is None:
    mode_to_set = system_posix_data.default_mode
  else:
    mode_to_set = mode

  uid_to_set = uid or os.getuid()
  if uid is None or uid == os.getuid():
    # No UID causes system to default to current user as owner.
    # Owner permissions take priority over group and "other".
    if mode_to_set.base_ten_int & stat.S_IRUSR:
      return
    error = errors.SystemPermissionError(
        _INSUFFICIENT_USER_READ_ACCESS_FORMAT.format(
            url_string, uid_to_set, mode_to_set.base_eight_str
        )
    )
    _raise_error_and_maybe_delete_file(error, delete_path)

  if gid is None or gid in system_posix_data.user_groups:
    # No GID causes system to create file owned by user's primary group.
    # Group permissions take priority over "other" if user is member of group.
    if mode_to_set.base_ten_int & stat.S_IRGRP:
      return

    error = errors.SystemPermissionError(
        _INSUFFICIENT_GROUP_READ_ACCESS_FORMAT.format(
            url_string,
            '[user primary group]' if gid is None else gid,
            mode_to_set.base_eight_str,
        )
    )
    _raise_error_and_maybe_delete_file(error, delete_path)

  if mode_to_set.base_ten_int & stat.S_IROTH:
    # User is not owner and not in relevant group. User is "other".
    return
  error = errors.SystemPermissionError(
      _INSUFFICIENT_OTHER_READ_ACCESS_FORMAT.format(
          url_string, uid_to_set, mode_to_set.base_eight_str
      )
  )
  _raise_error_and_maybe_delete_file(error, delete_path)


# Holds custom POSIX information we may extract or apply to a file.
#
# "None" values typically mean using the system default.
#
# Attributes:
#   atime (int|None): File's access time in seconds since epoch.
#   mtime (int|None): File's modification time in seconds since epoch.
#   uid (int|None): The user ID marked as owning the file.
#   gid (int|None): The group ID marked as owning the file.
#   mode (PosixMode|None): Access permissions for the file.
PosixAttributes = collections.namedtuple(
    'PosixAttributes', ['atime', 'mtime', 'uid', 'gid', 'mode'])


def get_posix_attributes_from_file(file_path, preserve_symlinks=False):
  """Takes file path and returns PosixAttributes object."""
  follow_symlinks = (
      not preserve_symlinks or os.stat not in os.supports_follow_symlinks
  )
  mode, _, _, _, uid, gid, _, atime, mtime, _ = os.stat(
      file_path, follow_symlinks=follow_symlinks
  )
  return PosixAttributes(atime, mtime, uid, gid,
                         PosixMode.from_base_ten_int(mode))


def set_posix_attributes_on_file_if_valid(
    system_posix_data,
    source_resource,
    destination_resource,
    known_source_posix=None,
    known_destination_posix=None,
    preserve_symlinks=False,
):
  """Sets custom POSIX attributes on file if the final metadata will be valid.

  This function is typically called after downloads.
  `raise_if_invalid_file_permissions` should have been called before initiating
  a download, but we call it again here to be safe.

  Args:
    system_posix_data (SystemPosixData): System-wide POSIX. Helps fill in
      missing data and determine validity of result.
    source_resource (resource_reference.ObjectResource): Source resource with
      POSIX attributes to apply.
    destination_resource (resource_reference.FileObjectResource): Destination
      resource to apply POSIX attributes to.
    known_source_posix (PosixAttributes|None): Use pre-parsed POSIX data instead
      of extracting from source.
    known_destination_posix (PosixAttributes|None): Use pre-parsed POSIX data
      instead of extracting from destination.
    preserve_symlinks (bool): Whether symlinks should be preserved rather than
      followed.

  Raises:
    SystemPermissionError: Custom metadata asked for file ownership change that
      user did not have permission to perform. Other permission errors from
      OS functions are possible. Also see `raise_if_invalid_file_permissions`.
  """
  destination_path = destination_resource.storage_url.object_name
  raise_if_invalid_file_permissions(
      system_posix_data,
      source_resource,
      destination_path,
      known_posix=known_source_posix,
  )

  custom_posix_attributes = (
      known_source_posix
      or get_posix_attributes_from_cloud_resource(source_resource)
  )
  existing_posix_attributes = (
      known_destination_posix
      or get_posix_attributes_from_file(destination_path, preserve_symlinks)
  )

  if custom_posix_attributes.atime is None:
    atime = existing_posix_attributes.atime
    need_utime_call = False
  else:
    atime = custom_posix_attributes.atime
    need_utime_call = (
        custom_posix_attributes.atime != existing_posix_attributes.atime
    )
  if custom_posix_attributes.mtime is None:
    mtime = existing_posix_attributes.mtime
  else:
    mtime = custom_posix_attributes.mtime
    need_utime_call = (
        need_utime_call
        or custom_posix_attributes.mtime != existing_posix_attributes.mtime
    )

  # Don't follow symlinks if they're being preserved.
  if need_utime_call:
    follow_symlinks = (
        not preserve_symlinks or os.utime not in os.supports_follow_symlinks
    )
    os.utime(destination_path, (atime, mtime), follow_symlinks=follow_symlinks)

  if platforms.OperatingSystem.IsWindows():
    # Windows does not use the remaining POSIX attributes.
    return

  if custom_posix_attributes.uid is None:
    # Allow only valid UIDs.
    uid = existing_posix_attributes.uid
    need_chown_call = False
  else:
    uid = custom_posix_attributes.uid
    need_chown_call = (
        custom_posix_attributes.uid != existing_posix_attributes.uid
    )

    if uid != existing_posix_attributes.uid and os.geteuid() != 0:
      # Clean up file we can't set proper metadata on.
      os.remove(destination_path)
      # Custom may equal existing if user is uploading and downloading on the
      # same machine and account.
      raise errors.SystemPermissionError(
          'Root permissions required to set UID {}.'.format(uid)
      )

  if custom_posix_attributes.gid is None:
    gid = existing_posix_attributes.gid
  else:
    gid = custom_posix_attributes.gid
    need_chown_call = (
        need_chown_call
        or custom_posix_attributes.gid != existing_posix_attributes.gid
    )

  if need_chown_call:
    # Note: chown doesn't do anything for negative numbers like _INVALID_ID.
    follow_symlinks = (
        not preserve_symlinks or os.chown not in os.supports_follow_symlinks
    )
    os.chown(destination_path, uid, gid, follow_symlinks=follow_symlinks)

  if custom_posix_attributes.mode is not None and (
      custom_posix_attributes.mode.base_ten_int
      != existing_posix_attributes.mode.base_ten_int
  ):
    follow_symlinks = (
        not preserve_symlinks or os.chmod not in os.supports_follow_symlinks
    )
    os.chmod(
        destination_path,
        custom_posix_attributes.mode.base_ten_int,
        follow_symlinks=follow_symlinks,
    )


def _extract_time_from_custom_metadata(resource, key):
  """Finds, validates, and returns a POSIX time value."""
  if not resource.custom_fields or resource.custom_fields.get(key) is None:
    return None
  try:
    timestamp = int(resource.custom_fields[key])
  except ValueError:
    log.warning(
        '{} metadata did not contain a numeric value for {}: {}'.format(
            resource.storage_url.url_string, key, resource.custom_fields[key]
        )
    )
    return None
  if timestamp < 0:
    log.warning(
        'Found negative time value in {} metadata {}: {}'.format(
            resource.storage_url.url_string, key, resource.custom_fields[key]
        )
    )
    return None
  if (
      timestamp
      > datetime.datetime.now(datetime.timezone.utc).timestamp()
      + _SECONDS_PER_DAY
  ):
    log.warning(
        'Found {} value in {} metadata that is more than one day in the'
        ' future from the system time: {}'.format(
            key, resource.storage_url.url_string, resource.custom_fields[key]
        )
    )
    return None
  return timestamp


def _extract_id_from_custom_metadata(resource, key):
  """Finds, validates, and returns a POSIX ID value."""
  if not resource.custom_fields or resource.custom_fields.get(key) is None:
    return None
  try:
    posix_id = int(resource.custom_fields[key])
  except ValueError:
    log.warning(
        '{} metadata did not contain a numeric value for {}: {}'.format(
            resource.storage_url.url_string, key, resource.custom_fields[key]
        )
    )
    return None
  if posix_id < 0:
    log.warning(
        'Found negative ID value in {} metadata {}: {}'.format(
            resource.storage_url.url_string, key, resource.custom_fields[key]
        )
    )
    return None
  return posix_id


def _extract_mode_from_custom_metadata(resource):
  """Finds, validates, and returns a POSIX mode value."""
  if (
      not resource.custom_fields
      or resource.custom_fields.get(MODE_METADATA_KEY) is None
  ):
    return None
  try:
    return PosixMode.from_base_eight_str(
        resource.custom_fields[MODE_METADATA_KEY]
    )
  except ValueError:
    log.warning(
        '{} metadata did not contain a valid permissions octal string'
        ' for {}: {}'.format(
            resource.storage_url.url_string,
            MODE_METADATA_KEY,
            resource.custom_fields[MODE_METADATA_KEY],
        )
    )
  return None


def get_posix_attributes_from_cloud_resource(resource):
  """Parses metadata_dict and returns PosixAttributes.

  Note: This parses an object's *custom* metadata with user-set fields,
  not the full metadata with provider-set fields.

  Args:
    resource (ObjectResource): Contains URL to include in logged warnings and
      custom metadata to parse.

  Returns:
    PosixAttributes object populated from metadata_dict.
  """
  atime = _extract_time_from_custom_metadata(resource, ATIME_METADATA_KEY)
  mtime = _extract_time_from_custom_metadata(resource, MTIME_METADATA_KEY)
  uid = _extract_id_from_custom_metadata(resource, UID_METADATA_KEY)
  gid = _extract_id_from_custom_metadata(resource, GID_METADATA_KEY)
  mode = _extract_mode_from_custom_metadata(resource)
  return PosixAttributes(atime, mtime, uid, gid, mode)


def get_posix_attributes_from_resource(resource, preserve_symlinks=False):
  """Parses unknown resource type for POSIX data."""
  if isinstance(resource, resource_reference.ObjectResource):
    return get_posix_attributes_from_cloud_resource(resource)
  if isinstance(resource, resource_reference.FileObjectResource):
    return get_posix_attributes_from_file(
        resource.storage_url.object_name, preserve_symlinks
    )
  raise errors.InvalidUrlError(
      'Can only retrieve POSIX attributes from file or cloud'
      ' object, not: {}'.format(resource.TYPE_STRING)
  )


def update_custom_metadata_dict_with_posix_attributes(metadata_dict,
                                                      posix_attributes):
  """Updates custom metadata_dict with PosixAttributes data."""
  if posix_attributes.atime is not None:
    metadata_dict[ATIME_METADATA_KEY] = str(posix_attributes.atime)
  if posix_attributes.mtime is not None:
    metadata_dict[MTIME_METADATA_KEY] = str(posix_attributes.mtime)
  if posix_attributes.uid is not None:
    metadata_dict[UID_METADATA_KEY] = str(posix_attributes.uid)
  if posix_attributes.gid is not None:
    metadata_dict[GID_METADATA_KEY] = str(posix_attributes.gid)
  if posix_attributes.mode is not None:
    metadata_dict[MODE_METADATA_KEY] = posix_attributes.mode.base_eight_str


def raise_if_source_and_destination_not_valid_for_preserve_posix(
    source_url, destination_url
):
  """Logs errors and returns bool indicating if transfer is valid for POSIX."""
  if isinstance(source_url, storage_url.FileUrl) and source_url.is_stream:
    raise errors.InvalidUrlError(
        'Cannot preserve POSIX data from pipe: {}'.format(source_url)
    )
  if isinstance(destination_url,
                storage_url.FileUrl) and destination_url.is_stream:
    raise errors.InvalidUrlError(
        'Cannot write POSIX data to pipe: {}'.format(destination_url)
    )
  if isinstance(source_url, storage_url.CloudUrl) and isinstance(
      destination_url, storage_url.CloudUrl):
    raise errors.InvalidUrlError(
        'Cannot preserve POSIX data for cloud-to-cloud copies'
    )


def run_if_setting_posix(
    posix_to_set, user_request_args, function, *args, **kwargs
):
  """Useful for gating functions without repeating the below if statement."""
  if posix_to_set or (user_request_args and user_request_args.preserve_posix):
    return function(*args, **kwargs)
  return None

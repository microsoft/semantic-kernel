# -*- coding: utf-8 -*-
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Helper file for POSIX methods."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from calendar import timegm
import getpass
import logging
import os
import re
import time

import six

from gslib.exception import CommandException
from gslib.tz_utc import UTC
from gslib.utils.metadata_util import CreateCustomMetadata
from gslib.utils.metadata_util import GetValueFromObjectCustomMetadata
from gslib.utils.system_util import IS_WINDOWS
from gslib.utils.unit_util import SECONDS_PER_DAY

# pylint: disable=g-import-not-at-top
if not IS_WINDOWS:
  import grp
  import pwd

if six.PY3:
  long = int

# Metadata attribute names for POSIX attributes.
ATIME_ATTR = 'goog-reserved-file-atime'
GID_ATTR = 'goog-reserved-posix-gid'
MODE_ATTR = 'goog-reserved-posix-mode'
MTIME_ATTR = 'goog-reserved-file-mtime'
UID_ATTR = 'goog-reserved-posix-uid'
# NA_TIME is a long value that takes the place of any invalid mtime.
NA_TIME = -1
# NA_ID is a value that takes the place of any invalid POSIX UID or GID.
NA_ID = -1
# NA_MODE is an octal value that takes the place of any invalid POSIX file mode.
NA_MODE = -0o1

MODE_REGEX = re.compile('^[0-7]{3}$')

# POSIX Permissions Bit-masks
# User.
U_R = 0o400
U_W = 0o200
U_X = 0o100

# Group.
G_R = 0o040
G_W = 0o020
G_X = 0o010

# Other.
O_R = 0o004
O_W = 0o002
O_X = 0o001

# The permissions newly created files get by default.
SYSTEM_POSIX_MODE = None
# A list of group IDs that the current user is a member of.
USER_GROUPS = set()


class POSIXAttributes(object):
  """Class to hold POSIX attributes for a file/object."""

  def __init__(self,
               atime=NA_TIME,
               mtime=NA_TIME,
               uid=NA_ID,
               gid=NA_ID,
               mode=None):
    """Constructor for POSIXAttributes class which holds relevant data.

    Args:
      atime: The access time of the file/object.
      mtime: The modification time of the file/object.
      uid: The user ID that owns the file.
      gid: The group ID that the user is in.
      mode: An instance of POSIXMode.
    """
    self.atime = atime
    self.mtime = mtime
    self.uid = uid
    self.gid = gid
    self.mode = POSIXMode(mode if mode else NA_MODE)


class POSIXMode(object):

  def __init__(self, permissions):
    self.permissions = permissions


def ConvertModeToBase8(mode):
  """Converts a base-10 mode integer from os.stat to base-8."""
  # Strip out unnecessary bits in the mode. Mode is given as a base-10
  # integer. It must be converted to base-8.
  return int(oct(mode)[-3:])


def DeserializeFileAttributesFromObjectMetadata(obj_metadata, url_str):
  """Parses the POSIX attributes from the supplied metadata.

  Args:
    obj_metadata: The metadata for an object.
    url_str: File/object path that provides context if a warning is thrown.

  Returns:
    A POSIXAttribute object with the retrieved values or a default value for
    any attribute that could not be found.
  """
  posix_attrs = POSIXAttributes()
  # Parse atime.
  found, atime = GetValueFromObjectCustomMetadata(obj_metadata, ATIME_ATTR,
                                                  NA_TIME)
  try:
    atime = long(atime)
    if found and atime <= NA_TIME:
      WarnNegativeAttribute('atime', url_str)
      atime = NA_TIME
    elif atime > long(time.time()) + SECONDS_PER_DAY:
      WarnFutureTimestamp('atime', url_str)
      atime = NA_TIME
  except ValueError:
    WarnInvalidValue('atime', url_str)
    atime = NA_TIME
  posix_attrs.atime = atime
  # Parse gid.
  DeserializeIDAttribute(obj_metadata, GID_ATTR, url_str, posix_attrs)
  # Parse uid.
  DeserializeIDAttribute(obj_metadata, UID_ATTR, url_str, posix_attrs)
  found, mode = GetValueFromObjectCustomMetadata(obj_metadata, MODE_ATTR,
                                                 NA_MODE)
  if found and MODE_REGEX.match(mode):
    try:
      # Parse mode into a 3-digit base-8 number.
      posix_attrs.mode = POSIXMode(int(mode))
    except ValueError:
      WarnInvalidValue('mode', url_str)
  return posix_attrs


def SerializeFileAttributesToObjectMetadata(posix_attrs,
                                            custom_metadata,
                                            preserve_posix=False):
  """Takes a POSIXAttributes object and serializes it into custom metadata.

  Args:
    posix_attrs: A POSIXAttributes object.
    custom_metadata: A custom metadata object to serialize values into.
    preserve_posix: Whether or not to preserve POSIX attributes other than
                    mtime.
  """
  # mtime will always be needed in the object metadata for rsync.
  if posix_attrs.mtime != NA_TIME:
    CreateCustomMetadata(entries={MTIME_ATTR: posix_attrs.mtime},
                         custom_metadata=custom_metadata)
  # Only add other POSIX attributes if the preserve_posix flag is set.
  if preserve_posix:
    if posix_attrs.atime != NA_TIME:
      CreateCustomMetadata(entries={ATIME_ATTR: posix_attrs.atime},
                           custom_metadata=custom_metadata)
    if posix_attrs.uid != NA_ID:
      CreateCustomMetadata(entries={UID_ATTR: posix_attrs.uid},
                           custom_metadata=custom_metadata)
    if posix_attrs.gid != NA_ID:
      CreateCustomMetadata(entries={GID_ATTR: posix_attrs.gid},
                           custom_metadata=custom_metadata)
    if posix_attrs.mode.permissions != NA_MODE:
      CreateCustomMetadata(entries={MODE_ATTR: posix_attrs.mode.permissions},
                           custom_metadata=custom_metadata)


def DeserializeIDAttribute(obj_metadata, attr, url_str, posix_attrs):
  """Parses the POSIX attributes from the supplied metadata into posix_attrs.

  Args:
    obj_metadata: The metadata for an object.
    attr: Either GID_ATTR or UID_ATTR.
    url_str: File/object path that provides context if a warning is thrown.
    posix_attrs: POSIXAttribute object.
  """
  attr_name = attr.split('-')[-1]
  found, val = GetValueFromObjectCustomMetadata(obj_metadata, attr, NA_ID)
  try:
    val = int(val)
    if found and val <= NA_ID:
      WarnNegativeAttribute(attr_name, url_str)
      val = NA_ID
  except ValueError:
    WarnInvalidValue(attr_name, url_str)
    val = NA_ID
  setattr(posix_attrs, attr_name, val)


def NeedsPOSIXAttributeUpdate(src_atime, dst_atime, src_mtime, dst_mtime,
                              src_uid, dst_uid, src_gid, dst_gid, src_mode,
                              dst_mode):
  """Checks whether an update for any POSIX attribute is needed.

  Args:
    src_atime: The source access time.
    dst_atime: The destination access time.
    src_mtime: The source modification time.
    dst_mtime: The destination modification time.
    src_uid: The source user ID.
    dst_uid: The destination user ID.
    src_gid: The source group ID.
    dst_gid: The destination group ID.
    src_mode: The source mode.
    dst_mode: The destination mode.

  Returns:
    A tuple containing a POSIXAttribute object and a boolean for whether an
    update was needed.
  """
  posix_attrs = POSIXAttributes()
  has_src_atime = src_atime > NA_TIME
  has_dst_atime = dst_atime > NA_TIME
  has_src_mtime = src_mtime > NA_TIME
  has_dst_mtime = dst_mtime > NA_TIME
  has_src_uid = src_uid > NA_ID
  has_dst_uid = dst_uid > NA_ID
  has_src_gid = src_gid > NA_ID
  has_dst_gid = dst_gid > NA_ID
  has_src_mode = src_mode > NA_MODE
  has_dst_mode = dst_mode > NA_MODE
  if has_src_atime and not has_dst_atime:
    posix_attrs.atime = src_atime
  if has_src_mtime and not has_dst_mtime:
    posix_attrs.mtime = src_mtime
  if has_src_uid and not has_dst_uid:
    posix_attrs.uid = src_uid
  if has_src_gid and not has_dst_gid:
    posix_attrs.gid = src_gid
  if has_src_mode and not has_dst_mode:
    posix_attrs.mode.permissions = src_mode
  return posix_attrs, ((has_src_atime and not has_dst_atime) or
                       (has_src_mtime and not has_dst_mtime) or
                       (has_src_uid and not has_dst_uid) or
                       (has_src_gid and not has_dst_gid) or
                       (has_src_mode and not has_dst_mode))


def ValidatePOSIXMode(mode):
  """Validates whether the mode is valid.

  In order for the mode to be valid either the user, group, or other byte must
  be >= 4.

  Args:
    mode: The mode as a 3-digit, base-8 integer.

  Returns:
    True/False
  """
  return MODE_REGEX.match(oct(mode)[-3:]) and (mode & U_R or mode & G_R or
                                               mode & O_R)


def ValidateFilePermissionAccess(url_str, uid=NA_ID, gid=NA_ID, mode=NA_MODE):
  """Validates that the user has file access if uid, gid, and mode are applied.

  Args:
    url_str: The path to the object for which this is validating.
    uid: A POSIX user ID.
    gid: A POSIX group ID.
    mode: A 3-digit, number representing POSIX permissions, must be in base-8.

  Returns:
    A (bool, str) tuple, True if and only if it's safe to copy the file, and a
    string containing details for the error.
  """
  # Windows doesn't use the POSIX system for file permissions, so all files will
  # validate.
  if IS_WINDOWS:
    return True, ''

  uid_present = uid > NA_ID
  gid_present = int(gid) > NA_ID
  mode_present = mode > NA_MODE
  # No need to perform validation if Posix attrs are not being preserved.
  if not (uid_present or gid_present or mode_present):
    return True, ''

  # The root user on non-Windows systems can access files regardless of their
  # permissions.
  if os.geteuid() == 0:
    return True, ''

  mode_valid = ValidatePOSIXMode(int(str(mode), 8))
  if mode_present:
    if not mode_valid:
      return False, 'Mode for %s won\'t allow read access.' % url_str
  else:
    # Calculate the default mode if the mode doesn't exist.
    # Convert mode to a 3-digit, base-8 integer.
    mode = int(SYSTEM_POSIX_MODE)

  if uid_present:
    try:
      pwd.getpwuid(uid)
    except (KeyError, OverflowError):
      return (False, 'UID for %s doesn\'t exist on current system. uid: %d' %
              (url_str, uid))
  if gid_present:
    try:
      grp.getgrgid(gid)
    except (KeyError, OverflowError):
      return (False, 'GID for %s doesn\'t exist on current system. gid: %d' %
              (url_str, gid))

  # uid at this point must exist, but isn't necessarily the current user.
  # Likewise, gid must also exist at this point.
  uid_is_current_user = uid == os.getuid()

  # By this point uid and gid must exist on the system. However, the uid might
  # not match the current user's or the current user might not be a member of
  # the group identified by gid. In this case, the 'other' byte of the
  # permissions could provide sufficient access.
  mode = int(str(mode), 8)
  # Check that if the uid is not present and the gid and mode are, so that we
  # won't orphan the file. For example if the mode is set to 007, we can orphan
  # the file because the uid would default to the current user's ID and if the
  # current user wouldn't have read access or better, the file will be orphaned
  # even though they might otherwise have access through the gid or other bytes.
  if not uid_present and gid_present and mode_present and not bool(mode & U_R):
    return (False, 'Insufficient access with uid/gid/mode for %s, gid: %d, '
            'mode: %s' % (url_str, gid, oct(mode)[-3:]))
  if uid_is_current_user:
    valid = bool(mode & U_R)
    return (valid, '' if valid else
            'Insufficient access with uid/gid/mode for %s, uid: %d, '
            'mode: %s' % (url_str, uid, oct(mode)[-3:]))
  elif int(gid) in USER_GROUPS:
    valid = bool(mode & G_R)
    return (valid, '' if valid else
            'Insufficient access with uid/gid/mode for %s, gid: %d, '
            'mode: %s' % (url_str, gid, oct(mode)[-3:]))
  elif mode & O_R:
    return True, ''
  elif not uid_present and not gid_present and mode_valid:
    return True, ''
  return False, 'There was a problem validating %s.' % url_str


def ParseAndSetPOSIXAttributes(path,
                               obj_metadata,
                               is_rsync=False,
                               preserve_posix=False):
  """Parses POSIX attributes from obj_metadata and sets them.

  Attributes will only be set if they exist in custom metadata. This function
  should only be called after ValidateFilePermissionAccess has been called for
  the specific file/object so as not to orphan files.

  Args:
    path: The local filesystem path for the file. Valid metadata attributes will
          be set for the file located at path, some attributes will only be set
          if preserve_posix is set to True.
    obj_metadata: The metadata for the file/object.
    is_rsync: Whether or not the caller is the rsync command. Used to determine
              if timeCreated should be used.
    preserve_posix: Whether or not all POSIX attributes should be set.
  """
  if obj_metadata is None:
    # This exception is meant for debugging purposes as it should never be
    # thrown unless there are unexpected code changes.
    raise CommandException('obj_metadata cannot be None for %s' % path)
  try:
    found_at, atime = GetValueFromObjectCustomMetadata(obj_metadata,
                                                       ATIME_ATTR,
                                                       default_value=NA_TIME)
    found_mt, mtime = GetValueFromObjectCustomMetadata(obj_metadata,
                                                       MTIME_ATTR,
                                                       default_value=NA_TIME)
    found_uid, uid = GetValueFromObjectCustomMetadata(obj_metadata,
                                                      UID_ATTR,
                                                      default_value=NA_ID)
    found_gid, gid = GetValueFromObjectCustomMetadata(obj_metadata,
                                                      GID_ATTR,
                                                      default_value=NA_ID)
    found_mode, mode = GetValueFromObjectCustomMetadata(obj_metadata,
                                                        MODE_ATTR,
                                                        default_value=NA_MODE)
    if found_mt:
      mtime = long(mtime)
      if not preserve_posix:
        atime_tmp = os.stat(path).st_atime
        os.utime(path, (atime_tmp, mtime))
        return
    elif is_rsync:
      mtime = ConvertDatetimeToPOSIX(obj_metadata.timeCreated)
      os.utime(path, (mtime, mtime))

    if not preserve_posix:
      return

    if found_at:
      atime = long(atime)
    if atime > NA_TIME and mtime > NA_TIME:
      # Set both atime and mtime.
      os.utime(path, (atime, mtime))
    elif atime > NA_TIME and mtime <= NA_TIME:
      # atime is valid but mtime isn't.
      mtime_tmp = os.stat(path).st_mtime
      os.utime(path, (atime, mtime_tmp))
    elif atime <= NA_TIME and mtime > NA_TIME:
      # mtime is valid but atime isn't
      atime_tmp = os.stat(path).st_atime
      os.utime(path, (atime_tmp, mtime))
    if IS_WINDOWS:
      # Windows doesn't use POSIX uid/gid/mode unlike other systems. So there's
      # no point continuing.
      return
    # Only root can change ownership.
    if found_uid and os.geteuid() == 0:
      uid = int(uid)
    else:
      uid = NA_ID
    if found_gid:
      gid = int(gid)
    if uid > NA_ID and gid > NA_ID:
      # Set both uid and gid.
      os.chown(path, uid, gid)
    elif uid > NA_ID and gid <= NA_ID:
      # uid is valid but gid isn't.
      os.chown(path, uid, -1)
    elif uid <= NA_ID and gid > NA_ID:
      # gid is valid but uid isn't.
      os.chown(path, -1, gid)

    if found_mode:
      mode = int(str(mode), 8)
      os.chmod(path, mode)

  except ValueError:
    raise CommandException('Check POSIX attribute values for %s' %
                           obj_metadata.name)


def WarnNegativeAttribute(attr_name, url_str):
  """Logs if an attribute has a negative value.

  Args:
    attr_name: The name of the attribute to log.
    url_str: The path of the file for context.
  """
  logging.getLogger().warn('%s has a negative %s in its metadata', url_str,
                           attr_name)


def WarnInvalidValue(attr_name, url_str):
  """Logs if an attribute has an invalid value.

  Args:
    attr_name: The name of the attribute to log.
    url_str: The path of the file for context.
  """
  logging.getLogger().warn('%s has an invalid %s in its metadata', url_str,
                           attr_name)


def WarnFutureTimestamp(attr_name, url_str):
  """Logs if an attribute has an invalid value.

  Args:
    attr_name: The name of the attribute to log.
    url_str: The path of the file for context.
  """
  logging.getLogger().warn(
      '%s has an %s more than 1 day from current system'
      ' time', url_str, attr_name)


def ConvertDatetimeToPOSIX(dt):
  """Converts a datetime object to UTC and formats as POSIX.

  Sanitize the timestamp returned in dt, and put it in UTC format. For more
  information see the UTC class.

  Args:
    dt: A Python datetime object.

  Returns:
    A POSIX timestamp according to UTC.
  """
  return long(timegm(dt.replace(tzinfo=UTC()).timetuple()))


def InitializeDefaultMode():
  """Records the default POSIX mode using os.umask."""
  global SYSTEM_POSIX_MODE
  if IS_WINDOWS:
    # os.umask returns 0 on Windows. Below math works out to 666.
    SYSTEM_POSIX_MODE = '666'
    return
  # umask returns the permissions that should not be granted, so they must be
  # subtracted from the maximum set of permissions.
  max_permissions = 0o777
  current_umask = os.umask(0o177)
  os.umask(current_umask)
  mode = max_permissions - current_umask
  # Files are not given execute privileges by default. Therefore we need to
  # subtract one from every odd permissions value. This is done via a bitmask.
  SYSTEM_POSIX_MODE = oct(mode & 0o666)[-3:]


def InitializeUserGroups():
  """Initializes the set of groups that the user is in.

  Should only be called if the flag for preserving POSIX attributes is set.
  """
  global USER_GROUPS
  if IS_WINDOWS:
    return
  user_id = os.getuid()
  user_name = pwd.getpwuid(user_id).pw_name
  USER_GROUPS = set(
      # Primary group
      [pwd.getpwuid(user_id).pw_gid] +
      # Secondary groups
      [g.gr_gid for g in grp.getgrall() if user_name in g.gr_mem])


def InitializePreservePosixData():
  """Initializes POSIX data. Run once at the beginning of a copy."""
  InitializeDefaultMode()
  InitializeUserGroups()

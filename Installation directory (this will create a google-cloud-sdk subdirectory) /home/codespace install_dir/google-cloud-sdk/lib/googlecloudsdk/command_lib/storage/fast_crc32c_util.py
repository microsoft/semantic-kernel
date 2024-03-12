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
"""Utilities that augment the core CRC32C functionality for storage commands.

The core CRC32C utility provides a hashlib-like functionality for CRC32C
calculation but will at times fall back to a slow, all-Python implementation.
This utility provides several mitigation strategies to avoid relying on the slow
implementation of CRC32C, including adding a "deferred" strategy that uses the
component gcloud-crc32c on files after they are downloaded.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import struct
import textwrap

from googlecloudsdk.command_lib import info_holder
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.util import crc32c
# TODO(b/243537215) Should be loaded from a more generic location
from googlecloudsdk.command_lib.util.anthos import binary_operations
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


BINARY_NAME = 'gcloud-crc32c'


class GcloudCrc32cOperation(binary_operations.BinaryBackedOperation):
  """Operation for hashing a file using gcloud-crc32c."""

  def __init__(self, **kwargs):
    super(GcloudCrc32cOperation, self).__init__(binary=BINARY_NAME, **kwargs)

  def _ParseArgsForCommand(self, file_path, offset=0, length=0, **kwargs):
    return ['-o', str(offset), '-l', str(length), file_path]


class DeferredCrc32c(object):
  """Hashlib-like helper for deferring hash calculations to gcloud-crc32c.

  NOTE: Given this class relies on analyzing data on disk, it is not appropriate
  for hashing streaming downloads and will fail to work as expected.
  """

  def __init__(self, crc=0):
    """Sets up the internal checksum variable and allows an initial value.

    Args:
      crc (int): The initial checksum to be stored.
    """
    self._crc = crc

  def copy(self):
    return DeferredCrc32c(crc=self._crc)

  def update(self, data):
    # Does nothing so hash calculation can be deferred to sum_file.
    del data  # Unused.
    return

  def sum_file(self, file_path, offset, length):
    """Calculates checksum on a provided file path.

    Args:
      file_path (str): A string representing a path to a file.
      offset (int): The number of bytes to offset from the beginning of the
        file. Defaults to 0.
      length (int): The number of bytes to read into the file. If not specified
        will calculate until the end of file is encountered.
    """
    if offset is None or length is None:
      raise errors.Error(
          'gcloud_crc32c binary uses 0 (not `None`) to indicate'
          ' "no argument given."'
      )
    crc32c_operation = GcloudCrc32cOperation()
    result = crc32c_operation(file_path=file_path, offset=offset, length=length)
    self._crc = 0 if result.failed else int(result.stdout)

  def digest(self):
    """Returns the checksum in big-endian order, per RFC 4960.

    See: https://cloud.google.com/storage/docs/json_api/v1/objects#crc32c

    Returns:
      An eight-byte digest string.
    """
    return struct.pack('>L', self._crc)

  def hexdigest(self):
    """Returns a checksum like `digest` except as a bytestring of double length.

    Returns:
      A sixteen byte digest string, containing only hex digits.
    """
    return '{:08x}'.format(self._crc).encode('ascii')


def _is_gcloud_crc32c_installed():
  """Returns if gcloud-crc32c is installed and does not attempt install."""
  try:
    return BINARY_NAME in binary_operations.CheckForInstalledBinary(BINARY_NAME)
  except binary_operations.MissingExecutableException:
    return False


def _check_if_gcloud_crc32c_available(install_if_missing=False):
  """Returns True if gcloud-crc32c is installed and optionally installs."""
  try:
    return BINARY_NAME in binary_operations.CheckForInstalledBinary(
        BINARY_NAME, install_if_missing=install_if_missing
    )
  except binary_operations.MissingExecutableException:
    # Failed because user has access to gcloud components but opted not to
    # install or the user doesn't have access to the gcloud components manager.
    # This property will prevent automatic installation in the future, but it
    # won't prevent gcloud-crc32c from being used if later installed separately.
    properties.VALUES.storage.use_gcloud_crc32c.Set(False)
  except:  # pylint: disable=bare-except
    # Other errors that happen during installation checks aren't fatal.
    pass
  return False


def check_if_will_use_fast_crc32c(install_if_missing=False):
  return crc32c.IS_FAST_GOOGLE_CRC32C_AVAILABLE or (
      # pylint:disable=g-bool-id-comparison
      properties.VALUES.storage.use_gcloud_crc32c.GetBool() is not False
      # pylint:enable=g-bool-id-comparison
      and _check_if_gcloud_crc32c_available(install_if_missing)
  )


def should_use_gcloud_crc32c(install_if_missing=False):
  """Returns True if gcloud-crc32c should be used and installs if needed.

  Args:
    install_if_missing (bool): Install gcloud-crc32c if not already present.

  Returns:
    True if the Go binary gcloud-crc32c should be used.
  """
  user_wants_gcloud_crc32c = (
      properties.VALUES.storage.use_gcloud_crc32c.GetBool())
  # pylint:disable=g-bool-id-comparison
  if user_wants_gcloud_crc32c is False:
    # pylint:enable=g-bool-id-comparison
    return False
  if (user_wants_gcloud_crc32c is None and
      crc32c.IS_FAST_GOOGLE_CRC32C_AVAILABLE):
    # User has no preference, and we can rely on google-crc32c module.
    return False
  if install_if_missing:
    return _check_if_gcloud_crc32c_available(install_if_missing=True)
  return _is_gcloud_crc32c_installed()


def get_crc32c(initial_data=b''):
  """Wraps the crc32c.get_crc32c() method to allow fallback to gcloud-crc32c.

  DO NOT USE for streaming downloads, as this relies on file-based hashing and
  does not take whether or not streaming is enabled into account.

  Args:
    initial_data (bytes): The CRC32C object will be initialized with the
      checksum of the data.

  Returns:
    A DeferredCrc32c instance if hashing can be deferred. Otherwise it returns a
    google_crc32c.Checksum instance if google-crc32c
    (https://github.com/googleapis/python-crc32c) is available and a
    predefined.Crc instance from crcmod library if not.
  """
  should_defer = should_use_gcloud_crc32c(install_if_missing=True)
  return DeferredCrc32c() if should_defer else crc32c.get_crc32c(initial_data)


def get_google_crc32c_install_command():
  """Returns the command to install google-crc32c library.

  This will typically only be called if gcloud-crc32c is missing and can't be
  installed for some reason. It requires user intervention which is why it's
  not a preferred option.
  """
  sdk_info = info_holder.InfoHolder()
  sdk_root = sdk_info.installation.sdk_root
  if sdk_root:
    third_party_path = os.path.join(sdk_root, 'lib', 'third_party')
    return '{} -m pip install google-crc32c --upgrade --target {}'.format(
        sdk_info.basic.python_location, third_party_path)
  return None


def _get_hash_check_warning_base():
  """CRC32C warnings share this text."""
  # Create the text in a function so that we can test it easily.
  google_crc32c_install_step = get_google_crc32c_install_command()
  gcloud_crc32c_install_step = 'gcloud components install gcloud-crc32c'
  return textwrap.dedent(
      """\
      This copy {{}} since fast hash calculation tools
      are not installed. You can change this by running:
      \t$ {crc32c_step}
      You can also modify the "storage/check_hashes" config setting.""".format(
          crc32c_step=google_crc32c_install_step
          if google_crc32c_install_step
          else gcloud_crc32c_install_step
      )
  )


_HASH_CHECK_WARNING_BASE = _get_hash_check_warning_base()
_NO_HASH_CHECK_WARNING = _HASH_CHECK_WARNING_BASE.format(
    'will not be validated'
)
_SLOW_HASH_CHECK_WARNING = _HASH_CHECK_WARNING_BASE.format('may be slow')
_NO_HASH_CHECK_ERROR = _HASH_CHECK_WARNING_BASE.format('was skipped')


def log_or_raise_crc32c_issues(warn_for_always=True):
  """Informs user about slow hashing if requested.

  Args:
    warn_for_always (bool): User may not want to see a warning about slow hashes
      if they have the "always check hashes" property set because (1) they
      intentionally set a property and (2) it could duplicate a warning in
      FileDownloadTask.

  Raises:
    errors.Error: IF_FAST_ELSE_FAIL set, and CRC32C binary not present. See
      error message for more details.
  """
  if check_if_will_use_fast_crc32c(install_if_missing=True):
    return

  check_hashes = properties.VALUES.storage.check_hashes.Get()
  if check_hashes == properties.CheckHashes.ALWAYS.value and warn_for_always:
    log.warning(_SLOW_HASH_CHECK_WARNING)
  elif check_hashes == properties.CheckHashes.IF_FAST_ELSE_SKIP.value:
    log.warning(_NO_HASH_CHECK_WARNING)
  elif check_hashes == properties.CheckHashes.IF_FAST_ELSE_FAIL.value:
    raise errors.Error(_NO_HASH_CHECK_ERROR)

# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Utilities for representing a part of a stream."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.core.updater import installers

_PROGRESS_CALLBACK_THRESHOLD = 16777216  # 16 MiB in bytes.


class UploadStream:
  """Implements a subset of the io.IOBase API, adding functionality for uploads.

  When data is read from a stream, this class
  1. Updates hash digesters.
  2. Executes a progress callbacks if a byte threshold is passed.
  """

  def __init__(self,
               stream,
               length=None,
               digesters=None,
               progress_callback=None):
    """Initializes a FilePart instance.

    Args:
      stream (io.IOBase): The underlying stream wrapped by this class.
      length (int|None): The total number of bytes in the UploadStream.
      digesters (dict[util.HashAlgorithm, hashlib hash object]|None): Values are
        updated with with data as it's read.
      progress_callback (func[int]|None): Accepts an amount of processed bytes
        and submits progress information for aggregation.
    """
    self._stream = stream
    self._length = length
    self._digesters = digesters if digesters is not None else {}
    self._progress_callback = progress_callback

    self._bytes_read_since_last_progress_callback = 0
    self._progress_updated_with_end_byte = False
    self._checkpoint_digesters = None
    self._checkpoint_absolute_index = 0

    self._start_byte = 0

  def _get_absolute_position(self):
    """Returns absolute position in the stream.

    Hashing and progress reporting logic relies on absolute positions. Since
    child classes overwrite `tell` to make it return relative positions, we need
    to write hashing and progress reporting in a way that does not reference
    `self.tell`, which this function makes possible.
    """
    return self._stream.tell()

  def _update_absolute_position(self, offset):
    """Seeks to a position in the underlying stream.

    Catching up digesters sometimes requires seeking to a specific position in
    self._stream. Child classes wrap streams which are not seekable, and have
    different strategies to make it appear that a seek has occured, which can
    be supported by overriding this method.

    Args:
      offset (int): the position to seek to.

    Returns:
      the new position in the stream.
    """
    return self._stream.seek(offset)

  def _get_data(self, size=-1):
    """Reads bytes from the underlying stream.

    Child classes do not always read directly from the stream. Progress
    reporting and hashing logic can be reused by overriding only this method.

    Args:
      size (int): the number of bytes to read. If less than 0, all bytes are
          returned.

    Returns:
      bytes from self._stream.
    """
    return self._stream.read(size)

  def _save_digesters_checkpoint(self):
    """Updates checkpoint that holds old hashes to optimize backwards seeks."""
    if not self._digesters:
      return
    self._checkpoint_absolute_index = self._get_absolute_position()
    self._checkpoint_digesters = hash_util.copy_digesters(self._digesters)

  def _catch_up_digesters(self, new_absolute_index):
    """Digests data between last and current stream position."""
    if not self._digesters:
      return
    if new_absolute_index < self._checkpoint_absolute_index:
      # Case 1: New position < Checkpoint position < Old position.
      self._update_absolute_position(self._start_byte)
      hash_util.reset_digesters(self._digesters)
    elif new_absolute_index < self._get_absolute_position():
      # Case 2: Checkpoint position < New position < Old position.
      self._update_absolute_position(self._checkpoint_absolute_index)

      # The instantiator of this class expects the digesters dictionary it
      # passes to the initializer to contain updated digests. To handle backward
      # seeks we replace the current digester in that dictionary with their
      # values at the last checkpoint.
      self._digesters.update(self._checkpoint_digesters)
      self._checkpoint_digesters = hash_util.copy_digesters(
          self._checkpoint_digesters)
    elif new_absolute_index == self._get_absolute_position():
      # Case 3: Old position == New position.
      return
    # Case 4: Old position < New position.
    # Below digester updates are sufficient.

    self._save_digesters_checkpoint()
    while True:
      data = self._get_data(
          min(new_absolute_index - self._get_absolute_position(),
              installers.WRITE_BUFFER_SIZE))
      if not data:
        break
      hash_util.update_digesters(self._digesters, data)

  def tell(self):
    """Returns the current position in the stream."""
    return self._get_absolute_position()

  def read(self, size=-1):
    """Returns `size` bytes from the underlying stream."""
    self._save_digesters_checkpoint()
    data = self._get_data(size)
    if data:
      hash_util.update_digesters(self._digesters, data)
      if self._progress_callback:
        self._bytes_read_since_last_progress_callback += len(data)
        if (self._bytes_read_since_last_progress_callback >=
            _PROGRESS_CALLBACK_THRESHOLD):
          self._bytes_read_since_last_progress_callback = 0
          self._progress_callback(self._get_absolute_position())
          self._progress_updated_with_end_byte = self.tell() == self._length

    return data

  def seek(self, offset, whence=os.SEEK_SET):
    """Goes to a specific point in the stream.

    Args:
      offset (int): The number of bytes to move.
      whence: Specifies the position offset is added to.
        os.SEEK_SET: offset is added to the current byte.
        os.SEEK_END, os.SEEK_CUR are not supported.

    Returns:
      The new position in the stream (int).
    """
    if whence == os.SEEK_END:
      if self._length:
        new_absolute_index = offset + self._length
      else:
        raise errors.Error(
            'SEEK_END is not supported if the length of the stream is unknown.')
    elif whence == os.SEEK_CUR:
      new_absolute_index = self._get_absolute_position() + offset
    else:
      new_absolute_index = offset

    self._catch_up_digesters(new_absolute_index)
    # Above may perform seek, but repeating is harmless.
    return self._update_absolute_position(new_absolute_index)

  def close(self, caught_error=False):
    """Closes the underlying stream."""
    if (self._progress_callback and not self._progress_updated_with_end_byte):
      if not caught_error:
        self._progress_callback(self._get_absolute_position())
      self._progress_updated_with_end_byte = True
    return self._stream.close()

  def __enter__(self):
    return self

  def __exit__(self, error_type, *unused_args):
    self.close(caught_error=bool(error_type))

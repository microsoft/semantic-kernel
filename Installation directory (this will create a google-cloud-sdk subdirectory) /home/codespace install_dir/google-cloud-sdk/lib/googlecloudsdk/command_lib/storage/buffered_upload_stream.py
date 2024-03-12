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

"""Implements a file wrapper used for in-flight retries of streaming uploads."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import os

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import hash_util
from googlecloudsdk.command_lib.storage import upload_stream


class BufferedUploadStream(upload_stream.UploadStream):
  """Supports limited seeking within a non-seekable stream by buffering data."""

  def __init__(self,
               stream,
               max_buffer_size,
               digesters=None,
               progress_callback=None):
    """Initializes a FilePart instance.

    Args:
      stream (io.IOBase): The underlying stream wrapped by this class.
      max_buffer_size: Maximum size of the internal buffer. This should be >= to
          the chunk size used by the API to execute streaming uploads to ensure
          that at least one full chunk write can be repeated in the event of a
          server error.
      digesters (dict[util.HashAlgorithm, hashlib hash object]|None): See super
        class.
      progress_callback (func[int]|None): See super class.
    """
    super(__class__, self).__init__(
        stream=stream,
        length=None,
        digesters=digesters,
        progress_callback=progress_callback)

    self._buffer = collections.deque()
    self._max_buffer_size = max_buffer_size
    self._buffer_start = 0
    self._position = 0
    self._buffer_end = 0

    self._checkpoint_digesters = hash_util.copy_digesters(self._digesters)

  def _get_absolute_position(self):
    return self._position

  def _update_absolute_position(self, offset):
    self._position = offset

  def _read_from_buffer(self, amount):
    """Get any buffered data required to complete a read.

    If a backward seek has not happened, the buffer will never contain any
    information needed to complete a read call. Return the empty string in
    these cases.

    If the current position is before the end of the buffer, some of the
    requested bytes will be in the buffer. For example, if our position is 1,
    five bytes are being read, and the buffer contains b'0123', we will return
    b'123'. Two additional bytes will be read from the stream at a later stage.

    Args:
      amount (int): The total number of bytes to be read

    Returns:
      A byte string, the length of which is equal to `amount` if there are
      enough buffered bytes to complete the read, or less than `amount` if there
      are not.
    """
    buffered_data = []
    bytes_remaining = amount
    if self._position < self._buffer_end:
      # There was a backward seek, so read from the buffer.
      position_in_buffer = self._buffer_start
      for data in self._buffer:
        if position_in_buffer + len(data) >= self._position:
          offset_from_position = self._position - position_in_buffer
          bytes_to_read_this_block = len(data) - offset_from_position
          read_size = min(bytes_to_read_this_block, bytes_remaining)
          buffered_data.append(data[offset_from_position:offset_from_position +
                                    read_size])
          bytes_remaining -= read_size
          self._position += read_size
        position_in_buffer += len(data)
    return b''.join(buffered_data)

  def _save_digesters_checkpoint(self):
    """Disables parent class digester checkpointing behavior.

    To guarantee that seeks within the buffer are possible, we need to ensure
    that the checkpoint is aligned with the buffer's start_byte. This is not
    possible if we save digester checkpoints when the parent class does so.
    """
    pass

  def _store_data(self, data):
    """Adds data to the buffer, respecting max_buffer_size.

    The buffer can consist of many different blocks of data, e.g.

      [b'0', b'12', b'3']

    With a maximum size of 4, if we read two bytes, we must discard the oldest
    data and keep half of the second-oldest block:

      [b'2', b'3', b'45']

    Args:
      data (bytes): the data being added to the buffer.
    """
    if data:
      self._buffer.append(data)
      self._buffer_end += len(data)
      oldest_data = None
      while self._buffer_end - self._buffer_start > self._max_buffer_size:
        oldest_data = self._buffer.popleft()
        self._buffer_start += len(oldest_data)
        if oldest_data:
          refill_amount = self._max_buffer_size - (
              self._buffer_end - self._buffer_start)
          if refill_amount >= 1:
            self._buffer.appendleft(oldest_data[-refill_amount:])
            self._buffer_start -= refill_amount

          # Ensure checkpoint digesters always start at the beginning of the
          # buffer.
          hash_util.update_digesters(
              self._checkpoint_digesters,
              oldest_data[:len(oldest_data) - refill_amount])
          self._checkpoint_absolute_index = self._buffer_start

  def _get_data(self, size=-1):
    """Reads from the wrapped stream.

    Args:
      size: The amount of bytes to read. If omitted or negative, the entire
          stream will be read and returned.

    Returns:
      Bytes from the wrapped stream.
    """
    read_all_bytes = size is None or size < 0
    if read_all_bytes:
      # Ensures everything is read from the buffer.
      bytes_remaining = self._max_buffer_size
    else:
      bytes_remaining = size

    data = self._read_from_buffer(bytes_remaining)
    bytes_remaining -= len(data)

    if read_all_bytes:
      new_data = super(__class__, self)._get_data(-1)
    elif bytes_remaining:
      new_data = super(__class__, self)._get_data(bytes_remaining)
    else:
      new_data = b''

    self._position += len(new_data)
    self._store_data(new_data)

    return data + new_data

  def seek(self, offset, whence=os.SEEK_SET):
    """Seeks within the buffered stream."""
    if whence == os.SEEK_SET:
      if offset < self._buffer_start or offset > self._buffer_end:
        raise errors.Error(
            'Unable to recover from an upload error because limited buffering'
            ' is available for streaming uploads. Offset {} was requested, but'
            ' only data from {} to {} is buffered.'.format(
                offset, self._buffer_start, self._buffer_end))
      new_position = offset
    elif whence == os.SEEK_END:
      # Offset is typically negative with SEEK_END, as it sets the position left
      # of the end of the stream.
      if abs(offset) > self._max_buffer_size:
        raise errors.Error(
            'Invalid SEEK_END offset {} on streaming upload. Only {} bytes'
            ' can be buffered.'.format(offset, self._max_buffer_size))

      while self.read(self._max_buffer_size):
        pass
      new_position = self._position + offset
    else:
      raise errors.Error(
          'Invalid seek mode on streaming upload. Mode: {}, offset: {}'.format(
              whence, offset))
    self._catch_up_digesters(new_position)
    self._position = new_position

  def seekable(self):
    """Indicates that this stream is not seekable.

    Needed so that boto3 can correctly identify how to treat this stream.
    The library attempts to seek to the beginning after an upload completes,
    which is not always possible.

    Apitools does not check the return value of this method, so it will not
    raise issues for resumable uploads.

    Returns:
      False
    """
    return False

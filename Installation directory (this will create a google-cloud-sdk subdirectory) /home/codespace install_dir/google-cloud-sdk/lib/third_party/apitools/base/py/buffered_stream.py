#!/usr/bin/env python
#
# Copyright 2015 Google Inc.
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

"""Small helper class to provide a small slice of a stream.

This class reads ahead to detect if we are at the end of the stream.
"""

from apitools.base.py import exceptions


# TODO(user): Consider replacing this with a StringIO.
class BufferedStream(object):

    """Buffers a stream, reading ahead to determine if we're at the end."""

    def __init__(self, stream, start, size):
        self.__stream = stream
        self.__start_pos = start
        self.__buffer_pos = 0
        self.__buffered_data = self.__stream.read(size)
        self.__stream_at_end = len(self.__buffered_data) < size
        self.__end_pos = self.__start_pos + len(self.__buffered_data)

    def __str__(self):
        return ('Buffered stream %s from position %s-%s with %s '
                'bytes remaining' % (self.__stream, self.__start_pos,
                                     self.__end_pos, self._bytes_remaining))

    def __len__(self):
        return len(self.__buffered_data)

    @property
    def stream_exhausted(self):
        return self.__stream_at_end

    @property
    def stream_end_position(self):
        return self.__end_pos

    @property
    def _bytes_remaining(self):
        return len(self.__buffered_data) - self.__buffer_pos

    def read(self, size=None):  # pylint: disable=invalid-name
        """Reads from the buffer."""
        if size is None or size < 0:
            raise exceptions.NotYetImplementedError(
                'Illegal read of size %s requested on BufferedStream. '
                'Wrapped stream %s is at position %s-%s, '
                '%s bytes remaining.' %
                (size, self.__stream, self.__start_pos, self.__end_pos,
                 self._bytes_remaining))

        data = ''
        if self._bytes_remaining:
            size = min(size, self._bytes_remaining)
            data = self.__buffered_data[
                self.__buffer_pos:self.__buffer_pos + size]
            self.__buffer_pos += size
        return data

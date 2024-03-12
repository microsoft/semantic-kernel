#!/usr/bin/env python
#
# Copyright 2017 Google Inc.
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

"""Compression support for apitools."""

from collections import deque

from apitools.base.py import gzip

__all__ = [
    'CompressStream',
]


# pylint: disable=invalid-name
# Note: Apitools only uses the default chunksize when compressing.
def CompressStream(in_stream, length=None, compresslevel=2,
                   chunksize=16777216):

    """Compresses an input stream into a file-like buffer.

    This reads from the input stream until either we've stored at least length
    compressed bytes, or the input stream has been exhausted.

    This supports streams of unknown size.

    Args:
        in_stream: The input stream to read from.
        length: The target number of compressed bytes to buffer in the output
            stream. If length is none, the input stream will be compressed
            until it's exhausted.

            The actual length of the output buffer can vary from the target.
            If the input stream is exhaused, the output buffer may be smaller
            than expected. If the data is incompressible, the maximum length
            can be exceeded by can be calculated to be:

              chunksize + 5 * (floor((chunksize - 1) / 16383) + 1) + 17

            This accounts for additional header data gzip adds. For the default
            16MiB chunksize, this results in the max size of the output buffer
            being:

              length + 16Mib + 5142 bytes

        compresslevel: Optional, defaults to 2. The desired compression level.
        chunksize: Optional, defaults to 16MiB. The chunk size used when
            reading data from the input stream to write into the output
            buffer.

    Returns:
        A file-like output buffer of compressed bytes, the number of bytes read
        from the input stream, and a flag denoting if the input stream was
        exhausted.
    """
    in_read = 0
    in_exhausted = False
    out_stream = StreamingBuffer()
    with gzip.GzipFile(mode='wb',
                       fileobj=out_stream,
                       compresslevel=compresslevel) as compress_stream:
        # Read until we've written at least length bytes to the output stream.
        while not length or out_stream.length < length:
            data = in_stream.read(chunksize)
            data_length = len(data)
            compress_stream.write(data)
            in_read += data_length
            # If we read less than requested, the stream is exhausted.
            if data_length < chunksize:
                in_exhausted = True
                break
    return out_stream, in_read, in_exhausted


class StreamingBuffer(object):

    """Provides a file-like object that writes to a temporary buffer.

    When data is read from the buffer, it is permanently removed. This is
    useful when there are memory constraints preventing the entire buffer from
    being stored in memory.
    """

    def __init__(self):
        # The buffer of byte arrays.
        self.__buf = deque()
        # The number of bytes in __buf.
        self.__size = 0

    def __len__(self):
        return self.__size

    def __nonzero__(self):
        # For 32-bit python2.x, len() cannot exceed a 32-bit number; avoid
        # accidental len() calls from httplib in the form of "if this_object:".
        return bool(self.__size)

    @property
    def length(self):
        # For 32-bit python2.x, len() cannot exceed a 32-bit number.
        return self.__size

    def write(self, data):
        # Gzip can write many 0 byte chunks for highly compressible data.
        # Prevent them from being added internally.
        if data is not None and data:
            self.__buf.append(data)
            self.__size += len(data)

    def read(self, size=None):
        """Read at most size bytes from this buffer.

        Bytes read from this buffer are consumed and are permanently removed.

        Args:
          size: If provided, read no more than size bytes from the buffer.
            Otherwise, this reads the entire buffer.

        Returns:
          The bytes read from this buffer.
        """
        if size is None:
            size = self.__size
        ret_list = []
        while size > 0 and self.__buf:
            data = self.__buf.popleft()
            size -= len(data)
            ret_list.append(data)
        if size < 0:
            ret_list[-1], remainder = ret_list[-1][:size], ret_list[-1][size:]
            self.__buf.appendleft(remainder)
        ret = b''.join(ret_list)
        self.__size -= len(ret)
        return ret

# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
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
"""FilePart implementation for representing part of a file."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import io


class FilePart(io.IOBase):
  """Subclass of the file API for representing part of a file.

  This class behaves as a contiguous subset of a given file (e.g., this object
  will behave as though the desired part of the file was written to another
  file, and the second file was opened).
  """

  # pylint: disable=super-init-not-called
  def __init__(self, filename, offset, length):
    """Initializes the FilePart.

    Args:
      filename: The name of the existing file, of which this object represents
                a part.
      offset: The position (in bytes) in the original file that corresponds to
              the first byte of the FilePart.
      length: The total number of bytes in the FilePart.
    """
    self._fp = open(filename, 'rb')
    self.length = length
    self._start = offset
    self._end = self._start + self.length
    self._fp.seek(self._start)

  def __enter__(self):
    pass

  # pylint: disable=redefined-builtin
  def __exit__(self, type, value, traceback):
    self.close()

  def tell(self):
    return self._fp.tell() - self._start

  def read(self, size=-1):
    if size < 0:
      size = self.length
    size = min(size, self._end - self._fp.tell())  # Only read to our EOF
    return self._fp.read(max(0, size))

  def seek(self, offset, whence=os.SEEK_SET):
    if whence == os.SEEK_END:
      return self._fp.seek(offset + self._end)
    elif whence == os.SEEK_CUR:
      return self._fp.seek(offset, whence)
    else:
      return self._fp.seek(self._start + offset)

  def close(self):
    self._fp.close()

  def flush(self, size=None):
    raise NotImplementedError('flush is not implemented in FilePart.')

  def fileno(self, size=None):
    raise NotImplementedError('fileno is not implemented in FilePart.')

  def isatty(self, size=None):
    raise NotImplementedError('isatty is not implemented in FilePart.')

  def next(self, size=None):
    raise NotImplementedError('next is not implemented in FilePart.')

  def readline(self, size=None):
    raise NotImplementedError('readline is not implemented in FilePart.')

  def readlines(self, size=None):
    raise NotImplementedError('readlines is not implemented in FilePart.')

  def xreadlines(self, size=None):
    raise NotImplementedError('xreadlines is not implemented in FilePart.')

  def truncate(self, size=None):
    raise NotImplementedError('truncate is not implemented in FilePart.')

  def write(self, size=None):
    raise NotImplementedError('write is not implemented in FilePart.')

  def writelines(self, size=None):
    raise NotImplementedError('writelines is not implemented in FilePart.')

# Copyright 2013 Google Inc.
# Copyright 2011, Nexenta Systems Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.

"""
Wrapper class to expose a Key being read via a partial implementaiton of the
Python file interface. The only functions supported are those needed for seeking
in a Key open for reading.
"""

import os
from boto.exception import StorageResponseError

class KeyFile():

  def __init__(self, key):
    self.key = key
    self.key.open_read()
    self.location = 0
    self.closed = False
    self.softspace = -1 # Not implemented.
    self.mode = 'r'
    self.encoding = 'Undefined in KeyFile'
    self.errors = 'Undefined in KeyFile'
    self.newlines = 'Undefined in KeyFile'
    self.name = key.name

  def tell(self):
    if self.location is None:
      raise ValueError("I/O operation on closed file")
    return self.location

  def seek(self, pos, whence=os.SEEK_SET):
    self.key.close(fast=True)
    if whence == os.SEEK_END:
      # We need special handling for this case because sending an HTTP range GET
      # with EOF for the range start would cause an invalid range error. Instead
      # we position to one before EOF (plus pos) and then read one byte to
      # position at EOF.
      if self.key.size == 0:
        # Don't try to seek with an empty key.
        return
      pos = self.key.size + pos - 1
      if pos < 0:
        raise IOError("Invalid argument")
      self.key.open_read(headers={"Range": "bytes=%d-" % pos})
      self.key.read(1)
      self.location = pos + 1
      return

    if whence == os.SEEK_SET:
      if pos < 0:
        raise IOError("Invalid argument")
    elif whence == os.SEEK_CUR:
      pos += self.location
    else:
      raise IOError('Invalid whence param (%d) passed to seek' % whence)
    try:
      self.key.open_read(headers={"Range": "bytes=%d-" % pos})
    except StorageResponseError as e:
      # 416 Invalid Range means that the given starting byte was past the end
      # of file. We catch this because the Python file interface allows silently
      # seeking past the end of the file.
      if e.status != 416:
        raise

    self.location = pos

  def read(self, size):
    self.location += size
    return self.key.read(size)

  def close(self):
    self.key.close()
    self.location = None
    self.closed = True

  def isatty(self):
    return False

  # Non-file interface, useful for code that wants to dig into underlying Key
  # state.
  def getkey(self):
    return self.key

  # Unimplemented interfaces below here.

  def write(self, buf):
    raise NotImplementedError('write not implemented in KeyFile')

  def fileno(self):
    raise NotImplementedError('fileno not implemented in KeyFile')

  def flush(self):
    raise NotImplementedError('flush not implemented in KeyFile')

  def next(self):
    raise NotImplementedError('next not implemented in KeyFile')

  def readinto(self):
    raise NotImplementedError('readinto not implemented in KeyFile')

  def readline(self):
    raise NotImplementedError('readline not implemented in KeyFile')

  def readlines(self):
    raise NotImplementedError('readlines not implemented in KeyFile')

  def truncate(self):
    raise NotImplementedError('truncate not implemented in KeyFile')

  def writelines(self):
    raise NotImplementedError('writelines not implemented in KeyFile')

  def xreadlines(self):
    raise NotImplementedError('xreadlines not implemented in KeyFile')

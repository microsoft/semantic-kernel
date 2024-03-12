# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Helper for cat and cp streaming download."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import io
import sys

from boto import config

from gslib.cloud_api import EncryptionException
from gslib.exception import CommandException
from gslib.exception import NO_URLS_MATCHED_TARGET
from gslib.storage_url import StorageUrlFromString
from gslib.utils.encryption_helper import CryptoKeyWrapperFromKey
from gslib.utils.encryption_helper import FindMatchingCSEKInBotoConfig
from gslib.utils.metadata_util import ObjectIsGzipEncoded
from gslib.utils import text_util

_CAT_BUCKET_LISTING_FIELDS = [
    'bucket',
    'contentEncoding',
    'crc32c',
    'customerEncryption',
    'generation',
    'md5Hash',
    'name',
    'size',
]


class CatHelper(object):
  """Provides methods for the "cat" command and associated functionality."""

  def __init__(self, command_obj):
    """Initializes the helper object.

    Args:
      command_obj: gsutil command instance of calling command.
    """
    self.command_obj = command_obj

  def _WriteBytesBufferedFileToFile(self, src_fd, dst_fd):
    """Copies contents of the source to the destination via buffered IO.

    Buffered reads are necessary in the case where you're reading from a
    source that produces more data than can fit into memory all at once. This
    method does not close either file when finished.

    Args:
      src_fd: The already-open source file to read from.
      dst_fd: The already-open destination file to write to.
    """
    while True:
      buf = src_fd.read(io.DEFAULT_BUFFER_SIZE)
      if not buf:
        break
      text_util.write_to_fd(dst_fd, buf)

  def CatUrlStrings(self,
                    url_strings,
                    show_header=False,
                    start_byte=0,
                    end_byte=None,
                    cat_out_fd=None):
    """Prints each of the url strings to stdout.

    Args:
      url_strings: String iterable.
      show_header: If true, print a header per file.
      start_byte: Starting byte of the file to print, used for constructing
                  range requests.
      end_byte: Ending byte of the file to print; used for constructing range
                requests. If this is negative, the start_byte is ignored and
                and end range is sent over HTTP (such as range: bytes -9)
      cat_out_fd: File descriptor to which output should be written. Defaults to
                 stdout if no file descriptor is supplied.
    Returns:
      0 on success.

    Raises:
      CommandException if no URLs can be found.
    """
    printed_one = False
    # This should refer to whatever sys.stdin refers to when this method is
    # run, not when this method is defined, so we do the initialization here
    # rather than define sys.stdin as the cat_out_fd parameter's default value.
    if cat_out_fd is None:
      cat_out_fd = sys.stdout
    # We manipulate the stdout so that all other data other than the Object
    # contents go to stderr.
    old_stdout = sys.stdout
    sys.stdout = sys.stderr
    try:
      if url_strings and url_strings[0] in ('-', 'file://-'):
        self._WriteBytesBufferedFileToFile(sys.stdin, cat_out_fd)
      else:
        for url_str in url_strings:
          did_some_work = False
          # TODO: Get only the needed fields here.
          for blr in self.command_obj.WildcardIterator(url_str).IterObjects(
              bucket_listing_fields=_CAT_BUCKET_LISTING_FIELDS):
            decryption_keywrapper = None
            if (blr.root_object and blr.root_object.customerEncryption and
                blr.root_object.customerEncryption.keySha256):
              decryption_key = FindMatchingCSEKInBotoConfig(
                  blr.root_object.customerEncryption.keySha256, config)
              if not decryption_key:
                raise EncryptionException(
                    'Missing decryption key with SHA256 hash %s. No decryption '
                    'key matches object %s' %
                    (blr.root_object.customerEncryption.keySha256,
                     blr.url_string))
              decryption_keywrapper = CryptoKeyWrapperFromKey(decryption_key)

            did_some_work = True
            if show_header:
              if printed_one:
                print()
              print('==> %s <==' % blr)
              printed_one = True
            cat_object = blr.root_object
            # This if statement ensures nothing is outputted and no error
            # is thrown if the user enters an out of bounds range for the object.
            if 0 < getattr(cat_object, 'size', -1) <= start_byte:
              return 0
            storage_url = StorageUrlFromString(blr.url_string)
            if storage_url.IsCloudUrl():
              compressed_encoding = ObjectIsGzipEncoded(cat_object)
              self.command_obj.gsutil_api.GetObjectMedia(
                  cat_object.bucket,
                  cat_object.name,
                  cat_out_fd,
                  compressed_encoding=compressed_encoding,
                  start_byte=start_byte,
                  end_byte=end_byte,
                  object_size=cat_object.size,
                  generation=storage_url.generation,
                  decryption_tuple=decryption_keywrapper,
                  provider=storage_url.scheme)
              cat_out_fd.flush()

            else:
              with open(storage_url.object_name, 'rb') as f:
                self._WriteBytesBufferedFileToFile(f, cat_out_fd)
          if not did_some_work:
            raise CommandException(NO_URLS_MATCHED_TARGET % url_str)
    finally:
      sys.stdout = old_stdout

    return 0

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
"""Hashing utilities for storage commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import enum

from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import fast_crc32c_util
from googlecloudsdk.core.updater import installers
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import hashing


class HashAlgorithm(enum.Enum):
  """Algorithms available for hashing data."""

  MD5 = 'md5'
  CRC32C = 'crc32c'


def get_base64_string(hash_bytes):
  """Takes bytes and returns base64-encoded string."""
  return base64.b64encode(hash_bytes).decode(encoding='utf-8')


def get_bytes_from_base64_string(hash_string):
  """Takes base64-encoded string and returns bytes."""
  hash_bytes = hash_string.encode('utf-8')
  return base64.b64decode(hash_bytes)


def get_base64_hash_digest_string(hash_object):
  """Takes hashlib object and returns base64-encoded digest as string."""
  return get_base64_string(hash_object.digest())


def get_hash_from_file(path, hash_algorithm, start=None, stop=None):
  """Reads file and returns its hash object.

  core.util.files.Checksum does similar things but is different enough to merit
  this function. The primary differences are that this function:
  -Uses a FIPS-safe MD5 object.
  -Accomodates gcloud_crc32c, which uses a Go binary for hashing.
  -Supports start and end index to set byte range for hashing.

  Args:
    path (str): File to read.
    hash_algorithm (HashAlgorithm): Algorithm to hash file with.
    start (int|None): Byte index to start hashing at.
    stop (int|None): Stop hashing at this byte index.

  Returns:
    Hash object for file.
  """
  if hash_algorithm == HashAlgorithm.MD5:
    hash_object = hashing.get_md5()
  elif hash_algorithm == HashAlgorithm.CRC32C:
    hash_object = fast_crc32c_util.get_crc32c()
  else:
    return

  if isinstance(hash_object, fast_crc32c_util.DeferredCrc32c):
    offset = 0 if start is None else start
    length = 0 if stop is None else stop - offset
    hash_object.sum_file(path, offset=offset, length=length)
    return hash_object

  with files.BinaryFileReader(path) as stream:
    if start:
      stream.seek(start)
    while True:
      if stop and stream.tell() >= stop:
        break

      # Avoids holding all of file in memory at once.
      if stop is None or stream.tell() + installers.WRITE_BUFFER_SIZE < stop:
        bytes_to_read = installers.WRITE_BUFFER_SIZE
      else:
        bytes_to_read = stop - stream.tell()

      data = stream.read(bytes_to_read)
      if not data:
        break

      if isinstance(data, str):
        # read() can return strings or bytes. Hash objects need bytes.
        data = data.encode('utf-8')
      # Compresses each piece of added data.
      hash_object.update(data)

  return hash_object


def validate_object_hashes_match(object_path, source_hash, destination_hash):
  """Confirms hashes match for copied objects.

  Args:
    object_path (str): URL of object being validated.
    source_hash (str): Hash of source object.
    destination_hash (str): Hash of destination object.

  Raises:
    HashMismatchError: Hashes are not equal.
  """
  if source_hash != destination_hash:
    raise errors.HashMismatchError(
        'Source hash {} does not match destination hash {}'
        ' for object {}.'.format(source_hash, destination_hash, object_path))


def update_digesters(digesters, data):
  """Updates every hash object with new data in a dict of digesters."""
  for hash_object in digesters.values():
    hash_object.update(data)


def copy_digesters(digesters):
  """Returns copy of provided digesters since deepcopying doesn't work."""
  result = {}
  for hash_algorithm in digesters:
    result[hash_algorithm] = digesters[hash_algorithm].copy()
  return result


def reset_digesters(digesters):
  """Clears the data from every hash object in a dict of digesters."""
  for hash_algorithm in digesters:
    if hash_algorithm is HashAlgorithm.MD5:
      digesters[hash_algorithm] = hashing.get_md5()
    elif hash_algorithm is HashAlgorithm.CRC32C:
      digesters[hash_algorithm] = fast_crc32c_util.get_crc32c()
    else:
      raise errors.Error(
          'Unknown hash algorithm found in digesters: {}'.format(hash_algorithm)
      )

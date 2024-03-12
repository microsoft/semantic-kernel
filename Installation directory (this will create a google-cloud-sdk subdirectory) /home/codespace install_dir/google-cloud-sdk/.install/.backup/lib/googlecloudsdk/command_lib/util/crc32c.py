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
"""Helpers for calculating CRC32C checksums."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64
import warnings

import six

# pylint: disable=g-import-not-at-top
try:
  # TODO(b/175725675) Make google_crc32c available with Cloud SDK.
  # Supress missing c extension warnings raised by google-crc32c. This usually
  # means the user needs to re-install the library.
  with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    import google_crc32c

  if google_crc32c.implementation in ('c', 'cffi'):
    # google-crc32c==1.1.3 changed implementation value to `c`.
    # We are checking both to ensure this is compatible with older versions.
    IS_FAST_GOOGLE_CRC32C_AVAILABLE = True
  else:
    raise ImportError
except ImportError:
  # TODO(b/194124148) Fall back on pure Python google-crc32c.
  # Cleans up a lot of this file.
  import gcloud_crcmod as crcmod
  IS_FAST_GOOGLE_CRC32C_AVAILABLE = False
# pylint: enable=g-import-not-at-top

# Castagnoli polynomial and its degree.
CASTAGNOLI_POLY = 4812730177
DEGREE = 32

# Table storing polynomial values of x^(2^k) mod CASTAGNOLI_POLY for all k < 31,
# where x^(2^k) and CASTAGNOLI_POLY are both considered polynomials. This is
# sufficient since x^(2^31) mod CASTAGNOLI_POLY = x.
X_POW_2K_TABLE = [
    2, 4, 16, 256, 65536, 517762881, 984302966, 408362264, 1503875210,
    2862076957, 3884826397, 1324787473, 621200174, 1758783527, 1416537776,
    1180494764, 648569364, 2521473789, 994858823, 1728245375, 3498467999,
    4059169852, 3345064394, 2828422810, 2429203150, 3336788029, 860151998,
    2102628683, 1033187991, 4243778976, 1123580069
]


def get_crc32c(initial_data=b''):
  """Returns an instance of Hashlib-like helper for CRC32C operations.

  Args:
    initial_data (bytes): The CRC32C object will be initialized with the
      checksum of the data.

  Returns:
    The google_crc32c.Checksum instance
    if google-crc32c (https://github.com/googleapis/python-crc32c) is
    available. If not, returns the predefined.Crc instance from crcmod library.

  Usage:
    # Get the instance.
    crc = get_crc32c()
    # Update the instance with data. If your data is available in chunks,
    # you can update each chunk so that you don't have to keep everything in
    # memory.
    for chunk in chunks:
      crc.update(data)
    # Get the digest.
    crc_digest = crc.digest()

  """
  if IS_FAST_GOOGLE_CRC32C_AVAILABLE:
    crc = google_crc32c.Checksum()
  else:
    crc = crcmod.predefined.Crc('crc-32c')

  if initial_data:
    crc.update(initial_data)

  return crc


def get_crc32c_from_checksum(checksum):
  """Returns Hashlib-like CRC32C object with a starting checksum.

  Args:
    checksum (int): CRC32C checksum representing the hash of processed data.

  Returns:
    google_crc32c.Checksum if google-crc32c is available or predefined.Crc
   instance from crcmod library. Both set to use initial checksum.
  """
  crc = get_crc32c()
  if IS_FAST_GOOGLE_CRC32C_AVAILABLE:
    # pylint:disable=protected-access
    crc._crc = checksum
    # pylint:enable=protected-access
  else:
    crc.crcValue = checksum
  return crc


def get_crc32c_hash_string_from_checksum(checksum):
  """Returns base64-encoded hash from the checksum.

  Args:
    checksum (int): CRC32C checksum representing the hash of processed data.

  Returns:
    A string representing the base64 encoded CRC32C hash.
  """
  crc_object = get_crc32c_from_checksum(checksum)
  return get_hash(crc_object)


def get_checksum(crc):
  """Gets the hex checksum from a CRC32C object.

  Args:
    crc (google_crc32c.Checksum|predefined.Crc): CRC32C object from
      google-crc32c or crcmod package.

  Returns:
    An int representing the CRC32C checksum of the provided object.
  """
  return int(crc.hexdigest(), 16)


def get_hash(crc):
  """Gets the base64-encoded hash from a CRC32C object.

  Args:
    crc (google_crc32c.Checksum|predefined.Crc): CRC32C object from
      google-crc32c or crcmod package.

  Returns:
    A string representing the base64 encoded CRC32C hash.
  """
  return base64.b64encode(crc.digest()).decode('ascii')


def does_data_match_checksum(data, crc32c_checksum):
  """Checks if checksum for the data matches the supplied checksum.

  Args:
    data (bytes): Bytes over which the checksum should be calculated.
    crc32c_checksum (int): Checksum against which data's checksum will be
      compared.

  Returns:
    True iff both checksums match.
  """
  crc = get_crc32c()
  crc.update(six.ensure_binary(data))
  return get_checksum(crc) == crc32c_checksum


def _reverse_32_bits(crc_checksum):
  return int('{0:032b}'.format(crc_checksum, width=32)[::-1], 2)


def _multiply_crc_polynomials(p, q):
  """Multiplies two polynomials together modulo CASTAGNOLI_POLY.

  Args:
    p (int): The first polynomial.
    q (int): The second polynomial.

  Returns:
    Int result of the multiplication.
  """
  result = 0
  top_bit = 1 << DEGREE
  for _ in range(DEGREE):
    if p & 1:
      result ^= q
    q <<= 1

    if q & top_bit:
      q ^= CASTAGNOLI_POLY
    p >>= 1

  return result


def _extend_crc32c_checksum_by_zeros(crc_checksum, bit_count):
  """Given crc_checksum representing polynomial P(x), compute P(x)*x^bit_count.

  Args:
    crc_checksum (int): crc respresenting polynomial P(x).
    bit_count (int): number of bits in crc.

  Returns:
    P(x)*x^bit_count (int).
  """
  updated_crc_checksum = _reverse_32_bits(crc_checksum)
  i = 0

  while bit_count != 0:
    if bit_count & 1:
      updated_crc_checksum = _multiply_crc_polynomials(
          updated_crc_checksum, X_POW_2K_TABLE[i % len(X_POW_2K_TABLE)])
    i += 1
    bit_count >>= 1

  updated_crc_checksum = _reverse_32_bits(updated_crc_checksum)
  return updated_crc_checksum


def concat_checksums(crc_a, crc_b, b_byte_count):
  """Computes CRC32C for concat(A, B) given crc(A), crc(B),and len(B).

  An explanation of the algorithm can be found at
  https://code.google.com/archive/p/crcutil/downloads.

  Args:
    crc_a (int): Represents the CRC32C checksum of object A.
    crc_b (int): Represents the CRC32C checksum of object B.
    b_byte_count (int): Length of data covered by crc_b in bytes.

  Returns:
    CRC32C checksum representing the data covered by crc_a and crc_b (int).
  """
  if not b_byte_count:
    return crc_a

  b_bit_count = 8 * b_byte_count
  return _extend_crc32c_checksum_by_zeros(crc_a, bit_count=b_bit_count) ^ crc_b

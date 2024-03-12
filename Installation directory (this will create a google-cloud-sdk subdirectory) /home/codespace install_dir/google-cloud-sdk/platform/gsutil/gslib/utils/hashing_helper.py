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
"""Helper functions for hashing functionality."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import base64
import binascii
import hashlib
import os

import six

from boto import config
import crcmod

from gslib.exception import CommandException
from gslib.utils.boto_util import UsingCrcmodExtension
from gslib.utils.constants import DEFAULT_FILE_BUFFER_SIZE
from gslib.utils.constants import MIN_SIZE_COMPUTE_LOGGING
from gslib.utils.constants import TRANSFER_BUFFER_SIZE
from gslib.utils.constants import UTF8

SLOW_CRCMOD_WARNING = """
WARNING: You have requested checksumming but your crcmod installation isn't
using the module's C extension, so checksumming will run very slowly. For help
installing the extension, please see "gsutil help crcmod".
"""

SLOW_CRCMOD_RSYNC_WARNING = """
WARNING: gsutil rsync uses hashes when modification time is not available at
both the source and destination. Your crcmod installation isn't using the
module's C extension, so checksumming will run very slowly. If this is your
first rsync since updating gsutil, this rsync can take significantly longer than
usual. For help installing the extension, please see "gsutil help crcmod".
"""

_SLOW_CRCMOD_DOWNLOAD_WARNING = """
WARNING: Downloading this composite object requires integrity checking with
CRC32c, but your crcmod installation isn't using the module's C extension,
so the hash computation will likely throttle download performance. For help
installing the extension, please see "gsutil help crcmod".

To disable slow integrity checking, see the "check_hashes" option in your
boto config file.
"""

_SLOW_CRC_EXCEPTION_TEXT = """
Downloading this composite object requires integrity checking with CRC32c,
but your crcmod installation isn't using the module's C extension, so the
hash computation will likely throttle download performance. For help
installing the extension, please see "gsutil help crcmod".

To download regardless of crcmod performance or to skip slow integrity
checks, see the "check_hashes" option in your boto config file.

NOTE: It is strongly recommended that you not disable integrity checks. Doing so
could allow data corruption to go undetected during uploading/downloading."""

_NO_HASH_CHECK_WARNING = """
WARNING: This download will not be validated since your crcmod installation
doesn't use the module's C extension, so the hash computation would likely
throttle download performance. For help in installing the extension, please
see "gsutil help crcmod".

To force integrity checking, see the "check_hashes" option in your boto config
file.
"""

# Configuration values for hashing.
CHECK_HASH_IF_FAST_ELSE_FAIL = 'if_fast_else_fail'
CHECK_HASH_IF_FAST_ELSE_SKIP = 'if_fast_else_skip'
CHECK_HASH_ALWAYS = 'always'
CHECK_HASH_NEVER = 'never'

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
# Castagnoli polynomial and its degree.
CASTAGNOLI_POLY = 4812730177
DEGREE = 32


def ConcatCrc32c(crc_a, crc_b, num_bytes_in_b):
  """Computes CRC32C for concat(A, B) given crc(A), crc(B) and len(B).

  An explanation of the algorithm can be found at
  crcutil.googlecode.com/files/crc-doc.1.0.pdf.

  Args:
    crc_a: A 32-bit integer representing crc(A) with least-significant
           coefficient first.
    crc_b: Same as crc_a.
    num_bytes_in_b: Length of B in bytes.

  Returns:
    CRC32C for concat(A, B)
  """
  if not num_bytes_in_b:
    return crc_a

  return _ExtendByZeros(crc_a, 8 * num_bytes_in_b) ^ crc_b


def _CrcMultiply(p, q):
  """Multiplies two polynomials together modulo CASTAGNOLI_POLY.

  Args:
    p: The first polynomial.
    q: The second polynomial.

  Returns:
    Result of the multiplication.
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


def _ExtendByZeros(crc, num_bits):
  """Given crc representing polynomial P(x), compute P(x)*x^num_bits.

  Args:
    crc: crc respresenting polynomial P(x).
    num_bits: number of bits in crc.

  Returns:
    P(x)*x^num_bits
  """

  def _ReverseBits32(crc):
    return int('{0:032b}'.format(crc, width=32)[::-1], 2)

  crc = _ReverseBits32(crc)
  i = 0

  while num_bits != 0:
    if num_bits & 1:
      crc = _CrcMultiply(crc, X_POW_2K_TABLE[i % len(X_POW_2K_TABLE)])
    i += 1
    num_bits >>= 1
  crc = _ReverseBits32(crc)
  return crc


def _CalculateHashFromContents(fp, hash_alg):
  """Calculates a base64 digest of the contents of a seekable stream.

  This function resets the file pointer to position 0.

  Args:
    fp: An already-open file object.
    hash_alg: Instance of hashing class initialized to start state.

  Returns:
    Hash of the stream in hex string format.
  """
  hash_dict = {'placeholder': hash_alg}
  fp.seek(0)
  CalculateHashesFromContents(fp, hash_dict)
  fp.seek(0)
  return hash_dict['placeholder'].hexdigest()


def CalculateHashesFromContents(fp, hash_dict, callback_processor=None):
  """Calculates hashes of the contents of a file.

  Args:
    fp: An already-open file object (stream will be consumed).
    hash_dict: Dict of (string alg_name: initialized hashing class)
        Hashing class will be populated with digests upon return.
    callback_processor: Optional callback processing class that implements
        Progress(integer amount of bytes processed).
  """
  while True:
    data = fp.read(DEFAULT_FILE_BUFFER_SIZE)
    if not data:
      break
    if six.PY3:
      if isinstance(data, str):
        data = data.encode(UTF8)
    for hash_alg in six.itervalues(hash_dict):
      hash_alg.update(data)
    if callback_processor:
      callback_processor.Progress(len(data))


def CalculateB64EncodedCrc32cFromContents(fp):
  """Calculates a base64 CRC32c checksum of the contents of a seekable stream.

  This function sets the stream position 0 before and after calculation.

  Args:
    fp: An already-open file object.

  Returns:
    CRC32c checksum of the file in base64 format.
  """
  return _CalculateB64EncodedHashFromContents(fp,
                                              crcmod.predefined.Crc('crc-32c'))


def CalculateB64EncodedMd5FromContents(fp):
  """Calculates a base64 MD5 digest of the contents of a seekable stream.

  This function sets the stream position 0 before and after calculation.

  Args:
    fp: An already-open file object.

  Returns:
    MD5 digest of the file in base64 format.
  """
  return _CalculateB64EncodedHashFromContents(fp, GetMd5())


def CalculateMd5FromContents(fp):
  """Calculates a base64 MD5 digest of the contents of a seekable stream.

  This function sets the stream position 0 before and after calculation.

  Args:
    fp: An already-open file object.

  Returns:
    MD5 digest of the file in hex format.
  """
  return _CalculateHashFromContents(fp, GetMd5())


def Base64EncodeHash(digest_value):
  """Returns the base64-encoded version of the input hex digest value."""
  encoded_bytes = base64.b64encode(binascii.unhexlify(digest_value))
  return encoded_bytes.rstrip(b'\n').decode(UTF8)


def Base64ToHexHash(base64_hash):
  """Returns the hex digest value of the input base64-encoded hash.

  Args:
    base64_hash: Base64-encoded hash, which may contain newlines and single or
        double quotes.

  Returns:
    Hex digest of the input argument.
  """
  decoded_bytes = base64.b64decode(base64_hash.strip('\n"\'').encode(UTF8))
  return binascii.hexlify(decoded_bytes)


def _CalculateB64EncodedHashFromContents(fp, hash_alg):
  """Calculates a base64 digest of the contents of a seekable stream.

  This function sets the stream position 0 before and after calculation.

  Args:
    fp: An already-open file object.
    hash_alg: Instance of hashing class initialized to start state.

  Returns:
    Hash of the stream in base64 format.
  """
  return Base64EncodeHash(_CalculateHashFromContents(fp, hash_alg))


def GetUploadHashAlgs():
  """Returns a dict of hash algorithms for validating an uploaded object.

  This is for use only with single object uploads, not compose operations
  such as those used by parallel composite uploads (though it can be used to
  validate the individual components).

  Returns:
    dict of (algorithm_name: hash_algorithm)
  """
  check_hashes_config = config.get('GSUtil', 'check_hashes',
                                   CHECK_HASH_IF_FAST_ELSE_FAIL)
  if check_hashes_config == 'never':
    return {}
  return {'md5': GetMd5}


def GetDownloadHashAlgs(logger, consider_md5=False, consider_crc32c=False):
  """Returns a dict of hash algorithms for validating an object.

  Args:
    logger: logging.Logger for outputting log messages.
    consider_md5: If True, consider using a md5 hash.
    consider_crc32c: If True, consider using a crc32c hash.

  Returns:
    Dict of (string, hash algorithm).

  Raises:
    CommandException if hash algorithms satisfying the boto config file
    cannot be returned.
  """
  check_hashes_config = config.get('GSUtil', 'check_hashes',
                                   CHECK_HASH_IF_FAST_ELSE_FAIL)
  if check_hashes_config == CHECK_HASH_NEVER:
    return {}

  hash_algs = {}
  if consider_md5:
    hash_algs['md5'] = GetMd5
  elif consider_crc32c:
    # If the cloud provider supplies a CRC, we'll compute a checksum to
    # validate if we're using a native crcmod installation and MD5 isn't
    # offered as an alternative.
    if UsingCrcmodExtension():
      hash_algs['crc32c'] = lambda: crcmod.predefined.Crc('crc-32c')
    elif not hash_algs:
      if check_hashes_config == CHECK_HASH_IF_FAST_ELSE_FAIL:
        raise CommandException(_SLOW_CRC_EXCEPTION_TEXT)
      elif check_hashes_config == CHECK_HASH_IF_FAST_ELSE_SKIP:
        logger.warn(_NO_HASH_CHECK_WARNING)
      elif check_hashes_config == CHECK_HASH_ALWAYS:
        logger.warn(_SLOW_CRCMOD_DOWNLOAD_WARNING)
        hash_algs['crc32c'] = lambda: crcmod.predefined.Crc('crc-32c')
      else:
        raise CommandException(
            'Your boto config \'check_hashes\' option is misconfigured.')

  return hash_algs


def GetMd5(byte_string=b''):
  """Returns md5 object, avoiding incorrect FIPS error on Red Hat systems.

  Examples: GetMd5(b'abc')
            GetMd5(bytes('abc', encoding='utf-8'))

  Args:
    byte_string (bytes): String in bytes form to hash. Don't include for empty
      hash object, since md5(b'').digest() == md5().digest().

  Returns:
    md5 hash object.
  """
  try:
    return hashlib.md5(byte_string)
  except ValueError:
    # On Red Hat-based platforms, may catch a FIPS error.
    # "usedforsecurity" flag only available on Red Hat systems or Python 3.9+.
    # pylint:disable=unexpected-keyword-arg
    return hashlib.md5(byte_string, usedforsecurity=False)
    # pylint:enable=unexpected-keyword-arg


class HashingFileUploadWrapper(object):
  """Wraps an input stream in a hash digester and exposes a stream interface.

  This class provides integrity checking during file uploads via the
  following properties:

  Calls to read will appropriately update digesters with all bytes read.
  Calls to seek (assuming it is supported by the wrapped stream) using
      os.SEEK_SET will catch up / reset the digesters to the specified
      position. If seek is called with a different os.SEEK mode, the caller
      must return to the original position using os.SEEK_SET before further
      reads.
  Calls to seek are fast if the desired position is equal to the position at
      the beginning of the last read call (we only need to re-hash bytes
      from that point on).
  """

  def __init__(self, stream, digesters, hash_algs, src_url, logger):
    """Initializes the wrapper.

    Args:
      stream: Input stream.
      digesters: dict of {string: hash digester} containing digesters, where
          string is the name of the hash algorithm.
      hash_algs: dict of {string: hash algorithm} for resetting and
          recalculating digesters. String is the name of the hash algorithm.
      src_url: Source FileUrl that is being copied.
      logger: For outputting log messages.
    """
    if not digesters:
      raise CommandException('HashingFileUploadWrapper used with no digesters.')
    elif not hash_algs:
      raise CommandException('HashingFileUploadWrapper used with no hash_algs.')

    self._orig_fp = stream
    self._digesters = digesters
    self._src_url = src_url
    self._logger = logger
    self._seek_away = None

    self._digesters_previous = {}
    for alg in self._digesters:
      self._digesters_previous[alg] = self._digesters[alg].copy()
    self._digesters_previous_mark = 0
    self._digesters_current_mark = 0
    self._hash_algs = hash_algs

  @property
  def mode(self):
    """Returns the mode of the underlying file descriptor, or None."""
    return getattr(self._orig_fp, 'mode', None)

  def read(self, size=-1):  # pylint: disable=invalid-name
    """"Reads from the wrapped file pointer and calculates hash digests.

    Args:
      size: The amount of bytes to read. If ommited or negative, the entire
          contents of the file will be read, hashed, and returned.

    Returns:
      Bytes from the wrapped stream.

    Raises:
      CommandException if the position of the wrapped stream is unknown.
    """
    if self._seek_away is not None:
      raise CommandException('Read called on hashing file pointer in an '
                             'unknown position; cannot correctly compute '
                             'digest.')

    data = self._orig_fp.read(size)
    if isinstance(data, six.text_type):
      data = data.encode(UTF8)
    self._digesters_previous_mark = self._digesters_current_mark
    for alg in self._digesters:
      self._digesters_previous[alg] = self._digesters[alg].copy()
      self._digesters[alg].update(data)
    self._digesters_current_mark += len(data)
    return data

  def tell(self):  # pylint: disable=invalid-name
    """Returns the current stream position."""
    return self._orig_fp.tell()

  def seekable(self):  # pylint: disable=invalid-name
    """Returns true if the stream is seekable."""
    return self._orig_fp.seekable()

  def seek(self, offset, whence=os.SEEK_SET):  # pylint: disable=invalid-name
    """Seeks in the wrapped file pointer and catches up hash digests.

    Args:
      offset: The offset to seek to.
      whence: os.SEEK_CUR, or SEEK_END, SEEK_SET.

    Returns:
      Return value from the wrapped stream's seek call.
    """
    if whence != os.SEEK_SET:
      # We do not catch up hashes for non-absolute seeks, and rely on the
      # caller to seek to an absolute position before reading.
      self._seek_away = self._orig_fp.tell()

    else:
      # Hashes will be correct and it's safe to call read().
      self._seek_away = None
      if offset < self._digesters_previous_mark:
        # This is earlier than our earliest saved digest, so we need to
        # reset the digesters and scan from the beginning.
        for alg in self._digesters:
          self._digesters[alg] = self._hash_algs[alg]()
        self._digesters_current_mark = 0
        self._orig_fp.seek(0)
        self._CatchUp(offset)

      elif offset == self._digesters_previous_mark:
        # Just load the saved digests.
        self._digesters_current_mark = self._digesters_previous_mark
        for alg in self._digesters:
          self._digesters[alg] = self._digesters_previous[alg]

      elif offset < self._digesters_current_mark:
        # Reset the position to our previous digest and scan forward.
        self._digesters_current_mark = self._digesters_previous_mark
        for alg in self._digesters:
          self._digesters[alg] = self._digesters_previous[alg]
        self._orig_fp.seek(self._digesters_previous_mark)
        self._CatchUp(offset - self._digesters_previous_mark)

      else:
        # Scan forward from our current digest and position.
        self._orig_fp.seek(self._digesters_current_mark)
        self._CatchUp(offset - self._digesters_current_mark)

    return self._orig_fp.seek(offset, whence)

  def _CatchUp(self, bytes_to_read):
    """Catches up hashes, but does not return data and uses little memory.

    Before calling this function, digesters_current_mark should be updated
    to the current location of the original stream and the self._digesters
    should be current to that point (but no further).

    Args:
      bytes_to_read: Number of bytes to catch up from the original stream.
    """
    if self._orig_fp.tell() != self._digesters_current_mark:
      raise CommandException(
          'Invalid mark when catching up hashes. Stream position %s, hash '
          'position %s' % (self._orig_fp.tell(), self._digesters_current_mark))

    for alg in self._digesters:
      if bytes_to_read >= MIN_SIZE_COMPUTE_LOGGING:
        self._logger.debug('Catching up %s for %s...', alg,
                           self._src_url.url_string)
      self._digesters_previous[alg] = self._digesters[alg].copy()

    self._digesters_previous_mark = self._digesters_current_mark
    bytes_remaining = bytes_to_read
    bytes_this_round = min(bytes_remaining, TRANSFER_BUFFER_SIZE)
    while bytes_this_round:
      data = self._orig_fp.read(bytes_this_round)
      if isinstance(data, six.text_type):
        data = data.encode(UTF8)
      bytes_remaining -= bytes_this_round
      for alg in self._digesters:
        self._digesters[alg].update(data)
      bytes_this_round = min(bytes_remaining, TRANSFER_BUFFER_SIZE)
    self._digesters_current_mark += bytes_to_read

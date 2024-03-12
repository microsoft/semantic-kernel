# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
#
import hashlib
import math
import binascii

from boto.compat import six


_MEGABYTE = 1024 * 1024
DEFAULT_PART_SIZE = 4 * _MEGABYTE
MAXIMUM_NUMBER_OF_PARTS = 10000


def minimum_part_size(size_in_bytes, default_part_size=DEFAULT_PART_SIZE):
    """Calculate the minimum part size needed for a multipart upload.

    Glacier allows a maximum of 10,000 parts per upload.  It also
    states that the maximum archive size is 10,000 * 4 GB, which means
    the part size can range from 1MB to 4GB (provided it is one 1MB
    multiplied by a power of 2).

    This function will compute what the minimum part size must be in
    order to upload a file of size ``size_in_bytes``.

    It will first check if ``default_part_size`` is sufficient for
    a part size given the ``size_in_bytes``.  If this is not the case,
    then the smallest part size than can accomodate a file of size
    ``size_in_bytes`` will be returned.

    If the file size is greater than the maximum allowed archive
    size of 10,000 * 4GB, a ``ValueError`` will be raised.

    """
    # The default part size (4 MB) will be too small for a very large
    # archive, as there is a limit of 10,000 parts in a multipart upload.
    # This puts the maximum allowed archive size with the default part size
    # at 40,000 MB. We need to do a sanity check on the part size, and find
    # one that works if the default is too small.
    part_size = _MEGABYTE
    if (default_part_size * MAXIMUM_NUMBER_OF_PARTS) < size_in_bytes:
        if size_in_bytes > (4096 * _MEGABYTE * 10000):
            raise ValueError("File size too large: %s" % size_in_bytes)
        min_part_size = size_in_bytes / 10000
        power = 3
        while part_size < min_part_size:
            part_size = math.ldexp(_MEGABYTE, power)
            power += 1
        part_size = int(part_size)
    else:
        part_size = default_part_size
    return part_size


def chunk_hashes(bytestring, chunk_size=_MEGABYTE):
    chunk_count = int(math.ceil(len(bytestring) / float(chunk_size)))
    hashes = []
    for i in range(chunk_count):
        start = i * chunk_size
        end = (i + 1) * chunk_size
        hashes.append(hashlib.sha256(bytestring[start:end]).digest())
    if not hashes:
        return [hashlib.sha256(b'').digest()]
    return hashes


def tree_hash(fo):
    """
    Given a hash of each 1MB chunk (from chunk_hashes) this will hash
    together adjacent hashes until it ends up with one big one. So a
    tree of hashes.
    """
    hashes = []
    hashes.extend(fo)
    while len(hashes) > 1:
        new_hashes = []
        while True:
            if len(hashes) > 1:
                first = hashes.pop(0)
                second = hashes.pop(0)
                new_hashes.append(hashlib.sha256(first + second).digest())
            elif len(hashes) == 1:
                only = hashes.pop(0)
                new_hashes.append(only)
            else:
                break
        hashes.extend(new_hashes)
    return hashes[0]


def compute_hashes_from_fileobj(fileobj, chunk_size=1024 * 1024):
    """Compute the linear and tree hash from a fileobj.

    This function will compute the linear/tree hash of a fileobj
    in a single pass through the fileobj.

    :param fileobj: A file like object.

    :param chunk_size: The size of the chunks to use for the tree
        hash.  This is also the buffer size used to read from
        `fileobj`.

    :rtype: tuple
    :return: A tuple of (linear_hash, tree_hash).  Both hashes
        are returned in hex.

    """
    # Python 3+, not binary
    if six.PY3 and hasattr(fileobj, 'mode') and 'b' not in fileobj.mode:
        raise ValueError('File-like object must be opened in binary mode!')

    linear_hash = hashlib.sha256()
    chunks = []
    chunk = fileobj.read(chunk_size)
    while chunk:
        # It's possible to get a file-like object that has no mode (checked
        # above) and returns something other than bytes (e.g. str). So here
        # we try to catch that and encode to bytes.
        if not isinstance(chunk, bytes):
            chunk = chunk.encode(getattr(fileobj, 'encoding', '') or 'utf-8')
        linear_hash.update(chunk)
        chunks.append(hashlib.sha256(chunk).digest())
        chunk = fileobj.read(chunk_size)
    if not chunks:
        chunks = [hashlib.sha256(b'').digest()]
    return linear_hash.hexdigest(), bytes_to_hex(tree_hash(chunks))


def bytes_to_hex(str_as_bytes):
    return binascii.hexlify(str_as_bytes)


def tree_hash_from_str(str_as_bytes):
    """

    :type str_as_bytes: str
    :param str_as_bytes: The string for which to compute the tree hash.

    :rtype: str
    :return: The computed tree hash, returned as hex.

    """
    return bytes_to_hex(tree_hash(chunk_hashes(str_as_bytes)))


class ResettingFileSender(object):
    def __init__(self, archive):
        self._archive = archive
        self._starting_offset = archive.tell()

    def __call__(self, connection, method, path, body, headers):
        try:
            connection.request(method, path, self._archive, headers)
            return connection.getresponse()
        finally:
            self._archive.seek(self._starting_offset)

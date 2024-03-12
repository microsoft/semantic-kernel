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
import logging
import os
import tempfile
import time
from hashlib import sha256
from tests.unit import unittest

from boto.compat import BytesIO, six, StringIO
from boto.glacier.utils import minimum_part_size, chunk_hashes, tree_hash, \
        bytes_to_hex, compute_hashes_from_fileobj


class TestPartSizeCalculations(unittest.TestCase):
    def test_small_values_still_use_default_part_size(self):
        self.assertEqual(minimum_part_size(1), 4 * 1024 * 1024)

    def test_under_the_maximum_value(self):
        # If we're under the maximum, we can use 4MB part sizes.
        self.assertEqual(minimum_part_size(8 * 1024 * 1024),
                         4 * 1024 * 1024)

    def test_gigabyte_size(self):
        # If we're over the maximum default part size, we go up to the next
        # power of two until we find a part size that keeps us under 10,000
        # parts.
        self.assertEqual(minimum_part_size(8 * 1024 * 1024 * 10000),
                         8 * 1024 * 1024)

    def test_terabyte_size(self):
        # For a 4 TB file we need at least a 512 MB part size.
        self.assertEqual(minimum_part_size(4 * 1024 * 1024 * 1024 * 1024),
                         512 * 1024 * 1024)

    def test_file_size_too_large(self):
        with self.assertRaises(ValueError):
            minimum_part_size((40000 * 1024 * 1024 * 1024) + 1)

    def test_default_part_size_can_be_specified(self):
        default_part_size = 2 * 1024 * 1024
        self.assertEqual(minimum_part_size(8 * 1024 * 1024, default_part_size),
                         default_part_size)


class TestChunking(unittest.TestCase):
    def test_chunk_hashes_exact(self):
        chunks = chunk_hashes(b'a' * (2 * 1024 * 1024))
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0], sha256(b'a' * 1024 * 1024).digest())

    def test_chunks_with_leftovers(self):
        bytestring = b'a' * (2 * 1024 * 1024 + 20)
        chunks = chunk_hashes(bytestring)
        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0], sha256(b'a' * 1024 * 1024).digest())
        self.assertEqual(chunks[1], sha256(b'a' * 1024 * 1024).digest())
        self.assertEqual(chunks[2], sha256(b'a' * 20).digest())

    def test_less_than_one_chunk(self):
        chunks = chunk_hashes(b'aaaa')
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], sha256(b'aaaa').digest())


class TestTreeHash(unittest.TestCase):
    # For these tests, a set of reference tree hashes were computed.
    # This will at least catch any regressions to the tree hash
    # calculations.
    def calculate_tree_hash(self, bytestring):
        start = time.time()
        calculated = bytes_to_hex(tree_hash(chunk_hashes(bytestring)))
        end = time.time()
        logging.debug("Tree hash calc time for length %s: %s",
                      len(bytestring), end - start)
        return calculated

    def test_tree_hash_calculations(self):
        one_meg_bytestring = b'a' * (1 * 1024 * 1024)
        two_meg_bytestring = b'a' * (2 * 1024 * 1024)
        four_meg_bytestring = b'a' * (4 * 1024 * 1024)
        bigger_bytestring = four_meg_bytestring + b'a' * 20

        self.assertEqual(
            self.calculate_tree_hash(one_meg_bytestring),
            b'9bc1b2a288b26af7257a36277ae3816a7d4f16e89c1e7e77d0a5c48bad62b360')
        self.assertEqual(
            self.calculate_tree_hash(two_meg_bytestring),
            b'560c2c9333c719cb00cfdffee3ba293db17f58743cdd1f7e4055373ae6300afa')
        self.assertEqual(
            self.calculate_tree_hash(four_meg_bytestring),
            b'9491cb2ed1d4e7cd53215f4017c23ec4ad21d7050a1e6bb636c4f67e8cddb844')
        self.assertEqual(
            self.calculate_tree_hash(bigger_bytestring),
            b'12f3cbd6101b981cde074039f6f728071da8879d6f632de8afc7cdf00661b08f')

    def test_empty_tree_hash(self):
        self.assertEqual(
            self.calculate_tree_hash(''),
            b'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')


class TestFileHash(unittest.TestCase):
    def _gen_data(self):
        # Generate some pseudo-random bytes of data. We include the
        # hard-coded blob as an example that fails to decode via UTF-8.
        return os.urandom(5000) + b'\xc2\x00'

    def test_compute_hash_tempfile(self):
        # Compute a hash from a file object. On Python 2 this uses a non-
        # binary mode. On Python 3, however, binary mode is required for
        # binary files. If not used, you will get UTF-8 code errors.
        if six.PY2:
            mode = "w+"
        else:
            mode = "wb+"

        with tempfile.TemporaryFile(mode=mode) as f:
            f.write(self._gen_data())
            f.seek(0)

            compute_hashes_from_fileobj(f, chunk_size=512)

    @unittest.skipUnless(six.PY3, 'Python 3 requires reading binary!')
    def test_compute_hash_tempfile_py3(self):
        # Note the missing 'b' in the mode!
        with tempfile.TemporaryFile(mode='w+') as f:
            with self.assertRaises(ValueError):
                compute_hashes_from_fileobj(f, chunk_size=512)

        # What about file-like objects without a mode? If it has an
        # encoding we use it, otherwise attempt UTF-8 encoding to
        # bytes for hashing.
        f = StringIO('test data' * 500)
        compute_hashes_from_fileobj(f, chunk_size=512)

    @unittest.skipUnless(six.PY2, 'Python 3 requires reading binary!')
    def test_compute_hash_stringio(self):
        # Python 2 binary data in StringIO example
        f = StringIO(self._gen_data())
        compute_hashes_from_fileobj(f, chunk_size=512)

    def test_compute_hash_bytesio(self):
        # Compute a hash from a file-like BytesIO object.
        f = BytesIO(self._gen_data())
        compute_hashes_from_fileobj(f, chunk_size=512)

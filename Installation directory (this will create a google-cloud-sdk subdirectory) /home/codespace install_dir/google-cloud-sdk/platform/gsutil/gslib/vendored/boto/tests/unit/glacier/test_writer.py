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
from hashlib import sha256
import itertools
from boto.compat import StringIO

from tests.unit import unittest
from mock import (
    call,
    Mock,
    sentinel,
)
from nose.tools import assert_equal

from boto.glacier.layer1 import Layer1
from boto.glacier.vault import Vault
from boto.glacier.writer import Writer, resume_file_upload
from boto.glacier.utils import bytes_to_hex, chunk_hashes, tree_hash


def create_mock_vault():
    vault = Mock(spec=Vault)
    vault.layer1 = Mock(spec=Layer1)
    vault.layer1.complete_multipart_upload.return_value = dict(
        ArchiveId=sentinel.archive_id)
    vault.name = sentinel.vault_name
    return vault


def partify(data, part_size):
    for i in itertools.count(0):
        start = i * part_size
        part = data[start:start + part_size]
        if part:
            yield part
        else:
            return


def calculate_mock_vault_calls(data, part_size, chunk_size):
    upload_part_calls = []
    data_tree_hashes = []
    for i, data_part in enumerate(partify(data, part_size)):
        start = i * part_size
        end = start + len(data_part)
        data_part_tree_hash_blob = tree_hash(
            chunk_hashes(data_part, chunk_size))
        data_part_tree_hash = bytes_to_hex(data_part_tree_hash_blob)
        data_part_linear_hash = sha256(data_part).hexdigest()
        upload_part_calls.append(
            call(
                sentinel.vault_name, sentinel.upload_id,
                data_part_linear_hash, data_part_tree_hash,
                (start, end - 1), data_part))
        data_tree_hashes.append(data_part_tree_hash_blob)

    return upload_part_calls, data_tree_hashes


def check_mock_vault_calls(vault, upload_part_calls, data_tree_hashes,
                           data_len):
    vault.layer1.upload_part.assert_has_calls(
        upload_part_calls, any_order=True)
    assert_equal(
        len(upload_part_calls), vault.layer1.upload_part.call_count)

    data_tree_hash = bytes_to_hex(tree_hash(data_tree_hashes))
    vault.layer1.complete_multipart_upload.assert_called_once_with(
        sentinel.vault_name, sentinel.upload_id, data_tree_hash, data_len)


class TestWriter(unittest.TestCase):
    def setUp(self):
        super(TestWriter, self).setUp()
        self.vault = create_mock_vault()
        self.chunk_size = 2 # power of 2
        self.part_size = 4 # power of 2
        upload_id = sentinel.upload_id
        self.writer = Writer(
            self.vault, upload_id, self.part_size, self.chunk_size)

    def check_write(self, write_list):
        for write_data in write_list:
            self.writer.write(write_data)
        self.writer.close()

        data = b''.join(write_list)
        upload_part_calls, data_tree_hashes = calculate_mock_vault_calls(
            data, self.part_size, self.chunk_size)
        check_mock_vault_calls(
            self.vault, upload_part_calls, data_tree_hashes, len(data))

    def test_single_byte_write(self):
        self.check_write([b'1'])

    def test_one_part_write(self):
        self.check_write([b'1234'])

    def test_split_write_1(self):
        self.check_write([b'1', b'234'])

    def test_split_write_2(self):
        self.check_write([b'12', b'34'])

    def test_split_write_3(self):
        self.check_write([b'123', b'4'])

    def test_one_part_plus_one_write(self):
        self.check_write([b'12345'])

    def test_returns_archive_id(self):
        self.writer.write(b'1')
        self.writer.close()
        self.assertEquals(sentinel.archive_id, self.writer.get_archive_id())

    def test_current_tree_hash(self):
        self.writer.write(b'1234')
        self.writer.write(b'567')
        hash_1 = self.writer.current_tree_hash
        self.assertEqual(hash_1,
            b'\x0e\xb0\x11Z\x1d\x1f\n\x10|\xf76\xa6\xf5' +
            b'\x83\xd1\xd5"bU\x0c\x95\xa8<\xf5\x81\xef\x0e\x0f\x95\n\xb7k'
        )

        # This hash will be different, since the content has changed.
        self.writer.write(b'22i3uy')
        hash_2 = self.writer.current_tree_hash
        self.assertEqual(hash_2,
            b'\x7f\xf4\x97\x82U]\x81R\x05#^\xe8\x1c\xd19' +
            b'\xe8\x1f\x9e\xe0\x1aO\xaad\xe5\x06"\xa5\xc0\xa8AdL'
        )
        self.writer.close()

        # Check the final tree hash, post-close.
        final_hash = self.writer.current_tree_hash
        self.assertEqual(final_hash,
            b';\x1a\xb8!=\xf0\x14#\x83\x11\xd5\x0b\x0f' +
            b'\xc7D\xe4\x8e\xd1W\x99z\x14\x06\xb9D\xd0\xf0*\x93\xa2\x8e\xf9'
        )
        # Then assert we don't get a different one on a subsequent call.
        self.assertEqual(final_hash, self.writer.current_tree_hash)

    def test_current_uploaded_size(self):
        self.writer.write(b'1234')
        self.writer.write(b'567')
        size_1 = self.writer.current_uploaded_size
        self.assertEqual(size_1, 4)

        # This hash will be different, since the content has changed.
        self.writer.write(b'22i3uy')
        size_2 = self.writer.current_uploaded_size
        self.assertEqual(size_2, 12)
        self.writer.close()

        # Get the final size, post-close.
        final_size = self.writer.current_uploaded_size
        self.assertEqual(final_size, 13)
        # Then assert we don't get a different one on a subsequent call.
        self.assertEqual(final_size, self.writer.current_uploaded_size)

    def test_upload_id(self):
        self.assertEquals(sentinel.upload_id, self.writer.upload_id)


class TestResume(unittest.TestCase):
    def setUp(self):
        super(TestResume, self).setUp()
        self.vault = create_mock_vault()
        self.chunk_size = 2 # power of 2
        self.part_size = 4 # power of 2

    def check_no_resume(self, data, resume_set=set()):
        fobj = StringIO(data.decode('utf-8'))
        part_hash_map = {}
        for part_index in resume_set:
            start = self.part_size * part_index
            end = start + self.part_size
            part_data = data[start:end]
            part_hash_map[part_index] = tree_hash(
                chunk_hashes(part_data, self.chunk_size))

        resume_file_upload(
            self.vault, sentinel.upload_id, self.part_size, fobj,
            part_hash_map, self.chunk_size)

        upload_part_calls, data_tree_hashes = calculate_mock_vault_calls(
            data, self.part_size, self.chunk_size)
        resume_upload_part_calls = [
            call for part_index, call in enumerate(upload_part_calls)
                    if part_index not in resume_set]
        check_mock_vault_calls(
            self.vault, resume_upload_part_calls, data_tree_hashes, len(data))

    def test_one_part_no_resume(self):
        self.check_no_resume(b'1234')

    def test_two_parts_no_resume(self):
        self.check_no_resume(b'12345678')

    def test_one_part_resume(self):
        self.check_no_resume(b'1234', resume_set=set([0]))

    def test_two_parts_one_resume(self):
        self.check_no_resume(b'12345678', resume_set=set([1]))

    def test_returns_archive_id(self):
        archive_id = resume_file_upload(
            self.vault, sentinel.upload_id, self.part_size, StringIO('1'), {},
            self.chunk_size)
        self.assertEquals(sentinel.archive_id, archive_id)

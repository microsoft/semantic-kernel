# -*- coding: utf-8 -*-
# Copyright (c) 2012 Thomas Parslow http://almostobsolete.net/
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

from tests.unit import unittest

from mock import call, Mock, patch, sentinel

import codecs
from boto.glacier.layer1 import Layer1
from boto.glacier.layer2 import Layer2
import boto.glacier.vault
from boto.glacier.vault import Vault
from boto.glacier.vault import Job

from datetime import datetime, tzinfo, timedelta

# Some fixture data from the Glacier docs
FIXTURE_VAULT = {
    "CreationDate": "2012-02-20T17:01:45.198Z",
    "LastInventoryDate": "2012-03-20T17:03:43.221Z",
    "NumberOfArchives": 192,
    "SizeInBytes": 78088912,
    "VaultARN": "arn:aws:glacier:us-east-1:012345678901:vaults/examplevault",
    "VaultName": "examplevault"
}

FIXTURE_VAULTS = {
    'RequestId': 'vuXO7SHTw-luynJ0Zu31AYjR3TcCn7X25r7ykpuulxY2lv8',
    'VaultList': [{'SizeInBytes': 0, 'LastInventoryDate': None,
                   'VaultARN': 'arn:aws:glacier:us-east-1:686406519478:vaults/vault0',
                   'VaultName': 'vault0', 'NumberOfArchives': 0,
                   'CreationDate': '2013-05-17T02:38:39.049Z'},
                  {'SizeInBytes': 0, 'LastInventoryDate': None,
                   'VaultARN': 'arn:aws:glacier:us-east-1:686406519478:vaults/vault3',
                   'VaultName': 'vault3', 'NumberOfArchives': 0,
                   'CreationDate': '2013-05-17T02:31:18.659Z'}]}

FIXTURE_PAGINATED_VAULTS = {
    'Marker': 'arn:aws:glacier:us-east-1:686406519478:vaults/vault2',
    'RequestId': 'vuXO7SHTw-luynJ0Zu31AYjR3TcCn7X25r7ykpuulxY2lv8',
    'VaultList': [{'SizeInBytes': 0, 'LastInventoryDate': None,
                   'VaultARN': 'arn:aws:glacier:us-east-1:686406519478:vaults/vault0',
                   'VaultName': 'vault0', 'NumberOfArchives': 0,
                   'CreationDate': '2013-05-17T02:38:39.049Z'},
                  {'SizeInBytes': 0, 'LastInventoryDate': None,
                   'VaultARN': 'arn:aws:glacier:us-east-1:686406519478:vaults/vault1',
                   'VaultName': 'vault1', 'NumberOfArchives': 0,
                   'CreationDate': '2013-05-17T02:31:18.659Z'}]}
FIXTURE_PAGINATED_VAULTS_CONT = {
    'Marker': None,
    'RequestId': 'vuXO7SHTw-luynJ0Zu31AYjR3TcCn7X25r7ykpuulxY2lv8',
    'VaultList': [{'SizeInBytes': 0, 'LastInventoryDate': None,
                   'VaultARN': 'arn:aws:glacier:us-east-1:686406519478:vaults/vault2',
                   'VaultName': 'vault2', 'NumberOfArchives': 0,
                   'CreationDate': '2013-05-17T02:38:39.049Z'},
                  {'SizeInBytes': 0, 'LastInventoryDate': None,
                   'VaultARN': 'arn:aws:glacier:us-east-1:686406519478:vaults/vault3',
                   'VaultName': 'vault3', 'NumberOfArchives': 0,
                   'CreationDate': '2013-05-17T02:31:18.659Z'}]}

FIXTURE_ARCHIVE_JOB = {
    "Action": "ArchiveRetrieval",
    "ArchiveId": ("NkbByEejwEggmBz2fTHgJrg0XBoDfjP4q6iu87-TjhqG6eGoOY9Z8i1_AUyUs"
                  "uhPAdTqLHy8pTl5nfCFJmDl2yEZONi5L26Omw12vcs01MNGntHEQL8MBfGlqr"
                  "EXAMPLEArchiveId"),
    "ArchiveSizeInBytes": 16777216,
    "Completed": False,
    "CreationDate": "2012-05-15T17:21:39.339Z",
    "CompletionDate": "2012-05-15T17:21:43.561Z",
    "InventorySizeInBytes": None,
    "JobDescription": "My ArchiveRetrieval Job",
    "JobId": ("HkF9p6o7yjhFx-K3CGl6fuSm6VzW9T7esGQfco8nUXVYwS0jlb5gq1JZ55yHgt5v"
              "P54ZShjoQzQVVh7vEXAMPLEjobID"),
    "SHA256TreeHash": ("beb0fe31a1c7ca8c6c04d574ea906e3f97b31fdca7571defb5b44dc"
                       "a89b5af60"),
    "SNSTopic": "arn:aws:sns:us-east-1:012345678901:mytopic",
    "StatusCode": "InProgress",
    "StatusMessage": "Operation in progress.",
    "VaultARN": "arn:aws:glacier:us-east-1:012345678901:vaults/examplevault"
}

EXAMPLE_PART_LIST_RESULT_PAGE_1 = {
    "ArchiveDescription": "archive description 1",
    "CreationDate": "2012-03-20T17:03:43.221Z",
    "Marker": "MfgsKHVjbQ6EldVl72bn3_n5h2TaGZQUO-Qb3B9j3TITf7WajQ",
    "MultipartUploadId": "OW2fM5iVylEpFEMM9_HpKowRapC3vn5sSL39_396UW9zLFUWVrnRHaPjUJddQ5OxSHVXjYtrN47NBZ-khxOjyEXAMPLE",
    "PartSizeInBytes": 4194304,
    "Parts": [{
        "RangeInBytes": "4194304-8388607",
        "SHA256TreeHash": "01d34dabf7be316472c93b1ef80721f5d4"
    }],
    "VaultARN": "arn:aws:glacier:us-east-1:012345678901:vaults/demo1-vault"
}

# The documentation doesn't say whether the non-Parts fields are defined in
# future pages, so assume they are not.
EXAMPLE_PART_LIST_RESULT_PAGE_2 = {
    "ArchiveDescription": None,
    "CreationDate": None,
    "Marker": None,
    "MultipartUploadId": None,
    "PartSizeInBytes": None,
    "Parts": [{
        "RangeInBytes": "0-4194303",
        "SHA256TreeHash": "01d34dabf7be316472c93b1ef80721f5d4"
    }],
    "VaultARN": None
}

EXAMPLE_PART_LIST_COMPLETE = {
    "ArchiveDescription": "archive description 1",
    "CreationDate": "2012-03-20T17:03:43.221Z",
    "Marker": None,
    "MultipartUploadId": "OW2fM5iVylEpFEMM9_HpKowRapC3vn5sSL39_396UW9zLFUWVrnRHaPjUJddQ5OxSHVXjYtrN47NBZ-khxOjyEXAMPLE",
    "PartSizeInBytes": 4194304,
    "Parts": [{
        "RangeInBytes": "4194304-8388607",
        "SHA256TreeHash": "01d34dabf7be316472c93b1ef80721f5d4"
    }, {
        "RangeInBytes": "0-4194303",
        "SHA256TreeHash": "01d34dabf7be316472c93b1ef80721f5d4"
    }],
    "VaultARN": "arn:aws:glacier:us-east-1:012345678901:vaults/demo1-vault"
}


class GlacierLayer2Base(unittest.TestCase):
    def setUp(self):
        self.mock_layer1 = Mock(spec=Layer1)


class TestGlacierLayer2Connection(GlacierLayer2Base):
    def setUp(self):
        GlacierLayer2Base.setUp(self)
        self.layer2 = Layer2(layer1=self.mock_layer1)

    def test_create_vault(self):
        self.mock_layer1.describe_vault.return_value = FIXTURE_VAULT
        self.layer2.create_vault("My Vault")
        self.mock_layer1.create_vault.assert_called_with("My Vault")

    def test_get_vault(self):
        self.mock_layer1.describe_vault.return_value = FIXTURE_VAULT
        vault = self.layer2.get_vault("examplevault")
        self.assertEqual(vault.layer1, self.mock_layer1)
        self.assertEqual(vault.name, "examplevault")
        self.assertEqual(vault.size, 78088912)
        self.assertEqual(vault.number_of_archives, 192)

    def test_list_vaults(self):
        self.mock_layer1.list_vaults.return_value = FIXTURE_VAULTS
        vaults = self.layer2.list_vaults()
        self.assertEqual(vaults[0].name, "vault0")
        self.assertEqual(len(vaults), 2)

    def test_list_vaults_paginated(self):
        resps = [FIXTURE_PAGINATED_VAULTS, FIXTURE_PAGINATED_VAULTS_CONT]
        def return_paginated_vaults_resp(marker=None, limit=None):
            return resps.pop(0)

        self.mock_layer1.list_vaults = Mock(side_effect=return_paginated_vaults_resp)
        vaults = self.layer2.list_vaults()
        self.assertEqual(vaults[0].name, "vault0")
        self.assertEqual(vaults[3].name, "vault3")
        self.assertEqual(len(vaults), 4)


class TestVault(GlacierLayer2Base):
    def setUp(self):
        GlacierLayer2Base.setUp(self)
        self.vault = Vault(self.mock_layer1, FIXTURE_VAULT)

    # TODO: Tests for the other methods of uploading

    def test_create_archive_writer(self):
        self.mock_layer1.initiate_multipart_upload.return_value = {
            "UploadId": "UPLOADID"}
        writer = self.vault.create_archive_writer(description="stuff")
        self.mock_layer1.initiate_multipart_upload.assert_called_with(
            "examplevault", self.vault.DefaultPartSize, "stuff")
        self.assertEqual(writer.vault, self.vault)
        self.assertEqual(writer.upload_id, "UPLOADID")

    def test_delete_vault(self):
        self.vault.delete_archive("archive")
        self.mock_layer1.delete_archive.assert_called_with("examplevault",
                                                           "archive")

    def test_initiate_job(self):
        class UTC(tzinfo):
            """UTC"""

            def utcoffset(self, dt):
                return timedelta(0)

            def tzname(self, dt):
                return "Z"

            def dst(self, dt):
                return timedelta(0)

        self.mock_layer1.initiate_job.return_value = {'JobId': 'job-id'}
        self.vault.retrieve_inventory(start_date=datetime(2014, 0o1, 0o1, tzinfo=UTC()),
                                      end_date=datetime(2014, 0o1, 0o2, tzinfo=UTC()),
                                      limit=100)
        self.mock_layer1.initiate_job.assert_called_with(
            'examplevault', {
                'Type': 'inventory-retrieval',
                'InventoryRetrievalParameters': {
                    'StartDate': '2014-01-01T00:00:00Z',
                    'EndDate': '2014-01-02T00:00:00Z',
                    'Limit': 100
                }
            })

    def test_get_job(self):
        self.mock_layer1.describe_job.return_value = FIXTURE_ARCHIVE_JOB
        job = self.vault.get_job(
            "NkbByEejwEggmBz2fTHgJrg0XBoDfjP4q6iu87-TjhqG6eGoOY9Z8i1_AUyUsuhPA"
            "dTqLHy8pTl5nfCFJmDl2yEZONi5L26Omw12vcs01MNGntHEQL8MBfGlqrEXAMPLEA"
            "rchiveId")
        self.assertEqual(job.action, "ArchiveRetrieval")

    def test_list_jobs(self):
        self.mock_layer1.list_jobs.return_value = {
            "JobList": [FIXTURE_ARCHIVE_JOB]}
        jobs = self.vault.list_jobs(False, "InProgress")
        self.mock_layer1.list_jobs.assert_called_with("examplevault",
                                                      False, "InProgress")
        self.assertEqual(jobs[0].archive_id,
                         "NkbByEejwEggmBz2fTHgJrg0XBoDfjP4q6iu87-TjhqG6eGoOY9Z"
                         "8i1_AUyUsuhPAdTqLHy8pTl5nfCFJmDl2yEZONi5L26Omw12vcs0"
                         "1MNGntHEQL8MBfGlqrEXAMPLEArchiveId")

    def test_list_all_parts_one_page(self):
        self.mock_layer1.list_parts.return_value = (
            dict(EXAMPLE_PART_LIST_COMPLETE)) # take a copy
        parts_result = self.vault.list_all_parts(sentinel.upload_id)
        expected = [call('examplevault', sentinel.upload_id)]
        self.assertEquals(expected, self.mock_layer1.list_parts.call_args_list)
        self.assertEquals(EXAMPLE_PART_LIST_COMPLETE, parts_result)

    def test_list_all_parts_two_pages(self):
        self.mock_layer1.list_parts.side_effect = [
            # take copies
            dict(EXAMPLE_PART_LIST_RESULT_PAGE_1),
            dict(EXAMPLE_PART_LIST_RESULT_PAGE_2)
        ]
        parts_result = self.vault.list_all_parts(sentinel.upload_id)
        expected = [call('examplevault', sentinel.upload_id),
                    call('examplevault', sentinel.upload_id,
                         marker=EXAMPLE_PART_LIST_RESULT_PAGE_1['Marker'])]
        self.assertEquals(expected, self.mock_layer1.list_parts.call_args_list)
        self.assertEquals(EXAMPLE_PART_LIST_COMPLETE, parts_result)

    @patch('boto.glacier.vault.resume_file_upload')
    def test_resume_archive_from_file(self, mock_resume_file_upload):
        part_size = 4
        mock_list_parts = Mock()
        mock_list_parts.return_value = {
            'PartSizeInBytes': part_size,
            'Parts': [{
                'RangeInBytes': '0-3',
                'SHA256TreeHash': '12',
            }, {
                'RangeInBytes': '4-6',
                'SHA256TreeHash': '34',
            }],
        }

        self.vault.list_all_parts = mock_list_parts
        self.vault.resume_archive_from_file(
            sentinel.upload_id, file_obj=sentinel.file_obj)
        mock_resume_file_upload.assert_called_once_with(
            self.vault, sentinel.upload_id, part_size, sentinel.file_obj,
            {0: codecs.decode('12', 'hex_codec'), 1: codecs.decode('34', 'hex_codec')})


class TestJob(GlacierLayer2Base):
    def setUp(self):
        GlacierLayer2Base.setUp(self)
        self.vault = Vault(self.mock_layer1, FIXTURE_VAULT)
        self.job = Job(self.vault, FIXTURE_ARCHIVE_JOB)

    def test_get_job_output(self):
        self.mock_layer1.get_job_output.return_value = "TEST_OUTPUT"
        self.job.get_output((0, 100))
        self.mock_layer1.get_job_output.assert_called_with(
            "examplevault",
            "HkF9p6o7yjhFx-K3CGl6fuSm6VzW9T7esGQfco8nUXVYwS0jlb5gq1JZ55yHgt5vP"
            "54ZShjoQzQVVh7vEXAMPLEjobID", (0, 100))


class TestRangeStringParsing(unittest.TestCase):
    def test_simple_range(self):
        self.assertEquals(
            Vault._range_string_to_part_index('0-3', 4), 0)

    def test_range_one_too_big(self):
        # Off-by-one bug in Amazon's Glacier implementation
        # See: https://forums.aws.amazon.com/thread.jspa?threadID=106866&tstart=0
        # Workaround is to assume that if a (start, end] range appears to be
        # returned then that is what it is.
        self.assertEquals(
            Vault._range_string_to_part_index('0-4', 4), 0)

    def test_range_too_big(self):
        self.assertRaises(
            AssertionError, Vault._range_string_to_part_index, '0-5', 4)

    def test_range_start_mismatch(self):
        self.assertRaises(
            AssertionError, Vault._range_string_to_part_index, '1-3', 4)

    def test_range_end_mismatch(self):
        # End mismatch is OK, since the last part might be short
        self.assertEquals(
            Vault._range_string_to_part_index('0-2', 4), 0)

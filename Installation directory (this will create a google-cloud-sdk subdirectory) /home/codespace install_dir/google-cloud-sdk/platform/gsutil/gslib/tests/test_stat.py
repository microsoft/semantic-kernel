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
"""Tests for stat command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib.cs_api_map import ApiSelector
from gslib.exception import NO_URLS_MATCHED_TARGET
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.testcase.integration_testcase import SkipForXML
from gslib.tests.util import GenerationFromURI as urigen
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import TEST_ENCRYPTION_CONTENT1
from gslib.tests.util import TEST_ENCRYPTION_CONTENT1_CRC32C
from gslib.tests.util import TEST_ENCRYPTION_CONTENT1_MD5
from gslib.tests.util import TEST_ENCRYPTION_CONTENT2
from gslib.tests.util import TEST_ENCRYPTION_CONTENT2_CRC32C
from gslib.tests.util import TEST_ENCRYPTION_CONTENT2_MD5
from gslib.tests.util import TEST_ENCRYPTION_CONTENT3
from gslib.tests.util import TEST_ENCRYPTION_CONTENT3_CRC32C
from gslib.tests.util import TEST_ENCRYPTION_CONTENT3_MD5
from gslib.tests.util import TEST_ENCRYPTION_KEY1
from gslib.tests.util import TEST_ENCRYPTION_KEY1_SHA256_B64
from gslib.tests.util import TEST_ENCRYPTION_KEY2
from gslib.tests.util import TEST_ENCRYPTION_KEY2_SHA256_B64
from gslib.tests.util import unittest
from gslib.utils.retry_util import Retry


class TestStat(testcase.GsUtilIntegrationTestCase):
  """Integration tests for stat command."""

  @SkipForS3('\'Archived time\' is a GS-specific response field.')
  @SkipForXML(
      'XML API only supports \'DeletedTime\' response field when making a '
      'GET Bucket request to list all objects, which is heavy overhead when '
      'the real intent is just a HEAD Object call.')
  def test_versioned_stat_output(self):
    """Tests stat output of an outdated object under version control."""
    bucket_uri = self.CreateVersionedBucket()
    old_object_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'z')

    # Update object
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name=old_object_uri.object_name,
                      contents=b'z',
                      gs_idempotent_generation=urigen(old_object_uri))

    stdout = self.RunGsUtil(['stat', old_object_uri.version_specific_uri],
                            return_stdout=True)

    self.assertIn('Noncurrent time', stdout)

  def test_stat_output(self):
    """Tests stat output of a single object."""
    object_uri = self.CreateObject(contents=b'z')
    stdout = self.RunGsUtil(['stat', suri(object_uri)], return_stdout=True)
    self.assertIn(object_uri.uri, stdout)
    self.assertIn('Creation time:', stdout)

    # Cache-Control and Content-Encoding can be different depending on
    # whether the JSON or XML API is used.  For JSON, only max-age and
    # no-cache are respected.  Although the object field will be populated
    # with whatever we set, the actual header returned from the JSON API
    # may differ from it (and differ from the XML response for the same object).
    #
    # Likewise, with contentEncoding, the field value and the header value
    # are not guaranteed to match or be the same across APIs.
    #
    # JSON will not return a Cache-control or content-encoding with the
    # current test object creation, so check these only for the XML API.
    if self.default_provider == 'gs':
      if self.test_api == ApiSelector.XML:
        self.assertIn('Cache-Control:', stdout)
        self.assertIn('Content-Encoding:', stdout)
      # TODO: Remove JSON check after adding storage class parsing in Boto.
      elif self.test_api == ApiSelector.JSON:
        self.assertIn('Storage class:', stdout)
      self.assertIn('Generation:', stdout)
      self.assertIn('Metageneration:', stdout)
      self.assertIn('Hash (crc32c):', stdout)
      self.assertIn('Hash (md5):', stdout)
      self.assertNotIn('Archived time', stdout)  # object is not archived
    self.assertIn('Content-Length:', stdout)
    self.assertIn('Content-Type:', stdout)
    self.assertIn('ETag:', stdout)

  def test_minus_q_stat(self):
    object_uri = self.CreateObject(contents=b'z')
    stdout = self.RunGsUtil(['-q', 'stat', suri(object_uri)],
                            return_stdout=True)
    self.assertEqual(0, len(stdout))
    stdout = self.RunGsUtil(
        ['-q', 'stat', suri(object_uri, 'junk')],
        return_stdout=True,
        expected_status=1)
    self.assertEqual(0, len(stdout))

  def test_stat_of_non_object_uri(self):
    self.RunGsUtil(['-q', 'stat', 'gs://'], expected_status=1)
    self.RunGsUtil(['-q', 'stat', 'gs://bucket/object'], expected_status=1)
    self.RunGsUtil(['-q', 'stat', 'file://tmp/abc'], expected_status=1)

  def test_stat_one_missing(self):
    bucket_uri = self.CreateBucket()
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name='notmissing',
                      contents=b'z')
    stdout, stderr = self.RunGsUtil(
        ['stat',
         suri(bucket_uri, 'missing'),
         suri(bucket_uri, 'notmissing')],
        expected_status=1,
        return_stdout=True,
        return_stderr=True)
    self.assertIn(NO_URLS_MATCHED_TARGET % suri(bucket_uri, 'missing'), stderr)
    self.assertIn('%s:' % suri(bucket_uri, 'notmissing'), stdout)

  def test_stat_one_missing_wildcard(self):
    bucket_uri = self.CreateBucket()
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name='notmissing',
                      contents=b'z')
    stdout, stderr = self.RunGsUtil(
        ['stat',
         suri(bucket_uri, 'missin*'),
         suri(bucket_uri, 'notmissin*')],
        expected_status=1,
        return_stdout=True,
        return_stderr=True)
    self.assertIn(NO_URLS_MATCHED_TARGET % suri(bucket_uri, 'missin*'), stderr)
    self.assertIn('%s:' % suri(bucket_uri, 'notmissing'), stdout)

  def test_stat_bucket_wildcard(self):
    # Prefix is a workaround for XML API limitation, see PR 766 for details
    bucket_uri = self.CreateBucket(bucket_name_prefix='aaa-')
    self.CreateObject(bucket_uri=bucket_uri, object_name='foo', contents=b'z')
    stat_string = suri(bucket_uri)[:-1] + '?/foo'
    self.RunGsUtil(['stat', stat_string])
    stat_string2 = suri(bucket_uri)[:-1] + '*/foo'
    self.RunGsUtil(['stat', stat_string2])

  def test_stat_object_wildcard(self):
    bucket_uri = self.CreateBucket()
    object1_uri = self.CreateObject(bucket_uri=bucket_uri,
                                    object_name='foo1',
                                    contents=b'z')
    object2_uri = self.CreateObject(bucket_uri=bucket_uri,
                                    object_name='foo2',
                                    contents=b'z')
    stat_string = suri(object1_uri)[:-2] + '*'

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['stat', stat_string], return_stdout=True)
      self.assertIn(suri(object1_uri), stdout)
      self.assertIn(suri(object2_uri), stdout)

    _Check1()

  @SkipForS3('S3 customer-supplied encryption keys are not supported.')
  def test_stat_encrypted_object(self):
    """Tests stat command with an encrypted object."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=TEST_ENCRYPTION_CONTENT1,
                                   encryption_key=TEST_ENCRYPTION_KEY1)

    # Stat object with key should return unencrypted hashes.
    with SetBotoConfigForTest([('GSUtil', 'encryption_key',
                                TEST_ENCRYPTION_KEY1)]):
      stdout = self.RunGsUtil(['stat', suri(object_uri)], return_stdout=True)
      self.assertIn(TEST_ENCRYPTION_CONTENT1_MD5, stdout)
      self.assertIn(TEST_ENCRYPTION_CONTENT1_CRC32C, stdout)
      self.assertIn(TEST_ENCRYPTION_KEY1_SHA256_B64.decode('ascii'), stdout)

    # Stat object without key should return encrypted hashes.
    stdout = self.RunGsUtil(['stat', suri(object_uri)], return_stdout=True)
    self.assertNotIn(TEST_ENCRYPTION_CONTENT1_MD5, stdout)
    self.assertNotIn(TEST_ENCRYPTION_CONTENT1_CRC32C, stdout)
    self.assertIn('encrypted', stdout)
    self.assertIn(TEST_ENCRYPTION_KEY1_SHA256_B64.decode('ascii'), stdout)

  def test_stat_encrypted_object_wildcard(self):
    """Tests stat command with a mix of encrypted and unencrypted objects."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    bucket_uri = self.CreateBucket()
    object1_uri = self.CreateObject(bucket_uri=bucket_uri,
                                    object_name='foo1',
                                    contents=TEST_ENCRYPTION_CONTENT1,
                                    encryption_key=TEST_ENCRYPTION_KEY1)
    object2_uri = self.CreateObject(bucket_uri=bucket_uri,
                                    object_name='foo2',
                                    contents=TEST_ENCRYPTION_CONTENT2,
                                    encryption_key=TEST_ENCRYPTION_KEY2)
    object3_uri = self.CreateObject(bucket_uri=bucket_uri,
                                    object_name='foo3',
                                    contents=TEST_ENCRYPTION_CONTENT3)

    stat_string = suri(object1_uri)[:-2] + '*'

    # Stat 3 objects, two encrypted each with a different key, and one
    # unencrypted. Should result in two unencrypted listing and one encrypted
    # listing.
    with SetBotoConfigForTest([('GSUtil', 'encryption_key',
                                TEST_ENCRYPTION_KEY1)]):
      # Use @Retry as hedge against bucket listing eventual consistency.
      @Retry(AssertionError, tries=3, timeout_secs=1)
      def _StatExpectMixed():
        """Runs stat and validates output."""
        stdout, stderr = self.RunGsUtil(['stat', stat_string],
                                        return_stdout=True,
                                        return_stderr=True)
        self.assertIn(suri(object1_uri), stdout)
        self.assertIn(TEST_ENCRYPTION_CONTENT1_MD5, stdout)
        self.assertIn(TEST_ENCRYPTION_CONTENT1_CRC32C, stdout)
        self.assertIn(TEST_ENCRYPTION_KEY1_SHA256_B64.decode('ascii'), stdout)
        self.assertIn(suri(object2_uri), stdout)
        self.assertNotIn(TEST_ENCRYPTION_CONTENT2_MD5, stdout)
        self.assertNotIn(TEST_ENCRYPTION_CONTENT2_CRC32C, stdout)
        self.assertIn('encrypted', stdout)
        self.assertIn(TEST_ENCRYPTION_KEY2_SHA256_B64.decode('ascii'), stdout)
        self.assertIn(suri(object3_uri), stdout)
        self.assertIn(TEST_ENCRYPTION_CONTENT3_MD5, stdout)
        self.assertIn(TEST_ENCRYPTION_CONTENT3_CRC32C, stdout)

      _StatExpectMixed()

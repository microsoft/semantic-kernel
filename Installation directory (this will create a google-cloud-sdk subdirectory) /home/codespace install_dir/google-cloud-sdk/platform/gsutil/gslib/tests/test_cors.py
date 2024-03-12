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
"""Integration tests for cors command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import json
import posixpath
from xml.dom.minidom import parseString

import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import ObjectToURI as suri
from gslib.utils.constants import UTF8
from gslib.utils.retry_util import Retry
from gslib.utils.translation_helper import CorsTranslation


@SkipForS3('CORS command is only supported for gs:// URLs')
class TestCors(testcase.GsUtilIntegrationTestCase):
  """Integration tests for cors command."""

  _set_cmd_prefix = ['cors', 'set']
  _get_cmd_prefix = ['cors', 'get']

  empty_doc1 = '[]'
  empty_doc2 = '[ {} ]'

  cors_bad = (
      '[{"origin": ["http://origin1.example.com", '
      '"http://origin2.example.com"], '
      '"responseHeader": ["foo", "bar"], "badmethod": ["GET", "PUT", "POST"], '
      '"maxAgeSeconds": 3600},'
      '{"origin": ["http://origin3.example.com"], '
      '"responseHeader": ["foo2", "bar2"], "method": ["GET", "DELETE"]}])')

  xml_cors_doc = parseString(
      '<CorsConfig><Cors><Origins>'
      '<Origin>http://origin1.example.com</Origin>'
      '<Origin>http://origin2.example.com</Origin>'
      '</Origins><Methods><Method>GET</Method>'
      '<Method>PUT</Method><Method>POST</Method></Methods>'
      '<ResponseHeaders><ResponseHeader>foo</ResponseHeader>'
      '<ResponseHeader>bar</ResponseHeader></ResponseHeaders>'
      '<MaxAgeSec>3600</MaxAgeSec></Cors>'
      '<Cors><Origins><Origin>http://origin3.example.com</Origin></Origins>'
      '<Methods><Method>GET</Method><Method>DELETE</Method></Methods>'
      '<ResponseHeaders><ResponseHeader>foo2</ResponseHeader>'
      '<ResponseHeader>bar2</ResponseHeader></ResponseHeaders>'
      '</Cors></CorsConfig>').toprettyxml(indent='    ')

  cors_doc = (
      '[{"origin": ["http://origin1.example.com", '
      '"http://origin2.example.com"], '
      '"responseHeader": ["foo", "bar"], "method": ["GET", "PUT", "POST"], '
      '"maxAgeSeconds": 3600},'
      '{"origin": ["http://origin3.example.com"], '
      '"responseHeader": ["foo2", "bar2"], "method": ["GET", "DELETE"]}]\n')
  cors_json_obj = json.loads(cors_doc)

  cors_doc_not_nested_in_list = (
      '{"origin": ["http://origin.example.com", "http://origin2.example.com"], '
      '"responseHeader": ["foo", "bar"], '
      '"method": ["GET", "PUT", "POST"], '
      '"maxAgeSeconds": 3600}')

  cors_doc2 = (
      '[{"origin": ["http://origin1.example.com", '
      '"http://origin2.example.com"], '
      '"responseHeader": ["foo", "bar"], "method": ["GET", "PUT", "POST"]}]\n')
  cors_json_obj2 = json.loads(cors_doc2)

  def setUp(self):
    super(TestCors, self).setUp()
    self.no_cors = ('[]' if self._use_gcloud_storage else
                    'has no CORS configuration')

  def test_cors_translation(self):
    """Tests cors translation for various formats."""
    json_text = self.cors_doc
    entries_list = CorsTranslation.JsonCorsToMessageEntries(json_text)
    boto_cors = CorsTranslation.BotoCorsFromMessage(entries_list)
    converted_entries_list = CorsTranslation.BotoCorsToMessage(boto_cors)
    converted_json_text = CorsTranslation.MessageEntriesToJson(
        converted_entries_list)
    self.assertEqual(json.loads(json_text), json.loads(converted_json_text))

  def test_default_cors(self):
    bucket_uri = self.CreateBucket()
    stdout = self.RunGsUtil(self._get_cmd_prefix + [suri(bucket_uri)],
                            return_stdout=True)
    self.assertIn(self.no_cors, stdout)

  def test_set_empty_cors1(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=self.empty_doc1.encode(UTF8))
    self.RunGsUtil(self._set_cmd_prefix + [fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(self._get_cmd_prefix + [suri(bucket_uri)],
                            return_stdout=True)
    self.assertIn(self.no_cors, stdout)

  def test_set_empty_cors2(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=self.empty_doc2.encode(UTF8))
    self.RunGsUtil(self._set_cmd_prefix + [fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(self._get_cmd_prefix + [suri(bucket_uri)],
                            return_stdout=True)
    self.assertIn(self.no_cors, stdout)

  def test_non_null_cors(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=self.cors_doc.encode(UTF8))
    self.RunGsUtil(self._set_cmd_prefix + [fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(self._get_cmd_prefix + [suri(bucket_uri)],
                            return_stdout=True)
    self.assertEqual(json.loads(stdout), self.cors_json_obj)

  def test_bad_cors_xml(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=self.xml_cors_doc.encode(UTF8))
    stderr = self.RunGsUtil(self._set_cmd_prefix +
                            [fpath, suri(bucket_uri)],
                            expected_status=1,
                            return_stderr=True)
    self.assertIn('XML CORS data provided', stderr)

  def test_bad_cors(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=self.cors_bad.encode(UTF8))
    stderr = self.RunGsUtil(self._set_cmd_prefix +
                            [fpath, suri(bucket_uri)],
                            expected_status=1,
                            return_stderr=True)

    if self._use_gcloud_storage:
      self.assertIn('Found invalid JSON/YAML file', stderr)
    else:
      self.assertNotIn('XML CORS data provided', stderr)

  def test_cors_doc_not_wrapped_in_json_list(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(
        contents=self.cors_doc_not_nested_in_list.encode(UTF8))
    stderr = self.RunGsUtil(self._set_cmd_prefix +
                            [fpath, suri(bucket_uri)],
                            expected_status=1,
                            return_stderr=True)
    if self._use_gcloud_storage:
      self.assertIn("'str' object has no attribute 'items'", stderr)
    else:
      self.assertIn('should be formatted as a list', stderr)

  def test_set_cors_and_reset(self):
    """Tests setting CORS then removing it."""
    bucket_uri = self.CreateBucket()
    tmpdir = self.CreateTempDir()
    fpath = self.CreateTempFile(tmpdir=tmpdir, contents=self.cors_doc)
    self.RunGsUtil(self._set_cmd_prefix + [fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(self._get_cmd_prefix + [suri(bucket_uri)],
                            return_stdout=True)
    self.assertEqual(json.loads(stdout), self.cors_json_obj)

    fpath = self.CreateTempFile(tmpdir=tmpdir, contents=self.empty_doc1)
    self.RunGsUtil(self._set_cmd_prefix + [fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(self._get_cmd_prefix + [suri(bucket_uri)],
                            return_stdout=True)
    self.assertIn(self.no_cors, stdout)

  def test_set_partial_cors_and_reset(self):
    """Tests setting CORS without maxAgeSeconds, then removing it."""
    bucket_uri = self.CreateBucket()
    tmpdir = self.CreateTempDir()
    fpath = self.CreateTempFile(tmpdir=tmpdir, contents=self.cors_doc2)
    self.RunGsUtil(self._set_cmd_prefix + [fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(self._get_cmd_prefix + [suri(bucket_uri)],
                            return_stdout=True)
    self.assertEqual(json.loads(stdout), self.cors_json_obj2)

    fpath = self.CreateTempFile(tmpdir=tmpdir, contents=self.empty_doc1)
    self.RunGsUtil(self._set_cmd_prefix + [fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(self._get_cmd_prefix + [suri(bucket_uri)],
                            return_stdout=True)
    self.assertIn(self.no_cors, stdout)

  def test_set_multi_non_null_cors(self):
    """Tests setting different CORS configurations."""
    bucket1_uri = self.CreateBucket()
    bucket2_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=self.cors_doc)
    self.RunGsUtil(
        self._set_cmd_prefix +
        [fpath, suri(bucket1_uri), suri(bucket2_uri)])
    stdout = self.RunGsUtil(self._get_cmd_prefix + [suri(bucket1_uri)],
                            return_stdout=True)
    self.assertEqual(json.loads(stdout), self.cors_json_obj)
    stdout = self.RunGsUtil(self._get_cmd_prefix + [suri(bucket2_uri)],
                            return_stdout=True)
    self.assertEqual(json.loads(stdout), self.cors_json_obj)

  def test_set_wildcard_non_null_cors(self):
    """Tests setting CORS on a wildcarded bucket URI."""
    random_prefix = self.MakeRandomTestString()
    bucket1_name = self.MakeTempName('bucket', prefix=random_prefix)
    bucket2_name = self.MakeTempName('bucket', prefix=random_prefix)
    bucket1_uri = self.CreateBucket(bucket_name=bucket1_name)
    bucket2_uri = self.CreateBucket(bucket_name=bucket2_name)
    # This just double checks that the common prefix of the two buckets is what
    # we think it should be (based on implementation detail of CreateBucket).
    # We want to be careful when setting a wildcard on buckets to make sure we
    # don't step outside the test buckets to affect other buckets.
    common_prefix = posixpath.commonprefix(
        [suri(bucket1_uri), suri(bucket2_uri)])
    self.assertTrue(
        common_prefix.startswith('gs://%sgsutil-test-test-set-wildcard-non' %
                                 random_prefix))
    wildcard = '%s*' % common_prefix

    fpath = self.CreateTempFile(contents=self.cors_doc.encode(UTF8))

    # Use @Retry as hedge against bucket listing eventual consistency.
    if self._use_gcloud_storage:
      expected = set([
          'Updating %s' % suri(bucket1_uri),
          'Updating %s' % suri(bucket2_uri)
      ])
    else:
      expected = set([
          'Setting CORS on %s/...' % suri(bucket1_uri),
          'Setting CORS on %s/...' % suri(bucket2_uri)
      ])
    actual = set()

    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      """Ensures expect set lines are present in command output."""
      stderr = self.RunGsUtil(self._set_cmd_prefix + [fpath, wildcard],
                              return_stderr=True)
      outlines = stderr.splitlines()
      for line in outlines:
        # Ignore the deprecation warnings from running the old cors command.
        if ('You are using a deprecated alias' in line or
            'gsutil help cors' in line or
            'Please use "cors" with the appropriate sub-command' in line):
          continue
        actual.add(line)
      for line in expected:
        if self._use_gcloud_storage:
          # Not exact match because gcloud may print progress or other logs.
          self.assertIn(line, stderr)
        else:
          self.assertIn(line, actual)
          self.assertEqual(stderr.count('Setting CORS'), 2)

    _Check1()

    stdout = self.RunGsUtil(self._get_cmd_prefix + [suri(bucket1_uri)],
                            return_stdout=True)
    self.assertEqual(json.loads(stdout), self.cors_json_obj)
    stdout = self.RunGsUtil(self._get_cmd_prefix + [suri(bucket2_uri)],
                            return_stdout=True)
    self.assertEqual(json.loads(stdout), self.cors_json_obj)

  def testTooFewArgumentsFails(self):
    """Ensures CORS commands fail with too few arguments."""
    # No arguments for get, but valid subcommand.
    stderr = self.RunGsUtil(self._get_cmd_prefix,
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('command requires at least', stderr)

    # No arguments for set, but valid subcommand.
    stderr = self.RunGsUtil(self._set_cmd_prefix,
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('command requires at least', stderr)

    # Neither arguments nor subcommand.
    stderr = self.RunGsUtil(['cors'], return_stderr=True, expected_status=1)
    self.assertIn('command requires at least', stderr)


class TestCorsOldAlias(TestCors):
  _set_cmd_prefix = ['setcors']
  _get_cmd_prefix = ['getcors']

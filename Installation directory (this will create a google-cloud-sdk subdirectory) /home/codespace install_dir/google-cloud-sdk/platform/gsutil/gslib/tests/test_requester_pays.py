# -*- coding: utf-8 -*-
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Integration tests for notification command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import re

import gslib.tests.testcase as testcase
from gslib.project_id import PopulateProjectId
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.testcase.integration_testcase import SkipForXML
from gslib.tests.util import ObjectToURI as suri
from gslib.utils.retry_util import Retry
from gslib.utils.constants import UTF8

OBJECT_CONTENTS = b'innards'


@SkipForS3('gsutil doesn\'t support S3 Requester Pays.')
@SkipForXML('Requester Pays is not supported for the XML API.')
class TestRequesterPays(testcase.GsUtilIntegrationTestCase):
  """Integration tests for Requester Pays.

  Passing in a user project should succeed for operations on Requester Pays
  buckets, and with the GA release will also succeed for non-Requester Pays
  buckets.
  """

  _set_rp_cmd = ['requesterpays', 'set']
  _get_rp_cmd = ['requesterpays', 'get']

  def setUp(self):
    super(TestRequesterPays, self).setUp()
    self.non_requester_pays_bucket_uri = self.CreateBucket()
    self.requester_pays_bucket_uri = self.CreateBucket()
    self._set_requester_pays(self.requester_pays_bucket_uri)
    self.non_requester_pays_object_uri = self.CreateObject(
        bucket_uri=self.non_requester_pays_bucket_uri, contents=OBJECT_CONTENTS)
    self.requester_pays_object_uri = self.CreateObject(
        bucket_uri=self.requester_pays_bucket_uri, contents=OBJECT_CONTENTS)
    self.user_project_flag = ['-u', PopulateProjectId()]

  def _set_requester_pays(self, bucket_uri):
    self.RunGsUtil(['requesterpays', 'set', 'on', suri(bucket_uri)])

  def _run_requester_pays_test(self, command_list, regex=None):
    """Test a command with a user project.

    Run a command with a user project on a Requester Pays bucket. The command is
    expected to pass because the source bucket is Requester Pays. If a regex
    pattern is supplied, also assert that stdout of the command matches it.
    """
    stdout = self.RunGsUtil(self.user_project_flag + command_list,
                            return_stdout=True)
    if regex:
      if isinstance(regex, bytes):
        regex = regex.decode(UTF8)
      self.assertRegexpMatchesWithFlags(stdout, regex, flags=re.IGNORECASE)

  def _run_non_requester_pays_test(self, command_list):
    """Test a command with a user project on a non-Requester Pays bucket.

    Run a command with a user project on a non-Requester Pays bucket. The
    command will still succeed, because with GA user project is accepted for
    all requests.
    """
    stdout = self.RunGsUtil(self.user_project_flag + command_list,
                            return_stdout=True)

  def test_off_default(self):
    bucket_uri = self.CreateBucket()
    stdout = self.RunGsUtil(self._get_rp_cmd + [suri(bucket_uri)],
                            return_stdout=True)
    self.assertEqual(stdout.strip(), '%s: Disabled' % suri(bucket_uri))

  def test_turning_on(self):
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(self._set_rp_cmd + ['on', suri(bucket_uri)])

    def _Check1():
      stdout = self.RunGsUtil(self._get_rp_cmd + [suri(bucket_uri)],
                              return_stdout=True)
      self.assertEqual(stdout.strip(), '%s: Enabled' % suri(bucket_uri))

    _Check1()

  def test_turning_off(self):
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(self._set_rp_cmd + ['on', suri(bucket_uri)])

    def _Check1():
      stdout = self.RunGsUtil(self._get_rp_cmd + [suri(bucket_uri)],
                              return_stdout=True)
      self.assertEqual(stdout.strip(), '%s: Enabled' % suri(bucket_uri))

    _Check1()

    self.RunGsUtil(self._set_rp_cmd + ['off', suri(bucket_uri)])

    def _Check2():
      stdout = self.RunGsUtil(self._get_rp_cmd + [suri(bucket_uri)],
                              return_stdout=True)
      self.assertEqual(stdout.strip(), '%s: Disabled' % suri(bucket_uri))

    _Check2()

  def testTooFewArgumentsFails(self):
    """Ensures requesterpays commands fail with too few arguments."""
    # No arguments for set, but valid subcommand.
    stderr = self.RunGsUtil(self._set_rp_cmd,
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('command requires at least', stderr)

    # No arguments for get, but valid subcommand.
    stderr = self.RunGsUtil(self._get_rp_cmd,
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('command requires at least', stderr)

    # Neither arguments nor subcommand.
    stderr = self.RunGsUtil(['requesterpays'],
                            return_stderr=True,
                            expected_status=1)
    self.assertIn('command requires at least', stderr)

  def test_acl(self):
    requester_pays_bucket_uri = self.CreateBucket()
    self._set_requester_pays(requester_pays_bucket_uri)
    self._run_requester_pays_test(
        ['acl', 'set', 'public-read',
         suri(requester_pays_bucket_uri)])
    self._run_requester_pays_test(
        ['acl', 'get', suri(requester_pays_bucket_uri)])

    non_requester_pays_bucket_uri = self.CreateBucket()
    self._run_non_requester_pays_test(
        ['acl', 'set', 'public-read',
         suri(non_requester_pays_bucket_uri)])
    self._run_non_requester_pays_test(
        ['acl', 'get', suri(non_requester_pays_bucket_uri)])

  def test_ls(self):
    self._run_requester_pays_test(['ls', suri(self.requester_pays_bucket_uri)])
    self._run_non_requester_pays_test(
        ['ls', suri(self.non_requester_pays_bucket_uri)])

  def test_rb(self):
    rp_bucket_uri = self.CreateBucket()
    self._set_requester_pays(rp_bucket_uri)
    self._run_requester_pays_test(['rb', suri(rp_bucket_uri)])

    non_rp_bucket_uri = self.CreateBucket()
    self._run_non_requester_pays_test(['rb', suri(non_rp_bucket_uri)])

  def test_copy(self):
    dest_bucket_uri = self.CreateBucket()

    self._run_requester_pays_test(
        ['cp',
         suri(self.requester_pays_object_uri),
         suri(dest_bucket_uri)])
    self._run_non_requester_pays_test(
        ['cp',
         suri(self.non_requester_pays_object_uri),
         suri(dest_bucket_uri)])

  def test_compose(self):
    data_list = [b'apple', b'orange', b'banana']

    bucket_uri = self.CreateBucket()
    components = [
        self.CreateObject(bucket_uri=bucket_uri, contents=data).uri
        for data in data_list
    ]
    composite = self.StorageUriCloneReplaceName(bucket_uri,
                                                self.MakeTempName('obj'))
    self._run_non_requester_pays_test(['compose'] + components +
                                      [composite.uri])

    rp_bucket_uri = self.CreateBucket()
    self._set_requester_pays(rp_bucket_uri)
    rp_components = [
        self.CreateObject(bucket_uri=rp_bucket_uri, contents=data).uri
        for data in data_list
    ]
    rp_composite = suri(rp_bucket_uri) + '/composite.txt'
    self._run_requester_pays_test(['compose'] + rp_components + [rp_composite])

  def test_cat(self):
    self._run_requester_pays_test(
        ['cat', suri(self.requester_pays_object_uri)], regex=OBJECT_CONTENTS)
    self._run_non_requester_pays_test(
        ['cat', suri(self.non_requester_pays_object_uri)])

  def test_du_obj(self):

    @Retry(AssertionError, tries=3, timeout_secs=1)
    # Use @Retry as hedge against bucket listing eventual consistency.
    def _check():
      self._run_requester_pays_test(
          ['du', suri(self.requester_pays_object_uri)])
      self._run_non_requester_pays_test(
          ['du', suri(self.non_requester_pays_object_uri)])

    _check()

  def test_hash(self):
    self._run_requester_pays_test(
        ['hash', '-c', suri(self.requester_pays_object_uri)],
        regex=r'Hash \(crc32c\)')
    self._run_non_requester_pays_test(
        ['hash', '-c', suri(self.non_requester_pays_object_uri)])

  def test_iam(self):
    self._run_requester_pays_test(
        ['iam', 'get', str(self.requester_pays_object_uri)])
    self._run_non_requester_pays_test(
        ['iam', 'get', str(self.non_requester_pays_object_uri)])

  def test_mv(self):
    requester_pays_bucket_uri = self.CreateBucket()
    object1_uri = self.CreateObject(bucket_uri=requester_pays_bucket_uri,
                                    contents=b'foo')
    object2_uri = self.CreateObject(bucket_uri=requester_pays_bucket_uri,
                                    contents=b'oOOo')
    self.AssertNObjectsInBucket(requester_pays_bucket_uri, 2)
    self._set_requester_pays(requester_pays_bucket_uri)
    dest_bucket_uri = self.CreateBucket()

    # Move two objects from bucket1 to Requester Pays bucket.
    for obj in [object1_uri, object2_uri]:
      self._run_requester_pays_test(['mv', suri(obj), suri(dest_bucket_uri)])
    self.AssertNObjectsInBucket(requester_pays_bucket_uri, 0)

    bucket_uri = self.CreateBucket()
    object1_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'bar')
    object2_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'baz')
    self.AssertNObjectsInBucket(bucket_uri, 2)
    for obj in [object1_uri, object2_uri]:
      self._run_non_requester_pays_test(
          ['mv', suri(obj), suri(dest_bucket_uri)])
    self.AssertNObjectsInBucket(bucket_uri, 0)

  def test_rewrite(self):
    object_uri = self.CreateObject(contents=b'bar')
    storage_class = 'nearline' if self._use_gcloud_storage else 'dra'
    self._run_non_requester_pays_test(
        ['rewrite', '-s', storage_class,
         suri(object_uri)])

    req_pays_bucket_uri = self.CreateBucket()
    self._set_requester_pays(req_pays_bucket_uri)
    req_pays_obj_uri = self.CreateObject(bucket_uri=req_pays_bucket_uri,
                                         contents=b'baz')
    self._run_requester_pays_test(
        ['rewrite', '-s', storage_class,
         suri(req_pays_obj_uri)])

  def test_rsync(self):
    req_pays_bucket_uri = self.CreateBucket(test_objects=2)
    self._set_requester_pays(req_pays_bucket_uri)
    bucket_uri = self.CreateBucket(test_objects=1)
    self._run_requester_pays_test([
        'rsync', '-d',
        suri(req_pays_bucket_uri),
        suri(self.requester_pays_bucket_uri)
    ])

    bucket_uri1 = self.CreateBucket(test_objects=2)
    bucket_uri2 = self.CreateBucket(test_objects=1)
    self._run_non_requester_pays_test(
        ['rsync', '-d', suri(bucket_uri1),
         suri(bucket_uri2)])

  def test_setmeta(self):
    req_pays_obj_uri = self.CreateObject(
        bucket_uri=self.requester_pays_bucket_uri,
        contents=b'<html><body>text</body></html>')
    self._run_requester_pays_test(
        ['setmeta', '-h', 'content-type:text/html',
         suri(req_pays_obj_uri)])

    obj_uri = self.CreateObject(bucket_uri=self.non_requester_pays_bucket_uri,
                                contents=b'<html><body>text</body></html>')
    self._run_non_requester_pays_test(
        ['setmeta', '-h', 'content-type:text/html',
         suri(obj_uri)])

  def test_stat(self):
    self._run_requester_pays_test(
        ['stat', suri(self.requester_pays_object_uri)])
    self._run_non_requester_pays_test(
        ['stat', suri(self.non_requester_pays_object_uri)])

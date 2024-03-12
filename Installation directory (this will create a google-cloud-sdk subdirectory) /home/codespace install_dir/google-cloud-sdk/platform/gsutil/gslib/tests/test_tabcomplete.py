# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc.  All Rights Reserved.
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
"""Integration tests for tab completion."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import time

from gslib.command import CreateOrGetGsutilLogger
from gslib.tab_complete import CloudObjectCompleter
from gslib.tab_complete import TAB_COMPLETE_CACHE_TTL
from gslib.tab_complete import TabCompletionCache
import gslib.tests.testcase as testcase
from gslib.tests.util import ARGCOMPLETE_AVAILABLE
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import unittest
from gslib.tests.util import WorkingDirectory
from gslib.utils.boto_util import GetTabCompletionCacheFilename


@unittest.skipUnless(ARGCOMPLETE_AVAILABLE,
                     'Tab completion requires argcomplete')
class TestTabComplete(testcase.GsUtilIntegrationTestCase):
  """Integration tests for tab completion."""

  def setUp(self):
    super(TestTabComplete, self).setUp()
    self.logger = CreateOrGetGsutilLogger('tab_complete')

  def test_single_bucket(self):
    """Tests tab completion matching a single bucket."""

    # Prefix is a workaround for XML API limitation, see PR 766 for details
    bucket_name = self.MakeTempName('bucket', prefix='aaa-')
    self.CreateBucket(bucket_name)

    request = '%s://%s' % (self.default_provider, bucket_name[:-2])
    expected_result = '//%s/' % bucket_name

    self.RunGsUtilTabCompletion(['ls', request],
                                expected_results=[expected_result])

  def test_bucket_only_single_bucket(self):
    """Tests bucket-only tab completion matching a single bucket."""

    bucket_name = self.MakeTempName('bucket', prefix='aaa-')
    # Workaround for XML API limitation, see PR 766 for details
    self.CreateBucket(bucket_name)

    request = '%s://%s' % (self.default_provider, bucket_name[:-2])
    expected_result = '//%s ' % bucket_name

    self.RunGsUtilTabCompletion(['rb', request],
                                expected_results=[expected_result])

  def test_bucket_only_no_objects(self):
    """Tests that bucket-only tab completion doesn't match objects."""

    object_name = self.MakeTempName('obj')
    object_uri = self.CreateObject(object_name=object_name, contents=b'data')

    request = '%s://%s/%s' % (self.default_provider, object_uri.bucket_name,
                              object_name[:-2])

    self.RunGsUtilTabCompletion(['rb', request], expected_results=[])

  def test_single_subdirectory(self):
    """Tests tab completion matching a single subdirectory."""

    object_base_name = self.MakeTempName('obj')
    object_name = object_base_name + '/subobj'
    object_uri = self.CreateObject(object_name=object_name, contents=b'data')

    request = '%s://%s/' % (self.default_provider, object_uri.bucket_name)
    expected_result = '//%s/%s/' % (object_uri.bucket_name, object_base_name)

    self.RunGsUtilTabCompletion(['ls', request],
                                expected_results=[expected_result])

  def test_multiple_buckets(self):
    """Tests tab completion matching multiple buckets."""

    base_name = self.MakeTempName('bucket')
    # Workaround for XML API limitation, see PR 766 for details
    prefix = 'aaa-'
    self.CreateBucket(base_name,
                      bucket_name_prefix=prefix,
                      bucket_name_suffix='1')
    self.CreateBucket(base_name,
                      bucket_name_prefix=prefix,
                      bucket_name_suffix='2')

    request = '%s://%s' % (self.default_provider, ''.join([prefix, base_name]))
    expected_result1 = '//%s/' % ''.join([prefix, base_name, '1'])
    expected_result2 = '//%s/' % ''.join([prefix, base_name, '2'])

    self.RunGsUtilTabCompletion(
        ['ls', request], expected_results=[expected_result1, expected_result2])

  def test_single_object(self):
    """Tests tab completion matching a single object."""

    object_name = self.MakeTempName('obj')
    object_uri = self.CreateObject(object_name=object_name, contents=b'data')

    request = '%s://%s/%s' % (self.default_provider, object_uri.bucket_name,
                              object_name[:-2])
    expected_result = '//%s/%s ' % (object_uri.bucket_name, object_name)

    self.RunGsUtilTabCompletion(['ls', request],
                                expected_results=[expected_result])

  def test_multiple_objects(self):
    """Tests tab completion matching multiple objects."""

    bucket_uri = self.CreateBucket()

    object_base_name = self.MakeTempName('obj')
    object1_name = object_base_name + '-suffix1'
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name=object1_name,
                      contents=b'data')
    object2_name = object_base_name + '-suffix2'
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name=object2_name,
                      contents=b'data')

    request = '%s://%s/%s' % (self.default_provider, bucket_uri.bucket_name,
                              object_base_name)
    expected_result1 = '//%s/%s' % (bucket_uri.bucket_name, object1_name)
    expected_result2 = '//%s/%s' % (bucket_uri.bucket_name, object2_name)

    self.RunGsUtilTabCompletion(
        ['ls', request], expected_results=[expected_result1, expected_result2])

  def test_subcommands(self):
    """Tests tab completion for commands with subcommands."""

    bucket_name = self.MakeTempName('bucket', prefix='aaa-')
    self.CreateBucket(bucket_name)

    bucket_request = '%s://%s' % (self.default_provider, bucket_name[:-2])
    expected_bucket_result = '//%s ' % bucket_name

    local_file = 'a_local_file'
    local_dir = self.CreateTempDir(test_files=[local_file])

    local_file_request = '%s%s' % (local_dir, os.sep)
    expected_local_file_result = '%s ' % os.path.join(local_dir, local_file)

    # Should invoke Cloud bucket URL completer.
    self.RunGsUtilTabCompletion(['cors', 'get', bucket_request],
                                expected_results=[expected_bucket_result])

    # Should invoke File URL completer which should match the local file.
    self.RunGsUtilTabCompletion(['cors', 'set', local_file_request],
                                expected_results=[expected_local_file_result])

    # Should invoke Cloud bucket URL completer.
    self.RunGsUtilTabCompletion(['cors', 'set', 'some_file', bucket_request],
                                expected_results=[expected_bucket_result])

  def test_invalid_partial_bucket_name(self):
    """Tests tab completion with a partial URL that by itself is not valid.

    The bucket name in a Cloud URL cannot end in a dash, but a partial URL
    during tab completion may end in a dash and completion should still work.
    """

    bucket_base_name = self.MakeTempName('bucket', prefix='aaa-')
    bucket_name = bucket_base_name + '-s'
    self.CreateBucket(bucket_name)

    request = '%s://%s-' % (self.default_provider, bucket_base_name)
    expected_result = '//%s/' % bucket_name

    self.RunGsUtilTabCompletion(['ls', request],
                                expected_results=[expected_result])

  def test_acl_argument(self):
    """Tests tab completion for ACL arguments."""

    local_file = 'a_local_file'
    local_dir = self.CreateTempDir(test_files=[local_file])

    local_file_request = '%s%s' % (local_dir, os.sep)
    expected_local_file_result = '%s ' % os.path.join(local_dir, local_file)

    # Should invoke File URL completer which should match the local file.
    self.RunGsUtilTabCompletion(['acl', 'set', local_file_request],
                                expected_results=[expected_local_file_result])

    # Should match canned ACL name.
    self.RunGsUtilTabCompletion(['acl', 'set', 'priv'],
                                expected_results=['private '])

    local_file = 'priv_file'
    local_dir = self.CreateTempDir(test_files=[local_file])
    with WorkingDirectory(local_dir):
      # Should match both a file and a canned ACL since argument takes
      # either one.
      self.RunGsUtilTabCompletion(['acl', 'set', 'priv'],
                                  expected_results=[local_file, 'private'])


def _WriteTabCompletionCache(prefix,
                             results,
                             timestamp=None,
                             partial_results=False):
  if timestamp is None:
    timestamp = time.time()
  cache = TabCompletionCache(prefix, results, timestamp, partial_results)
  cache.WriteToFile(GetTabCompletionCacheFilename())


@unittest.skipUnless(ARGCOMPLETE_AVAILABLE,
                     'Tab completion requires argcomplete')
class TestTabCompleteUnitTests(testcase.unit_testcase.GsUtilUnitTestCase):
  """Unit tests for tab completion."""

  def test_cached_results(self):
    """Tests tab completion results returned from cache."""

    with SetBotoConfigForTest([('GSUtil', 'state_dir', self.CreateTempDir())]):
      request = 'gs://prefix'
      cached_results = ['gs://prefix1', 'gs://prefix2']

      _WriteTabCompletionCache(request, cached_results)

      completer = CloudObjectCompleter(self.MakeGsUtilApi())
      results = completer(request)

      self.assertEqual(cached_results, results)

  def test_expired_cached_results(self):
    """Tests tab completion results not returned from cache when too old."""

    with SetBotoConfigForTest([('GSUtil', 'state_dir', self.CreateTempDir())]):
      bucket_base_name = self.MakeTempName('bucket')
      bucket_name = bucket_base_name + '-suffix'
      self.CreateBucket(bucket_name)

      request = '%s://%s' % (self.default_provider, bucket_base_name)
      expected_result = '%s://%s/' % (self.default_provider, bucket_name)

      cached_results = ['//%s1' % bucket_name, '//%s2' % bucket_name]

      _WriteTabCompletionCache(request, cached_results,
                               time.time() - TAB_COMPLETE_CACHE_TTL)

      completer = CloudObjectCompleter(self.MakeGsUtilApi())
      results = completer(request)

      self.assertEqual([expected_result], results)

  def test_prefix_caching(self):
    """Tests tab completion results returned from cache with prefix match.

    If the tab completion prefix is an extension of the cached prefix, tab
    completion should return results from the cache that start with the prefix.
    """

    with SetBotoConfigForTest([('GSUtil', 'state_dir', self.CreateTempDir())]):
      cached_prefix = 'gs://prefix'
      cached_results = ['gs://prefix-first', 'gs://prefix-second']
      _WriteTabCompletionCache(cached_prefix, cached_results)

      request = 'gs://prefix-f'
      completer = CloudObjectCompleter(self.MakeGsUtilApi())
      results = completer(request)

      self.assertEqual(['gs://prefix-first'], results)

  def test_prefix_caching_boundary(self):
    """Tests tab completion prefix caching not spanning directory boundaries.

    If the tab completion prefix is an extension of the cached prefix, but is
    not within the same bucket/sub-directory then the cached results should not
    be used.
    """

    with SetBotoConfigForTest([('GSUtil', 'state_dir', self.CreateTempDir())]):
      object_uri = self.CreateObject(object_name='subdir/subobj',
                                     contents=b'test data')

      cached_prefix = '%s://%s/' % (self.default_provider,
                                    object_uri.bucket_name)
      cached_results = [
          '%s://%s/subdir' % (self.default_provider, object_uri.bucket_name)
      ]
      _WriteTabCompletionCache(cached_prefix, cached_results)

      request = '%s://%s/subdir/' % (self.default_provider,
                                     object_uri.bucket_name)
      expected_result = '%s://%s/subdir/subobj' % (self.default_provider,
                                                   object_uri.bucket_name)

      completer = CloudObjectCompleter(self.MakeGsUtilApi())
      results = completer(request)

      self.assertEqual([expected_result], results)

  def test_prefix_caching_no_results(self):
    """Tests tab completion returning empty result set using cached prefix.

    If the tab completion prefix is an extension of the cached prefix, but does
    not match any of the cached results then no remote request should be made
    and an empty result set should be returned.
    """

    with SetBotoConfigForTest([('GSUtil', 'state_dir', self.CreateTempDir())]):
      object_uri = self.CreateObject(object_name='obj', contents=b'test data')

      cached_prefix = '%s://%s/' % (self.default_provider,
                                    object_uri.bucket_name)
      cached_results = []
      _WriteTabCompletionCache(cached_prefix, cached_results)

      request = '%s://%s/o' % (self.default_provider, object_uri.bucket_name)

      completer = CloudObjectCompleter(self.MakeGsUtilApi())
      results = completer(request)

      self.assertEqual([], results)

  def test_prefix_caching_partial_results(self):
    """Tests tab completion prefix matching ignoring partial cached results.

    If the tab completion prefix is an extension of the cached prefix, but the
    cached result set is partial, the cached results should not be used because
    the matching results for the prefix may be incomplete.
    """

    with SetBotoConfigForTest([('GSUtil', 'state_dir', self.CreateTempDir())]):
      object_uri = self.CreateObject(object_name='obj', contents=b'test data')

      cached_prefix = '%s://%s/' % (self.default_provider,
                                    object_uri.bucket_name)
      cached_results = []
      _WriteTabCompletionCache(cached_prefix,
                               cached_results,
                               partial_results=True)

      request = '%s://%s/o' % (self.default_provider, object_uri.bucket_name)

      completer = CloudObjectCompleter(self.MakeGsUtilApi())
      results = completer(request)

      self.assertEqual([str(object_uri)], results)

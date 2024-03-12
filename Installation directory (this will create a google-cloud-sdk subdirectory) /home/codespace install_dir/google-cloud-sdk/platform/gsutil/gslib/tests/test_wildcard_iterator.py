# -*- coding: utf-8 -*-
# Copyright 2010 Google Inc. All Rights Reserved.
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
"""Unit tests for gsutil wildcard_iterator."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import re
import six
import tempfile

from gslib import wildcard_iterator
from gslib.exception import InvalidUrlError
from gslib.storage_url import ContainsWildcard
from gslib.storage_url import StorageUrlFromString
import gslib.tests.testcase as testcase
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetDummyProjectForUnitTest


class CloudWildcardIteratorTests(testcase.GsUtilUnitTestCase):
  """Unit tests for CloudWildcardIterator."""

  def setUp(self):
    """Creates 2 mock buckets, each containing 4 objects, including 1 nested."""
    super(CloudWildcardIteratorTests, self).setUp()
    self.immed_child_obj_names = ['abcd', 'abdd', 'ade$']
    self.all_obj_names = [
        'abcd', 'abdd', 'ade$', 'nested1/nested2/xyz1', 'nested1/nested2/xyz2',
        'nested1/nested2xyz1', 'nested1/nfile_abc'
    ]

    self.base_bucket_uri = self.CreateBucket()
    self.prefix_bucket_name = '%s_' % self.base_bucket_uri.bucket_name[:61]
    self.base_uri_str = suri(self.base_bucket_uri)
    self.base_uri_str = self.base_uri_str.replace(
        self.base_bucket_uri.bucket_name, self.prefix_bucket_name)

    self.test_bucket0_uri = self.CreateBucket(bucket_name='%s0' %
                                              self.prefix_bucket_name)
    self.test_bucket0_obj_uri_strs = set()
    for obj_name in self.all_obj_names:
      obj_uri = self.CreateObject(bucket_uri=self.test_bucket0_uri,
                                  object_name=obj_name,
                                  contents='')
      self.test_bucket0_obj_uri_strs.add(suri(obj_uri))

    self.test_bucket1_uri = self.CreateBucket(bucket_name='%s1' %
                                              self.prefix_bucket_name)
    self.test_bucket1_obj_uri_strs = set()
    for obj_name in self.all_obj_names:
      obj_uri = self.CreateObject(bucket_uri=self.test_bucket1_uri,
                                  object_name=obj_name,
                                  contents='')
      self.test_bucket1_obj_uri_strs.add(suri(obj_uri))

    self.test_bucket2_uri = self.CreateBucket(bucket_name='%s2' %
                                              self.prefix_bucket_name)
    self.test_bucket2_obj_uri_strs = set()
    object_list = [
        # For testing ** patterns.
        # zf.txt has been added in every folder here to test that it does not
        # get listed for **/f.txt requests.
        'f.txt',
        'double/f.txt',
        'double/zf.txt',
        'double/foo/f.txt',
        'double/foo/zf.txt',
        'double/bar/f.txt',
        'double/bar/zf.txt',
    ]
    for obj_name in object_list:
      obj_uri = self.CreateObject(bucket_uri=self.test_bucket2_uri,
                                  object_name=obj_name,
                                  contents='')
      self.test_bucket2_obj_uri_strs.add(suri(obj_uri))

  def testNoOpObjectIterator(self):
    """Tests that bucket-only URI iterates just that one URI."""
    results = list(
        self._test_wildcard_iterator(
            self.test_bucket0_uri).IterBuckets(bucket_fields=['id']))
    self.assertEqual(1, len(results))
    self.assertEqual(str(self.test_bucket0_uri), str(results[0]))

  def testMatchingAllObjects(self):
    """Tests matching all objects, based on wildcard."""
    actual_obj_uri_strs = set(
        six.ensure_text(str(u)) for u in self._test_wildcard_iterator(
            self.test_bucket0_uri.clone_replace_name('**')).IterAll(
                expand_top_level_buckets=True))
    self.assertEqual(self.test_bucket0_obj_uri_strs, actual_obj_uri_strs)

  def testMatchingObjectSubset(self):
    """Tests matching a subset of objects, based on wildcard."""
    exp_obj_uri_strs = set([
        str(self.test_bucket0_uri.clone_replace_name('abcd')),
        str(self.test_bucket0_uri.clone_replace_name('abdd'))
    ])
    actual_obj_uri_strs = set(
        str(u) for u in self._test_wildcard_iterator(
            self.test_bucket0_uri.clone_replace_name('ab??')).IterAll(
                expand_top_level_buckets=True))
    self.assertEqual(exp_obj_uri_strs, actual_obj_uri_strs)

  def testMatchingNonWildcardedUri(self):
    """Tests matching a single named object."""
    exp_obj_uri_strs = set(
        [str(self.test_bucket0_uri.clone_replace_name('abcd'))])
    actual_obj_uri_strs = set(
        str(u) for u in self._test_wildcard_iterator(
            self.test_bucket0_uri.clone_replace_name('abcd')).IterAll(
                expand_top_level_buckets=True))
    self.assertEqual(exp_obj_uri_strs, actual_obj_uri_strs)

  def testWildcardedObjectUriWithVsWithoutPrefix(self):
    """Tests that wildcarding w/ and w/o server prefix get same result."""
    # (It's just more efficient to query w/o a prefix; wildcard
    # iterator will filter the matches either way.)
    with_prefix_uri_strs = set(
        str(u) for u in self._test_wildcard_iterator(
            self.test_bucket0_uri.clone_replace_name('abcd')).IterAll(
                expand_top_level_buckets=True))
    # By including a wildcard at the start of the string no prefix can be
    # used in server request.
    no_prefix_uri_strs = set(
        str(u) for u in self._test_wildcard_iterator(
            self.test_bucket0_uri.clone_replace_name('?bcd')).IterAll(
                expand_top_level_buckets=True))
    self.assertEqual(with_prefix_uri_strs, no_prefix_uri_strs)

  def testWildcardedObjectUriNestedSubdirMatch(self):
    """Tests wildcarding with a nested subdir."""
    uri_strs = set()
    prefixes = set()
    for blr in self._test_wildcard_iterator(
        self.test_bucket0_uri.clone_replace_name('*')):
      if blr.IsPrefix():
        prefixes.add(blr.root_object)
      else:
        uri_strs.add(blr.url_string)
    exp_obj_uri_strs = set(
        [suri(self.test_bucket0_uri, x) for x in self.immed_child_obj_names])
    self.assertEqual(exp_obj_uri_strs, uri_strs)
    self.assertEqual(1, len(prefixes))
    self.assertTrue('nested1/' in prefixes)

  def testWildcardPlusSubdirMatch(self):
    """Tests gs://bucket/*/subdir matching."""
    actual_uri_strs = set()
    actual_prefixes = set()
    for blr in self._test_wildcard_iterator(
        self.test_bucket0_uri.clone_replace_name('*/nested1')):
      if blr.IsPrefix():
        actual_prefixes.add(blr.root_object)
      else:
        actual_uri_strs.add(blr.url_string)
    expected_uri_strs = set()
    expected_prefixes = set(['nested1/'])
    self.assertEqual(expected_prefixes, actual_prefixes)
    self.assertEqual(expected_uri_strs, actual_uri_strs)

  def testWildcardPlusSubdirSubdirMatch(self):
    """Tests gs://bucket/*/subdir/* matching."""
    actual_uri_strs = set()
    actual_prefixes = set()
    for blr in self._test_wildcard_iterator(
        self.test_bucket0_uri.clone_replace_name('*/nested2/*')):
      if blr.IsPrefix():
        actual_prefixes.add(blr.root_object)
      else:
        actual_uri_strs.add(blr.url_string)
    expected_uri_strs = set([
        self.test_bucket0_uri.clone_replace_name('nested1/nested2/xyz1').uri,
        self.test_bucket0_uri.clone_replace_name('nested1/nested2/xyz2').uri
    ])
    expected_prefixes = set()
    self.assertEqual(expected_prefixes, actual_prefixes)
    self.assertEqual(expected_uri_strs, actual_uri_strs)

  def testNoMatchingWildcardedObjectUri(self):
    """Tests that get back an empty iterator for non-matching wildcarded URI."""
    res = list(
        self._test_wildcard_iterator(
            self.test_bucket0_uri.clone_replace_name('*x0')).IterAll(
                expand_top_level_buckets=True))
    self.assertEqual(0, len(res))

  def testWildcardedInvalidObjectUri(self):
    """Tests that we raise an exception for wildcarded invalid URI."""
    try:
      for unused_ in self._test_wildcard_iterator('badscheme://asdf').IterAll(
          expand_top_level_buckets=True):
        self.assertFalse('Expected InvalidUrlError not raised.')
    except InvalidUrlError as e:
      # Expected behavior.
      self.assertTrue(e.message.find('Unrecognized scheme') != -1)

  def testSingleMatchWildcardedBucketUri(self):
    """Tests matching a single bucket based on a wildcarded bucket URI."""
    exp_obj_uri_strs = set(
        [suri(self.test_bucket1_uri) + self.test_bucket1_uri.delim])
    with SetDummyProjectForUnitTest():
      actual_obj_uri_strs = set(
          str(u)
          for u in self._test_wildcard_iterator('%s*1' %
                                                self.base_uri_str).IterBuckets(
                                                    bucket_fields=['id']))
    self.assertEqual(exp_obj_uri_strs, actual_obj_uri_strs)

  def testMultiMatchWildcardedBucketUri(self):
    """Tests matching a multiple buckets based on a wildcarded bucket URI."""
    exp_obj_uri_strs = set([
        suri(self.test_bucket0_uri) + self.test_bucket0_uri.delim,
        suri(self.test_bucket1_uri) + self.test_bucket1_uri.delim,
        suri(self.test_bucket2_uri) + self.test_bucket2_uri.delim,
    ])
    with SetDummyProjectForUnitTest():
      actual_obj_uri_strs = set(
          str(u)
          for u in self._test_wildcard_iterator('%s*' %
                                                self.base_uri_str).IterBuckets(
                                                    bucket_fields=['id']))
    self.assertEqual(exp_obj_uri_strs, actual_obj_uri_strs)

  def testWildcardBucketAndObjectUri(self):
    """Tests matching with both bucket and object wildcards."""
    exp_obj_uri_strs = set(
        [str(self.test_bucket0_uri.clone_replace_name('abcd'))])
    with SetDummyProjectForUnitTest():
      actual_obj_uri_strs = set(
          str(u) for u in self._test_wildcard_iterator(
              '%s0*/abc*' %
              self.base_uri_str).IterAll(expand_top_level_buckets=True))
    self.assertEqual(exp_obj_uri_strs, actual_obj_uri_strs)

  def testWildcardUpToFinalCharSubdirPlusObjectName(self):
    """Tests wildcard subd*r/obj name."""
    exp_obj_uri_strs = set(
        [str(self.test_bucket0_uri.clone_replace_name('nested1/nested2/xyz1'))])
    actual_obj_uri_strs = set(
        str(u) for u in self._test_wildcard_iterator(
            '%snested1/nest*2/xyz1' %
            self.test_bucket0_uri.uri).IterAll(expand_top_level_buckets=True))
    self.assertEqual(exp_obj_uri_strs, actual_obj_uri_strs)

  def testPostRecursiveWildcard(self):
    """Tests wildcard containing ** followed by an additional wildcard."""
    exp_obj_uri_strs = set(
        [str(self.test_bucket0_uri.clone_replace_name('nested1/nested2/xyz2'))])
    actual_obj_uri_strs = set(
        str(u) for u in self._test_wildcard_iterator(
            '%s**/*y*2' %
            self.test_bucket0_uri.uri).IterAll(expand_top_level_buckets=True))
    self.assertEqual(exp_obj_uri_strs, actual_obj_uri_strs)

  def testWildcardFields(self):
    """Tests that wildcard w/fields specification returns correct fields."""
    blrs = set(u for u in self._test_wildcard_iterator(
        self.test_bucket0_uri.clone_replace_name('**')).IterAll(
            bucket_listing_fields=['timeCreated']))
    self.assertTrue(len(blrs))
    for blr in blrs:
      self.assertTrue(blr.root_object and blr.root_object.timeCreated)
    blrs = set(u for u in self._test_wildcard_iterator(
        self.test_bucket0_uri.clone_replace_name('**')).IterAll(
            bucket_listing_fields=['generation']))
    self.assertTrue(len(blrs))
    for blr in blrs:
      self.assertTrue(blr.root_object and not blr.root_object.timeCreated)

  def testDoesNotStripDelimiterForDoubleWildcard(self):
    """Tests gs://bucket/*/subdir matching."""
    actual_uri_strs = set()
    actual_prefixes = set()
    for blr in self._test_wildcard_iterator(
        self.test_bucket0_uri.clone_replace_name('**/xyz*')):
      if blr.IsPrefix():
        actual_prefixes.add(blr.root_object)
      else:
        actual_uri_strs.add(blr.url_string)
    expected_uri_strs = set([
        self.test_bucket0_uri.clone_replace_name('nested1/nested2/xyz1').uri,
        self.test_bucket0_uri.clone_replace_name('nested1/nested2/xyz2').uri
    ])
    expected_prefixes = set()
    self.assertEqual(expected_prefixes, actual_prefixes)
    self.assertEqual(expected_uri_strs, actual_uri_strs)

  def testDoubleWildcardAfterBucket(self):
    """Tests gs://bucket/**/object matching."""
    actual_uri_strs = set()
    actual_prefixes = set()
    for blr in self._test_wildcard_iterator(
        self.test_bucket2_uri.clone_replace_name('**/f.txt')):
      if blr.IsPrefix():
        actual_prefixes.add(blr.root_object)
      else:
        actual_uri_strs.add(blr.url_string)
    expected_uri_strs = set([
        self.test_bucket2_uri.clone_replace_name('f.txt').uri,
        self.test_bucket2_uri.clone_replace_name('double/f.txt').uri,
        self.test_bucket2_uri.clone_replace_name('double/foo/f.txt').uri,
        self.test_bucket2_uri.clone_replace_name('double/bar/f.txt').uri,
    ])
    expected_prefixes = set()
    self.assertEqual(expected_prefixes, actual_prefixes)
    self.assertEqual(expected_uri_strs, actual_uri_strs)

  def testDoubleWildcardAfterPrefix(self):
    """Tests gs://bucket/dir/**/object matching."""
    actual_uri_strs = set()
    actual_prefixes = set()
    for blr in self._test_wildcard_iterator(
        self.test_bucket2_uri.clone_replace_name('double/**/f.txt')):
      if blr.IsPrefix():
        actual_prefixes.add(blr.root_object)
      else:
        actual_uri_strs.add(blr.url_string)
    expected_uri_strs = set([
        self.test_bucket2_uri.clone_replace_name('double/f.txt').uri,
        self.test_bucket2_uri.clone_replace_name('double/foo/f.txt').uri,
        self.test_bucket2_uri.clone_replace_name('double/bar/f.txt').uri,
    ])
    expected_prefixes = set()
    self.assertEqual(expected_prefixes, actual_prefixes)
    self.assertEqual(expected_uri_strs, actual_uri_strs)

  def testDoubleWildcardBeforeAndAfterPrefix(self):
    """Tests gs://bucket/**/dir/**/object matching."""
    actual_uri_strs = set()
    actual_prefixes = set()
    for blr in self._test_wildcard_iterator(
        self.test_bucket2_uri.clone_replace_name('**/double/**/f.txt')):
      if blr.IsPrefix():
        actual_prefixes.add(blr.root_object)
      else:
        actual_uri_strs.add(blr.url_string)
    expected_uri_strs = set([
        self.test_bucket2_uri.clone_replace_name('double/f.txt').uri,
        self.test_bucket2_uri.clone_replace_name('double/foo/f.txt').uri,
        self.test_bucket2_uri.clone_replace_name('double/bar/f.txt').uri,
    ])
    expected_prefixes = set()
    self.assertEqual(expected_prefixes, actual_prefixes)
    self.assertEqual(expected_uri_strs, actual_uri_strs)


class FileIteratorTests(testcase.GsUtilUnitTestCase):
  """Unit tests for FileWildcardIterator."""

  def setUp(self):
    """Creates a test dir with 3 files and one nested subdirectory + file."""
    super(FileIteratorTests, self).setUp()

    self.test_dir = self.CreateTempDir(
        test_files=['abcd', 'abdd', 'ade$', ('dir1', 'dir2', 'zzz')])

    self.root_files_uri_strs = set([
        suri(self.test_dir, 'abcd'),
        suri(self.test_dir, 'abdd'),
        suri(self.test_dir, 'ade$')
    ])

    self.subdirs_uri_strs = set([suri(self.test_dir, 'dir1')])

    self.nested_files_uri_strs = set(
        [suri(self.test_dir, 'dir1', 'dir2', 'zzz')])

    self.immed_child_uri_strs = self.root_files_uri_strs | self.subdirs_uri_strs
    self.all_file_uri_strs = (self.root_files_uri_strs |
                              self.nested_files_uri_strs)

  def testContainsWildcard(self):
    """Tests ContainsWildcard call."""
    self.assertTrue(ContainsWildcard('a*.txt'))
    self.assertTrue(ContainsWildcard('a[0-9].txt'))
    self.assertFalse(ContainsWildcard('0-9.txt'))
    self.assertTrue(ContainsWildcard('?.txt'))

  def testNoOpDirectoryIterator(self):
    """Tests that directory-only URI iterates just that one URI."""
    results = list(
        self._test_wildcard_iterator(suri(
            tempfile.tempdir)).IterAll(expand_top_level_buckets=True))
    self.assertEqual(1, len(results))
    self.assertEqual(suri(tempfile.tempdir), str(results[0]))

  def testMatchingAllFiles(self):
    """Tests matching all files, based on wildcard."""
    uri = self._test_storage_uri(suri(self.test_dir, '*'))
    actual_uri_strs = set(
        str(u) for u in self._test_wildcard_iterator(uri).IterAll(
            expand_top_level_buckets=True))
    self.assertEqual(self.immed_child_uri_strs, actual_uri_strs)

  def testMatchingAllFilesWithSize(self):
    """Tests matching all files, based on wildcard."""
    uri = self._test_storage_uri(suri(self.test_dir, '*'))
    blrs = self._test_wildcard_iterator(uri).IterAll(
        expand_top_level_buckets=True, bucket_listing_fields=['size'])
    num_expected_objects = 3
    num_actual_objects = 0
    for blr in blrs:
      self.assertTrue(str(blr) in self.immed_child_uri_strs)
      if blr.IsObject():
        num_actual_objects += 1
        # Size is based on contents "Test N" as created by CreateTempDir.
        self.assertEqual(blr.root_object.size, 6)
    self.assertEqual(num_expected_objects, num_actual_objects)

  def testMatchingFileSubset(self):
    """Tests matching a subset of files, based on wildcard."""
    exp_uri_strs = set(
        [suri(self.test_dir, 'abcd'),
         suri(self.test_dir, 'abdd')])
    uri = self._test_storage_uri(suri(self.test_dir, 'ab??'))
    actual_uri_strs = set(
        str(u) for u in self._test_wildcard_iterator(uri).IterAll(
            expand_top_level_buckets=True))
    self.assertEqual(exp_uri_strs, actual_uri_strs)

  def testMatchingNonWildcardedUri(self):
    """Tests matching a single named file."""
    exp_uri_strs = set([suri(self.test_dir, 'abcd')])
    uri = self._test_storage_uri(suri(self.test_dir, 'abcd'))
    actual_uri_strs = set(
        str(u) for u in self._test_wildcard_iterator(uri).IterAll(
            expand_top_level_buckets=True))
    self.assertEqual(exp_uri_strs, actual_uri_strs)

  def testMatchingFilesIgnoringOtherRegexChars(self):
    """Tests ignoring non-wildcard regex chars (e.g., ^ and $)."""

    exp_uri_strs = set([suri(self.test_dir, 'ade$')])
    uri = self._test_storage_uri(suri(self.test_dir, 'ad*$'))
    actual_uri_strs = set(
        str(u) for u in self._test_wildcard_iterator(uri).IterAll(
            expand_top_level_buckets=True))
    self.assertEqual(exp_uri_strs, actual_uri_strs)

  def testRecursiveDirectoryOnlyWildcarding(self):
    """Tests recursive expansion of directory-only '**' wildcard."""
    uri = self._test_storage_uri(suri(self.test_dir, '**'))
    actual_uri_strs = set(
        str(u) for u in self._test_wildcard_iterator(uri).IterAll(
            expand_top_level_buckets=True))
    self.assertEqual(self.all_file_uri_strs, actual_uri_strs)

  def testRecursiveDirectoryPlusFileWildcarding(self):
    """Tests recursive expansion of '**' directory plus '*' wildcard."""
    uri = self._test_storage_uri(suri(self.test_dir, '**', '*'))
    actual_uri_strs = set(
        str(u) for u in self._test_wildcard_iterator(uri).IterAll(
            expand_top_level_buckets=True))
    self.assertEqual(self.all_file_uri_strs, actual_uri_strs)

  def testInvalidRecursiveDirectoryWildcard(self):
    """Tests that wildcard containing '***' raises exception."""
    try:
      uri = self._test_storage_uri(suri(self.test_dir, '***', 'abcd'))
      for unused_ in self._test_wildcard_iterator(uri).IterAll(
          expand_top_level_buckets=True):
        self.fail('Expected WildcardException not raised.')
    except wildcard_iterator.WildcardException as e:
      # Expected behavior.
      self.assertTrue(str(e).find('more than 2 consecutive') != -1)

  def testMissingDir(self):
    """Tests that wildcard gets empty iterator when directory doesn't exist."""
    res = list(
        self._test_wildcard_iterator(suri(
            'no_such_dir', '*')).IterAll(expand_top_level_buckets=True))
    self.assertEqual(0, len(res))

  def testExistingDirNoFileMatch(self):
    """Tests that wildcard returns empty iterator when there's no match."""
    uri = self._test_storage_uri(suri(self.test_dir, 'non_existent*'))
    res = list(
        self._test_wildcard_iterator(uri).IterAll(
            expand_top_level_buckets=True))
    self.assertEqual(0, len(res))

  def testExcludeDir(self):
    """Tests that the exclude regex will omit a nested directory."""
    exp_uri_strs = self.root_files_uri_strs
    uri = self._test_storage_uri(suri(self.test_dir, '**'))
    exclude_tuple = (StorageUrlFromString(self.test_dir), True,
                     re.compile('dir1'))
    actual_uri_strs = set(
        str(u)
        for u in self._test_wildcard_iterator(uri, exclude_tuple=exclude_tuple).
        IterAll(expand_top_level_buckets=True))
    self.assertEqual(exp_uri_strs, actual_uri_strs)

  def testExcludeTupleButExcludeDirFalse(self):
    """Tests that the exclude regex will be disabled by exlude_dirs False."""
    exp_uri_strs = self.all_file_uri_strs
    uri = self._test_storage_uri(suri(self.test_dir, '**'))
    exclude_tuple = (StorageUrlFromString(self.test_dir), False,
                     re.compile('dir1'))
    actual_uri_strs = set(
        str(u)
        for u in self._test_wildcard_iterator(uri, exclude_tuple=exclude_tuple).
        IterAll(expand_top_level_buckets=True))
    self.assertEqual(exp_uri_strs, actual_uri_strs)

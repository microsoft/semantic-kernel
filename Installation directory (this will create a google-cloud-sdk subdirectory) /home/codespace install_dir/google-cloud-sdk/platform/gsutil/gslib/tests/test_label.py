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
"""Integration tests for label command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import json
import xml
from xml.dom.minidom import parseString
from xml.sax import _exceptions as SaxExceptions

import six
import boto
from boto import handler
from boto.s3.tagging import Tags

from gslib.exception import CommandException
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForGS
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import ObjectToURI as suri
from gslib.utils.retry_util import Retry
from gslib.utils.constants import UTF8

KEY1 = 'key_one'
KEY2 = 'key_two'
VALUE1 = 'value_one'
VALUE2 = 'value_two'


def _get_label_setting_output(using_gcloud_storage, bucket_uri):
  return ('Updating {}' if using_gcloud_storage else
          'Setting label configuration on {}/...').format(bucket_uri)


@SkipForGS('Tests use S3-style XML passthrough.')
class TestLabelS3(testcase.GsUtilIntegrationTestCase):
  """S3-specific tests. Most other test cases are covered in TestLabelGS."""

  _label_xml = parseString('<Tagging><TagSet>' + '<Tag><Key>' + KEY1 +
                           '</Key><Value>' + VALUE1 + '</Value></Tag>' +
                           '<Tag><Key>' + KEY2 + '</Key><Value>' + VALUE2 +
                           '</Value></Tag>' +
                           '</TagSet></Tagging>').toprettyxml(indent='    ')

  def setUp(self):
    super(TestLabelS3, self).setUp()
    self.xml_fpath = self.CreateTempFile(contents=self._label_xml.encode(UTF8))

  def DoAssertItemsMatch(self, item1, item2):
    if six.PY2:
      self.assertItemsEqual(item1, item2)
    else:
      # The name was switched, and to a more misleading name, in PY3. Oh well.
      self.assertCountEqual(item1, item2)

  def _LabelDictFromXmlString(self, xml_str):
    label_dict = {}
    tags_list = Tags()
    h = handler.XmlHandler(tags_list, None)
    try:
      xml.sax.parseString(xml_str, h)
    except SaxExceptions.SAXParseException as e:
      raise CommandException(
          'Requested labels/tagging config is invalid: %s at line %s, column '
          '%s' % (e.getMessage(), e.getLineNumber(), e.getColumnNumber()))
    for tagset_list in tags_list:
      for tag in tagset_list:
        label_dict[tag.key] = tag.value
    return label_dict

  def testSetAndGet(self):
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(['label', 'set', self.xml_fpath,
                             suri(bucket_uri)],
                            return_stderr=True)
    expected_output = _get_label_setting_output(self._use_gcloud_storage,
                                                suri(bucket_uri))
    if self._use_gcloud_storage:
      self.assertIn(expected_output, stderr)
    else:
      self.assertEqual(stderr.strip(), expected_output)

    # Verify that the bucket is configured with the labels we just set.
    # Work around eventual consistency for S3 tagging.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['label', 'get', suri(bucket_uri)],
                              return_stdout=True)
      self.DoAssertItemsMatch(self._LabelDictFromXmlString(stdout),
                              self._LabelDictFromXmlString(self._label_xml))

    _Check1()

  def testCh(self):
    bucket_uri = self.CreateBucket()
    self.RunGsUtil([
        'label', 'ch', '-l',
        '%s:%s' % (KEY1, VALUE1), '-l',
        '%s:%s' % (KEY2, VALUE2),
        suri(bucket_uri)
    ])

    # Verify that the bucket is configured with the labels we just set.
    # Work around eventual consistency for S3 tagging.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['label', 'get', suri(bucket_uri)],
                              return_stdout=True)
      self.DoAssertItemsMatch(self._LabelDictFromXmlString(stdout),
                              self._LabelDictFromXmlString(self._label_xml))

    _Check1()

    # Remove KEY1, add a new key, and attempt to remove a nonexistent key
    # with 'label ch'.
    self.RunGsUtil([
        'label', 'ch', '-d', KEY1, '-l', 'new_key:new_value', '-d',
        'nonexistent-key',
        suri(bucket_uri)
    ])
    expected_dict = {KEY2: VALUE2, 'new_key': 'new_value'}

    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check2():
      stdout = self.RunGsUtil(['label', 'get', suri(bucket_uri)],
                              return_stdout=True)
      self.DoAssertItemsMatch(self._LabelDictFromXmlString(stdout),
                              expected_dict)

    _Check2()


@SkipForS3('Tests use GS-style ')
class TestLabelGS(testcase.GsUtilIntegrationTestCase):
  """Integration tests for label command."""

  _label_dict = {KEY1: VALUE1, KEY2: VALUE2}

  def setUp(self):
    super(TestLabelGS, self).setUp()
    self.json_fpath = self.CreateTempFile(
        contents=json.dumps(self._label_dict).encode(UTF8))

  def testSetAndGetOnOneBucket(self):
    bucket_uri = self.CreateBucket()

    # Try setting labels for one bucket.
    stderr = self.RunGsUtil(['label', 'set', self.json_fpath,
                             suri(bucket_uri)],
                            return_stderr=True)
    expected_output = _get_label_setting_output(self._use_gcloud_storage,
                                                suri(bucket_uri))
    if self._use_gcloud_storage:
      self.assertIn(expected_output, stderr)
    else:
      self.assertEqual(stderr.strip(), expected_output)
    # Verify that the bucket is configured with the labels we just set.
    stdout = self.RunGsUtil(['label', 'get', suri(bucket_uri)],
                            return_stdout=True)
    self.assertDictEqual(json.loads(stdout), self._label_dict)

  def testSetOnMultipleBucketsInSameCommand(self):
    bucket_uri = self.CreateBucket()
    bucket2_uri = self.CreateBucket()

    # Try setting labels for multiple buckets in one command.
    stderr = self.RunGsUtil(
        ['label', 'set', self.json_fpath,
         suri(bucket_uri),
         suri(bucket2_uri)],
        return_stderr=True)
    actual = set(stderr.splitlines())
    expected = set([
        _get_label_setting_output(self._use_gcloud_storage, suri(bucket_uri)),
        _get_label_setting_output(self._use_gcloud_storage, suri(bucket2_uri)),
    ])
    if self._use_gcloud_storage:
      # Gcloud may not have exact match because of progress spinner.
      self.assertTrue(all([x in stderr for x in expected]))
    else:
      self.assertSetEqual(actual, expected)

  def testSetOverwritesOldLabelConfig(self):
    bucket_uri = self.CreateBucket()
    # Try setting labels for one bucket.
    self.RunGsUtil(['label', 'set', self.json_fpath, suri(bucket_uri)])
    new_key_1 = 'new_key_1'
    new_key_2 = 'new_key_2'
    new_value_1 = 'new_value_1'
    new_value_2 = 'new_value_2'
    new_json = {
        new_key_1: new_value_1,
        new_key_2: new_value_2,
        KEY1: 'different_value_for_an_existing_key'
    }
    new_json_fpath = self.CreateTempFile(
        contents=json.dumps(new_json).encode('ascii'))
    self.RunGsUtil(['label', 'set', new_json_fpath, suri(bucket_uri)])
    stdout = self.RunGsUtil(['label', 'get', suri(bucket_uri)],
                            return_stdout=True)
    self.assertDictEqual(json.loads(stdout), new_json)

  def testInitialAndSubsequentCh(self):
    bucket_uri = self.CreateBucket()
    ch_subargs = [
        '-l', '%s:%s' % (KEY1, VALUE1), '-l',
        '%s:%s' % (KEY2, VALUE2)
    ]

    # Ensure 'ch' progress message shows in stderr.
    stderr = self.RunGsUtil(['label', 'ch'] + ch_subargs + [suri(bucket_uri)],
                            return_stderr=True)
    expected_output = _get_label_setting_output(self._use_gcloud_storage,
                                                suri(bucket_uri))
    if self._use_gcloud_storage:
      self.assertIn(expected_output, stderr)
    else:
      self.assertEqual(stderr.strip(), expected_output)

    # Check the bucket to ensure it's configured with the labels we just
    # specified.
    stdout = self.RunGsUtil(['label', 'get', suri(bucket_uri)],
                            return_stdout=True)
    self.assertDictEqual(json.loads(stdout), self._label_dict)

    # Ensure a subsequent 'ch' command works correctly.
    new_key = 'new-key'
    new_value = 'new-value'
    self.RunGsUtil([
        'label', 'ch', '-l',
        '%s:%s' % (new_key, new_value), '-d', KEY2,
        suri(bucket_uri)
    ])
    stdout = self.RunGsUtil(['label', 'get', suri(bucket_uri)],
                            return_stdout=True)
    actual = json.loads(stdout)
    expected = {KEY1: VALUE1, new_key: new_value}
    self.assertDictEqual(actual, expected)

  def testChAppliesChangesToAllBucketArgs(self):
    bucket_suris = [suri(self.CreateBucket()), suri(self.CreateBucket())]
    ch_subargs = [
        '-l', '%s:%s' % (KEY1, VALUE1), '-l',
        '%s:%s' % (KEY2, VALUE2)
    ]

    # Ensure 'ch' progress message appears for both buckets in stderr.
    stderr = self.RunGsUtil(['label', 'ch'] + ch_subargs + bucket_suris,
                            return_stderr=True)
    actual = set(stderr.splitlines())
    expected = set([
        _get_label_setting_output(self._use_gcloud_storage, bucket_suri)
        for bucket_suri in bucket_suris
    ])
    if self._use_gcloud_storage:
      self.assertTrue(all([x in stderr for x in expected]))
    else:
      self.assertSetEqual(actual, expected)

    # Check the buckets to ensure both are configured with the labels we
    # just specified.
    for bucket_suri in bucket_suris:
      stdout = self.RunGsUtil(['label', 'get', bucket_suri], return_stdout=True)
      self.assertDictEqual(json.loads(stdout), self._label_dict)

  def testChMinusDWorksWithoutExistingLabels(self):
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(['label', 'ch', '-d', 'dummy-key', suri(bucket_uri)])
    stdout = self.RunGsUtil(['label', 'get', suri(bucket_uri)],
                            return_stdout=True)
    if self._use_gcloud_storage:
      self.assertIn('[]', stdout)
    else:
      self.assertIn('%s/ has no label configuration.' % suri(bucket_uri),
                    stdout)

  def testTooFewArgumentsFails(self):
    """Ensures label commands fail with too few arguments."""
    invocations_missing_args = (
        # Neither arguments nor subcommand.
        ['label'],
        # Not enough arguments for 'set'.
        ['label', 'set'],
        ['label', 'set', 'filename'],
        # Not enough arguments for 'get'.
        ['label', 'get'],
        # Not enough arguments for 'ch'.
        ['label', 'ch'],
        ['label', 'ch', '-l', 'key:val'])
    for arg_list in invocations_missing_args:
      stderr = self.RunGsUtil(arg_list, return_stderr=True, expected_status=1)
      self.assertIn('command requires at least', stderr)

    # Invoking 'ch' without any changes gives a slightly different message.
    stderr = self.RunGsUtil(
        ['label', 'ch', 'gs://some-nonexistent-foobar-bucket-name'],
        return_stderr=True,
        expected_status=1)
    self.assertIn('Please specify at least one label change', stderr)

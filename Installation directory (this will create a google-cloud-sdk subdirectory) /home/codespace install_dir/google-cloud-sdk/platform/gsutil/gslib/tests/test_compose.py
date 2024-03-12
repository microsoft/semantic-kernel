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
"""Tests for compose command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from six.moves import xrange
from six.moves import range

from gslib.commands.compose import MAX_COMPOSE_ARITY
from gslib.cs_api_map import ApiSelector
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import AuthorizeProjectToUseTestingKmsKey
from gslib.tests.util import GenerationFromURI as urigen
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import TEST_ENCRYPTION_KEY1
from gslib.tests.util import TEST_ENCRYPTION_KEY2
from gslib.tests.util import unittest
from gslib.project_id import PopulateProjectId


@SkipForS3('S3 does not support object composition.')
class TestCompose(testcase.GsUtilIntegrationTestCase):
  """Integration tests for compose command."""

  def check_n_ary_compose(self, num_components):
    """Tests composing num_components object."""
    bucket_uri = self.CreateBucket()

    data_list = [
        ('data-%d,' % i).encode('ascii') for i in xrange(num_components)
    ]
    components = [
        self.CreateObject(bucket_uri=bucket_uri, contents=data).uri
        for data in data_list
    ]

    composite = self.StorageUriCloneReplaceName(bucket_uri,
                                                self.MakeTempName('obj'))

    self.RunGsUtil(['compose'] + components + [composite.uri])
    self.assertEqual(composite.get_contents_as_string(), b''.join(data_list))

  def test_compose_too_many_fails(self):
    components = ['gs://b/component-obj'] * (MAX_COMPOSE_ARITY + 1)
    stderr = self.RunGsUtil(['compose'] + components + ['gs://b/composite-obj'],
                            expected_status=1,
                            return_stderr=True)
    self.assertIn('command accepts at most', stderr)

  def test_compose_too_few_fails(self):
    stderr = self.RunGsUtil(
        ['compose', 'gs://b/composite-obj'],
        expected_status=2 if self._use_gcloud_storage else 1,
        return_stderr=True)
    if self._use_gcloud_storage:
      self.assertIn('argument DESTINATION: Must be specified.', stderr)
    else:
      self.assertIn(
          'CommandException: "compose" requires at least 1 component object.\n',
          stderr)

  def test_compose_between_buckets_fails(self):
    bucket_uri_1 = self.CreateBucket()
    bucket_uri_2 = self.CreateBucket()
    object_uri1 = self.CreateObject(bucket_uri=bucket_uri_1, contents=b'1')
    object_uri2 = self.CreateObject(bucket_uri=bucket_uri_2, contents=b'2')
    composite_object_uri = self.StorageUriCloneReplaceName(
        bucket_uri_1, self.MakeTempName('obj'))
    stderr = self.RunGsUtil([
        'compose',
        suri(object_uri1),
        suri(object_uri2),
        suri(composite_object_uri)
    ],
                            expected_status=1,
                            return_stderr=True)
    if self._use_gcloud_storage:
      self.assertIn('Inter-bucket composing not supported\n', stderr)
    else:
      self.assertIn(
          'CommandException: GCS does '
          'not support inter-bucket composing.\n', stderr)

  def test_versioned_target_disallowed(self):
    stderr = self.RunGsUtil(
        ['compose', 'gs://b/o1', 'gs://b/o2', 'gs://b/o3#1234'],
        expected_status=1,
        return_stderr=True)

    if self._use_gcloud_storage:
      self.assertIn(
          'Verison-specific URLs are not valid destinations because composing always results in creating an object with the latest generation.',
          stderr)
    else:
      self.assertIn(
          'CommandException: A version-specific URL (%s) '
          'cannot be the destination for gsutil compose - abort.' %
          'gs://b/o3#1234', stderr)

  def test_simple_compose(self):
    self.check_n_ary_compose(1)
    self.check_n_ary_compose(2)

  def test_compose_copies_type_and_encoding_from_first_object(self):
    bucket_uri = self.CreateBucket()
    object_uri1 = self.CreateObject(bucket_uri=bucket_uri, contents=b'1')
    object_uri2 = self.CreateObject(bucket_uri=bucket_uri, contents=b'2')
    composite = self.StorageUriCloneReplaceName(bucket_uri,
                                                self.MakeTempName('obj'))
    self.RunGsUtil([
        'setmeta', '-h', 'Content-Type:python-x', '-h', 'Content-Encoding:gzip',
        suri(object_uri1)
    ])
    self.RunGsUtil(
        ['compose',
         suri(object_uri1),
         suri(object_uri2),
         suri(composite)])
    stdout = self.RunGsUtil(['stat', suri(composite)], return_stdout=True)
    self.assertRegex(stdout, r'Content-Type:\s+python-x')
    self.assertRegex(stdout, r'Content-Encoding:\s+gzip')

  def test_maximal_compose(self):
    self.check_n_ary_compose(MAX_COMPOSE_ARITY)

  def test_compose_with_wildcard(self):
    """Tests composing objects with a wildcarded URI."""
    bucket_uri = self.CreateBucket()

    component1 = self.CreateObject(bucket_uri=bucket_uri,
                                   contents=b'hello ',
                                   object_name='component1')
    component2 = self.CreateObject(bucket_uri=bucket_uri,
                                   contents=b'world!',
                                   object_name='component2')

    composite = self.StorageUriCloneReplaceName(bucket_uri,
                                                self.MakeTempName('obj'))

    self.RunGsUtil(['compose', component1.uri, component2.uri, composite.uri])
    self.assertEqual(composite.get_contents_as_string(), b'hello world!')

  def test_compose_with_precondition(self):
    """Tests composing objects with a destination precondition."""
    # Tests that cp -v option handles the if-generation-match header correctly.
    bucket_uri = self.CreateVersionedBucket()
    k1_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'data1')
    k2_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'data2')
    g1 = k1_uri.generation

    gen_match_header = 'x-goog-if-generation-match:%s' % g1
    # Append object 1 and 2
    self.RunGsUtil([
        '-h', gen_match_header, 'compose',
        suri(k1_uri),
        suri(k2_uri),
        suri(k1_uri)
    ])

    # Second compose should fail the precondition.
    stderr = self.RunGsUtil([
        '-h', gen_match_header, 'compose',
        suri(k1_uri),
        suri(k2_uri),
        suri(k1_uri)
    ],
                            return_stderr=True,
                            expected_status=1)
    if self._use_gcloud_storage:
      self.assertIn(
          'At least one of the pre-conditions you specified did not hold',
          stderr)
    else:
      self.assertIn('PreconditionException', stderr)

  def test_compose_with_encryption(self):
    """Tests composing encrypted objects."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    bucket_uri = self.CreateBucket()
    object_uri1 = self.CreateObject(bucket_uri=bucket_uri,
                                    contents=b'foo',
                                    encryption_key=TEST_ENCRYPTION_KEY1)
    object_uri2 = self.CreateObject(bucket_uri=bucket_uri,
                                    contents=b'bar',
                                    encryption_key=TEST_ENCRYPTION_KEY1)

    # Compose without correct key should fail.
    stderr = self.RunGsUtil([
        'compose',
        suri(object_uri1),
        suri(object_uri2),
        suri(bucket_uri, 'obj')
    ],
                            expected_status=1,
                            return_stderr=True)
    if self._use_gcloud_storage:
      self.assertIn('Missing decryption key', stderr)
    else:
      self.assertIn('is encrypted by a customer-supplied encryption key',
                    stderr)

    # Compose with different encryption key should fail; source and destination
    # encryption keys must match.
    with SetBotoConfigForTest([
        ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY2),
        ('GSUtil', 'decryption_key1', TEST_ENCRYPTION_KEY1)
    ]):
      stderr = self.RunGsUtil([
          'compose',
          suri(object_uri1),
          suri(object_uri2),
          suri(bucket_uri, 'obj')
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('provided encryption key is incorrect', stderr)

    with SetBotoConfigForTest([('GSUtil', 'encryption_key',
                                TEST_ENCRYPTION_KEY1)]):
      self.RunGsUtil([
          'compose',
          suri(object_uri1),
          suri(object_uri2),
          suri(bucket_uri, 'obj')
      ])

  @SkipForS3('Test uses gs-specific KMS encryption')
  def test_compose_with_kms_encryption(self):
    """Tests composing encrypted objects."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    bucket_uri = self.CreateBucket()
    object_uri1 = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
    object_uri2 = self.CreateObject(bucket_uri=bucket_uri, contents=b'bar')

    obj_suri = suri(bucket_uri, 'composed')
    key_fqn = AuthorizeProjectToUseTestingKmsKey()

    with SetBotoConfigForTest([('GSUtil', 'encryption_key', key_fqn)]):
      self.RunGsUtil([
          'compose',
          suri(object_uri1),
          suri(object_uri2),
          obj_suri,
      ])

    # verify composed object uses CMEK.
    with SetBotoConfigForTest([('GSUtil', 'prefer_api', 'json')]):
      self.AssertObjectUsesCMEK(obj_suri, key_fqn)

  def test_compose_different_encryption_keys(self):
    """Tests composing encrypted objects with different encryption keys."""
    bucket_uri = self.CreateBucket()
    object_uri1 = self.CreateObject(bucket_uri=bucket_uri,
                                    contents=b'foo',
                                    encryption_key=TEST_ENCRYPTION_KEY1)
    object_uri2 = self.CreateObject(bucket_uri=bucket_uri,
                                    contents=b'bar',
                                    encryption_key=TEST_ENCRYPTION_KEY2)

    with SetBotoConfigForTest([
        ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY1),
        ('GSUtil', 'decryption_key1', TEST_ENCRYPTION_KEY2)
    ]):
      stderr = self.RunGsUtil([
          'compose',
          suri(object_uri1),
          suri(object_uri2),
          suri(bucket_uri, 'obj')
      ],
                              expected_status=1,
                              return_stderr=True)

      self.assertIn('The provided encryption key is incorrect', stderr)

    # Should also fail if we don't have the second key.
    with SetBotoConfigForTest([('GSUtil', 'encryption_key',
                                TEST_ENCRYPTION_KEY1)]):
      stderr = self.RunGsUtil([
          'compose',
          suri(object_uri1),
          suri(object_uri2),
          suri(bucket_uri, 'obj')
      ],
                              expected_status=1,
                              return_stderr=True)
      if self._use_gcloud_storage:
        self.assertIn('Missing decryption key', stderr)
      else:
        self.assertIn('The provided encryption key is incorrect', stderr)

  def test_compose_missing_second_source_object(self):
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')

    # Compose with missing source object
    stderr = self.RunGsUtil([
        'compose',
        suri(object_uri),
        suri(bucket_uri, 'nonexistent-obj'),
        suri(bucket_uri, 'valid-destination')
    ],
                            expected_status=1,
                            return_stderr=True)
    if self._use_gcloud_storage:
      self.assertIn('The following URLs matched no objects or files:', stderr)
    else:
      self.assertIn('NotFoundException', stderr)
      if self.test_api == ApiSelector.JSON:
        self.assertIn('One of the source objects does not exist', stderr)

  def test_compose_with_generations(self):
    """Tests composing objects with generations."""
    bucket_uri = self.CreateBucket()
    components = []
    data_list = [b'1', b'2', b'3']
    for data in data_list:
      object_uri = self.CreateObject(bucket_uri=bucket_uri, contents=data)
      components.append(object_uri.version_specific_uri)

    composite = self.StorageUriCloneReplaceName(bucket_uri,
                                                self.MakeTempName('obj'))

    self.RunGsUtil(['compose'] + components + [composite.uri])
    self.assertEqual(composite.get_contents_as_string(), b''.join(data_list))


class TestCompatibleCompose(testcase.GsUtilIntegrationTestCase):

  def test_compose_non_gcs_target(self):
    stderr = self.RunGsUtil(['compose', 'gs://b/o1', 'gs://b/o2', 's3://b/o3'],
                            expected_status=1,
                            return_stderr=True)
    if self._use_gcloud_storage:
      self.assertIn('Composing across providers is not supported.', stderr)
    else:
      expected_msg = ('CommandException: "compose" called on URL with '
                      'unsupported provider (%s).\n' % 's3://b/o3')
      self.assertIn(expected_msg, stderr)

  def test_compose_non_gcs_component(self):
    stderr = self.RunGsUtil(['compose', 'gs://b/o1', 's3://b/o2', 'gs://b/o3'],
                            expected_status=1,
                            return_stderr=True)
    if self._use_gcloud_storage:
      self.assertIn('Composing across providers is not supported.', stderr)
    else:
      expected_msg = ('CommandException: "compose" called on URL with '
                      'unsupported provider (%s).\n' % 's3://b/o2')
      self.assertIn(expected_msg, stderr)

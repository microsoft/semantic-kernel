# -*- coding: utf-8 -*-
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Tests for private service connect custom endpoints."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from boto import config

from gslib.gcs_json_api import DEFAULT_HOST
from gslib.tests import testcase
from gslib.tests.testcase import integration_testcase
from gslib.tests.util import ObjectToURI
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import unittest

# Get full output from stdout, which might not be piped in Python 3.
PYTHON_UNBUFFERED_ENV_VAR = {'PYTHONUNBUFFERED': '1'}


class TestPsc(testcase.GsUtilIntegrationTestCase):
  """Integration tests for PSC custom endpoints."""

  @integration_testcase.SkipForXML('JSON test.')
  @integration_testcase.SkipForS3('Custom endpoints not available for S3.')
  def test_persists_custom_endpoint_through_json_sliced_download(self):
    gs_host = config.get('Credentials', 'gs_json_host', DEFAULT_HOST)
    if gs_host == DEFAULT_HOST:
      # Skips test when run without a custom endpoint configured.
      return

    temporary_directory = self.CreateTempDir()
    with SetBotoConfigForTest([
        ('GSUtil', 'sliced_object_download_threshold', '1B'),
        ('GSUtil', 'sliced_object_download_component_size', '1B')
    ]):
      bucket_uri = self.CreateBucket()
      key_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')

      stdout = self.RunGsUtil(
          ['-DD', 'cp', ObjectToURI(key_uri), temporary_directory],
          env_vars=PYTHON_UNBUFFERED_ENV_VAR,
          return_stdout=True)

    self.assertIn(gs_host, stdout)
    self.assertNotIn(DEFAULT_HOST, stdout)

  @integration_testcase.SkipForJSON('XML test.')
  @integration_testcase.SkipForS3('Custom endpoints not available for S3.')
  def test_persists_custom_endpoint_through_xml_sliced_download(self):
    gs_host = config.get('Credentials', 'gs_host', DEFAULT_HOST)
    if gs_host == DEFAULT_HOST:
      # Skips test when run without a custom endpoint configured.
      return

    temporary_directory = self.CreateTempDir()
    with SetBotoConfigForTest([
        ('GSUtil', 'sliced_object_download_threshold', '1B'),
        ('GSUtil', 'sliced_object_download_component_size', '1B')
    ]):
      bucket_uri = self.CreateBucket()
      key_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
      stdout, stderr = self.RunGsUtil(
          ['-D', 'cp', ObjectToURI(key_uri), temporary_directory],
          return_stdout=True,
          return_stderr=True)

    output = stdout + stderr

    self.assertIn(gs_host, output)
    self.assertNotIn('hostname=' + DEFAULT_HOST, output)

  @integration_testcase.SkipForXML('JSON test.')
  @integration_testcase.SkipForS3('Custom endpoints not available for S3.')
  def test_persists_custom_endpoint_through_json_parallel_composite_upload(
      self):
    gs_host = config.get('Credentials', 'gs_json_host', DEFAULT_HOST)
    if gs_host == DEFAULT_HOST:
      # Skips test when run without a custom endpoint configured.
      return

    temporary_file = self.CreateTempFile(contents=b'foo')
    with SetBotoConfigForTest([
        ('GSUtil', 'parallel_composite_upload_threshold', '1B'),
        ('GSUtil', 'parallel_composite_upload_component_size', '1B')
    ]):
      bucket_uri = self.CreateBucket()
      stdout = self.RunGsUtil(
          ['-DD', 'cp', temporary_file,
           ObjectToURI(bucket_uri)],
          env_vars=PYTHON_UNBUFFERED_ENV_VAR,
          return_stdout=True)

    self.assertIn(gs_host, stdout)
    self.assertNotIn(DEFAULT_HOST, stdout)

  @integration_testcase.SkipForJSON('XML test.')
  @integration_testcase.SkipForS3('Custom endpoints not available for S3.')
  def test_persists_custom_endpoint_through_xml_parallel_composite_upload(self):
    gs_host = config.get('Credentials', 'gs_host', DEFAULT_HOST)
    if gs_host == DEFAULT_HOST:
      # Skips test when run without a custom endpoint configured.
      return

    temporary_file = self.CreateTempFile(contents=b'foo')
    with SetBotoConfigForTest([
        ('GSUtil', 'parallel_composite_upload_threshold', '1B'),
        ('GSUtil', 'parallel_composite_upload_component_size', '1B')
    ]):
      bucket_uri = self.CreateBucket()
      stdout, stderr = self.RunGsUtil(
          ['-D', 'cp', temporary_file,
           ObjectToURI(bucket_uri)],
          return_stdout=True,
          return_stderr=True)

    output = stdout + stderr
    self.assertIn(gs_host, output)
    self.assertNotIn('hostname=' + DEFAULT_HOST, output)

  @integration_testcase.SkipForJSON('XML test.')
  @integration_testcase.SkipForS3('Custom endpoints not available for S3.')
  def test_persists_custom_endpoint_through_resumable_upload(self):
    gs_host = config.get('Credentials', 'gs_host', DEFAULT_HOST)
    if gs_host == DEFAULT_HOST:
      # Skips test when run without a custom endpoint configured.
      return

    temporary_file = self.CreateTempFile(contents=b'foo')
    with SetBotoConfigForTest([('GSUtil', 'resumable_threshold', '1')]):
      bucket_uri = self.CreateBucket()
      stdout, stderr = self.RunGsUtil(
          ['-D', 'cp', temporary_file,
           ObjectToURI(bucket_uri)],
          return_stdout=True,
          return_stderr=True)

    output = stdout + stderr
    self.assertIn(gs_host, output)
    self.assertNotIn('hostname=' + DEFAULT_HOST, output)
# -*- coding: utf-8 -*-
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Tests for mTLS authentication."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from boto import config

from gslib.tests import testcase
from gslib.tests.testcase import integration_testcase
from gslib.tests.util import unittest

MTLS_AVAILABILITY_MESSAGE = (
    'mTLS/DCA authentication is only available for the GCS JSON API.')


class TestMtls(testcase.GsUtilIntegrationTestCase):
  """Integration tests for mTLS authentication."""

  @unittest.skipIf(
      not config.getbool('Credentials', 'use_client_certificate'),
      'mTLS requires "use_client_certificate" to be "True" in .boto config.')
  @integration_testcase.SkipForXML(MTLS_AVAILABILITY_MESSAGE)
  @integration_testcase.SkipForS3(MTLS_AVAILABILITY_MESSAGE)
  def test_can_list_bucket_with_mtls_authentication(self):
    # Cannot use self.CreateBucket because testing framework's authentication
    # doesn't work with mTLS.
    bucket_uri = 'gs://{}'.format(self.MakeTempName('bucket'))
    self.RunGsUtil(['mb', bucket_uri])
    stdout = self.RunGsUtil(['-D', 'ls'], return_stdout=True)
    self.RunGsUtil(['rb', bucket_uri])

    # # Check if mTLS API endpoint was hit in debug output.
    self.assertIn('storage.mtls.googleapis.com', stdout)
    # # If bucket was successfully listed, it implies successful authentication.
    self.assertIn(bucket_uri, stdout)

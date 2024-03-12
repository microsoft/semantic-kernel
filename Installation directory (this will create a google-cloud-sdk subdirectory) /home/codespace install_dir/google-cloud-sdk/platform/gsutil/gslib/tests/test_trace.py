# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Integration tests for gsutil --trace-token option."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib.cs_api_map import ApiSelector
import gslib.tests.testcase as testcase
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.util import ObjectToURI as suri


@SkipForS3('--trace-token is supported only on GCS JSON API.')
class TestTraceTokenOption(testcase.GsUtilIntegrationTestCase):
  """Integration tests for gsutil --trace-token option."""

  def test_minus_tracetoken_cat(self):
    """Tests cat command with trace-token option."""
    key_uri = self.CreateObject(contents=b'0123456789')
    (_, stderr) = self.RunGsUtil(
        ['-D', '--trace-token=THISISATOKEN', 'cat',
         suri(key_uri)],
        return_stdout=True,
        return_stderr=True)
    if self.test_api == ApiSelector.JSON:
      self.assertIn('You are running gsutil with trace output enabled.', stderr)
      self.assertRegex(
          stderr, r'.*GET.*b/%s/o/%s\?.*trace=token%%3ATHISISATOKEN' %
          (key_uri.bucket_name, key_uri.object_name))

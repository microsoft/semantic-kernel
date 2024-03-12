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
"""Tests for gcs_json_api.py."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib import cloud_api
from gslib import gcs_json_api
from gslib import context_config
from gslib.tests import testcase
from gslib.tests.testcase import base
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import unittest

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock


class TestGcsJsonApi(testcase.GsUtilUnitTestCase):
  """Test logic for interacting with GCS JSON API."""

  @mock.patch.object(context_config, 'get_context_config')
  def testSetsHostBaseToMtlsIfClientCertificateEnabled(self,
                                                       mock_get_context_config):
    mock_context_config = mock.Mock()
    mock_context_config.use_client_certificate = True
    mock_get_context_config.return_value = mock_context_config

    with SetBotoConfigForTest([('Credentials', 'gs_json_host', None),
                               ('Credentials', 'gs_host', None)]):
      client = gcs_json_api.GcsJsonApi(None, None, None, None)
      self.assertEqual(client.host_base, gcs_json_api.MTLS_HOST)

  @mock.patch.object(context_config, 'get_context_config')
  def testRaisesErrorIfConflictingJsonAndMtlsHost(self,
                                                  mock_get_context_config):
    mock_context_config = mock.Mock()
    mock_context_config.use_client_certificate = True
    mock_get_context_config.return_value = mock_context_config

    with SetBotoConfigForTest([('Credentials', 'gs_json_host', 'host')]):
      with self.assertRaises(cloud_api.ArgumentException):
        gcs_json_api.GcsJsonApi(None, None, None, None)

  def testSetsCustomJsonHost(self):
    with SetBotoConfigForTest([('Credentials', 'gs_json_host', 'host')]):
      client = gcs_json_api.GcsJsonApi(None, None, None, None)
      self.assertEqual(client.host_base, 'host')

  def testSetsDefaultHost(self):
    with SetBotoConfigForTest([('Credentials', 'gs_json_host', None),
                               ('Credentials', 'gs_host', None)]):
      client = gcs_json_api.GcsJsonApi(None, None, None, None)
      self.assertEqual(client.host_base, gcs_json_api.DEFAULT_HOST)

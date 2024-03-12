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
"""Tests for cloud_api_delegator.py."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from gslib import cloud_api
from gslib import cloud_api_delegator
from gslib import context_config
from gslib import cs_api_map
from gslib.tests import testcase
from gslib.tests.testcase import base
from gslib.tests.util import unittest

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock


class TestCloudApiDelegator(testcase.GsUtilUnitTestCase):
  """Test delegator class for cloud provider API clients."""

  @mock.patch.object(context_config, 'get_context_config')
  def testRaisesErrorIfMtlsUsedWithXml(self, mock_get_context_config):
    mock_context_config = mock.Mock()
    mock_context_config.use_client_certificate = True
    mock_get_context_config.return_value = mock_context_config

    # api_map setup from command_runner.py.
    api_map = cs_api_map.GsutilApiMapFactory.GetApiMap(
        gsutil_api_class_map_factory=cs_api_map.GsutilApiClassMapFactory,
        support_map={'s3': [cs_api_map.ApiSelector.XML]},
        default_map={'s3': cs_api_map.ApiSelector.XML})
    delegator = cloud_api_delegator.CloudApiDelegator(None, api_map, None, None)

    with self.assertRaises(cloud_api.ArgumentException):
      delegator.GetApiSelector(provider='s3')

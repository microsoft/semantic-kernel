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
"""Tests for boto_util.py."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import boto.auth
from gslib import cloud_api
from gslib.utils import boto_util
from gslib import context_config
from gslib.tests import testcase
from gslib.tests.testcase import base
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import unittest

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock


class TestBotoUtil(testcase.GsUtilUnitTestCase):
  """Test utils that make use of the Boto dependency."""

  @mock.patch.object(context_config, 'get_context_config')
  def testSetsHostBaseToMtlsIfClientCertificateEnabled(self,
                                                       mock_get_context_config):
    mock_context_config = mock.Mock()
    mock_context_config.use_client_certificate = True
    mock_context_config.client_cert_path = 'path'
    mock_context_config.client_cert_password = 'password'
    mock_get_context_config.return_value = mock_context_config

    mock_http_class = mock.Mock(return_value=mock.Mock())
    mock_http = boto_util.GetNewHttp(mock_http_class)
    mock_http.add_certificate.assert_called_once_with(
        key='path',
        cert='path',
        domain='',
        password='password',
    )

  @mock.patch.object(boto.auth, 'get_auth_handler', return_value=None)
  def testHasConfiguredCredentialsNoCreds(self, _):
    with SetBotoConfigForTest([
        ('Credentials', 'gs_access_key_id', None),
        ('Credentials', 'gs_secret_access_key', None),
        ('Credentials', 'aws_access_key_id', None),
        ('Credentials', 'aws_secret_access_key', None),
        ('Credentials', 'gs_oauth2_refresh_token', None),
        ('Credentials', 'gs_external_account_file', None),
        ('Credentials', 'gs_external_account_authorized_user_file', None),
        ('Credentials', 'gs_service_client_id', None),
        ('Credentials', 'gs_service_key_file', None),
    ]):
      self.assertFalse(boto_util.HasConfiguredCredentials())

  @mock.patch.object(boto.auth, 'get_auth_handler', return_value=None)
  def testHasConfiguredCredentialsGoogCreds(self, _):
    with SetBotoConfigForTest([
        ('Credentials', 'gs_access_key_id', "?????"),
        ('Credentials', 'gs_secret_access_key', "?????"),
        ('Credentials', 'aws_access_key_id', None),
        ('Credentials', 'aws_secret_access_key', None),
        ('Credentials', 'gs_oauth2_refresh_token', None),
        ('Credentials', 'gs_external_account_file', None),
        ('Credentials', 'gs_external_account_authorized_user_file', None),
        ('Credentials', 'gs_service_client_id', None),
        ('Credentials', 'gs_service_key_file', None),
    ]):
      self.assertTrue(boto_util.HasConfiguredCredentials())

  @mock.patch.object(boto.auth, 'get_auth_handler', return_value=None)
  def testHasConfiguredCredentialsAmznCreds(self, _):
    with SetBotoConfigForTest([
        ('Credentials', 'gs_access_key_id', None),
        ('Credentials', 'gs_secret_access_key', None),
        ('Credentials', 'aws_access_key_id', "?????"),
        ('Credentials', 'aws_secret_access_key', "?????"),
        ('Credentials', 'gs_oauth2_refresh_token', None),
        ('Credentials', 'gs_external_account_file', None),
        ('Credentials', 'gs_external_account_authorized_user_file', None),
        ('Credentials', 'gs_service_client_id', None),
        ('Credentials', 'gs_service_key_file', None),
    ]):
      self.assertTrue(boto_util.HasConfiguredCredentials())

  @mock.patch.object(boto.auth, 'get_auth_handler', return_value=None)
  def testHasConfiguredCredentialsOauthCreds(self, _):
    with SetBotoConfigForTest([
        ('Credentials', 'gs_access_key_id', None),
        ('Credentials', 'gs_secret_access_key', None),
        ('Credentials', 'aws_access_key_id', None),
        ('Credentials', 'aws_secret_access_key', None),
        ('Credentials', 'gs_oauth2_refresh_token', "?????"),
        ('Credentials', 'gs_external_account_file', None),
        ('Credentials', 'gs_external_account_authorized_user_file', None),
        ('Credentials', 'gs_service_client_id', None),
        ('Credentials', 'gs_service_key_file', None),
    ]):
      self.assertTrue(boto_util.HasConfiguredCredentials())

  @mock.patch.object(boto.auth, 'get_auth_handler', return_value=None)
  def testHasConfiguredCredentialsExternalCreds(self, _):
    with SetBotoConfigForTest([
        ('Credentials', 'gs_access_key_id', None),
        ('Credentials', 'gs_secret_access_key', None),
        ('Credentials', 'aws_access_key_id', None),
        ('Credentials', 'aws_secret_access_key', None),
        ('Credentials', 'gs_oauth2_refresh_token', None),
        ('Credentials', 'gs_external_account_file', "?????"),
        ('Credentials', 'gs_external_account_authorized_user_file', None),
        ('Credentials', 'gs_service_client_id', None),
        ('Credentials', 'gs_service_key_file', None),
    ]):
      self.assertTrue(boto_util.HasConfiguredCredentials())

  @mock.patch.object(boto.auth, 'get_auth_handler', return_value=None)
  def testHasConfiguredCredentialsExternalAuthorizedUserCreds(self, _):
    with SetBotoConfigForTest([
        ('Credentials', 'gs_access_key_id', None),
        ('Credentials', 'gs_secret_access_key', None),
        ('Credentials', 'aws_access_key_id', None),
        ('Credentials', 'aws_secret_access_key', None),
        ('Credentials', 'gs_oauth2_refresh_token', None),
        ('Credentials', 'gs_external_account_file', None),
        ('Credentials', 'gs_external_account_authorized_user_file', "?????"),
        ('Credentials', 'gs_service_client_id', None),
        ('Credentials', 'gs_service_key_file', None),
    ]):
      self.assertTrue(boto_util.HasConfiguredCredentials())

  def testUsingGsHmacWithHmacAndServiceAccountCreds(self):
    with SetBotoConfigForTest([
        ('Credentials', 'gs_access_key_id', "?????"),
        ('Credentials', 'gs_secret_access_key', "?????"),
        ('Credentials', 'gs_external_account_file', None),
        ('Credentials', 'gs_external_account_authorized_user_file', None),
        ('Credentials', 'gs_oauth2_refresh_token', None),
        ('Credentials', 'gs_service_client_id', "?????"),
        ('Credentials', 'gs_service_key_file', "?????"),
    ]):
      self.assertFalse(boto_util.UsingGsHmac())

  def testUsingGsHmacWithHmacAndOauth2RefreshToken(self):
    with SetBotoConfigForTest([
        ('Credentials', 'gs_access_key_id', "?????"),
        ('Credentials', 'gs_secret_access_key', "?????"),
        ('Credentials', 'gs_external_account_file', None),
        ('Credentials', 'gs_external_account_authorized_user_file', None),
        ('Credentials', 'gs_oauth2_refresh_token', "?????"),
        ('Credentials', 'gs_service_client_id', None),
        ('Credentials', 'gs_service_key_file', None),
    ]):
      self.assertFalse(boto_util.UsingGsHmac())

  def testUsingGsHmacWithIncompleteHmacOnly(self):
    with SetBotoConfigForTest([
        ('Credentials', 'gs_access_key_id', "?????"),
        ('Credentials', 'gs_secret_access_key', None),
        ('Credentials', 'gs_external_account_file', None),
        ('Credentials', 'gs_external_account_authorized_user_file', None),
        ('Credentials', 'gs_oauth2_refresh_token', None),
        ('Credentials', 'gs_service_client_id', None),
        ('Credentials', 'gs_service_key_file', None),
    ]):
      self.assertFalse(boto_util.UsingGsHmac())

  def testUsingGsHmacWithHmacAndExternalAccountFile(self):
    with SetBotoConfigForTest([
        ('Credentials', 'gs_access_key_id', "?????"),
        ('Credentials', 'gs_secret_access_key', "?????"),
        ('Credentials', 'gs_external_account_file', "?????"),
        ('Credentials', 'gs_external_account_authorized_user_file', None),
        ('Credentials', 'gs_oauth2_refresh_token', None),
        ('Credentials', 'gs_service_client_id', None),
        ('Credentials', 'gs_service_key_file', None),
    ]):
      self.assertTrue(boto_util.UsingGsHmac())

  def testUsingGsHmacWithHmacAndExternalAccountAuthorizedUserFile(self):
    with SetBotoConfigForTest([
        ('Credentials', 'gs_access_key_id', "?????"),
        ('Credentials', 'gs_secret_access_key', "?????"),
        ('Credentials', 'gs_external_account_file', None),
        ('Credentials', 'gs_external_account_authorized_user_file', "?????"),
        ('Credentials', 'gs_oauth2_refresh_token', None),
        ('Credentials', 'gs_service_client_id', None),
        ('Credentials', 'gs_service_key_file', None),
    ]):
      self.assertTrue(boto_util.UsingGsHmac())

  def testUsingGsHmacWithHmacOnly(self):
    with SetBotoConfigForTest([
        ('Credentials', 'gs_access_key_id', "?????"),
        ('Credentials', 'gs_secret_access_key', "?????"),
        ('Credentials', 'gs_external_account_file', None),
        ('Credentials', 'gs_external_account_authorized_user_file', None),
        ('Credentials', 'gs_oauth2_refresh_token', None),
        ('Credentials', 'gs_service_client_id', None),
        ('Credentials', 'gs_service_key_file', None),
    ]):
      self.assertTrue(boto_util.UsingGsHmac())

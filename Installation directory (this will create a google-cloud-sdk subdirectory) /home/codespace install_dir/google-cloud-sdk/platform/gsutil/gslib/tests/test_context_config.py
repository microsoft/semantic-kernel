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
"""Tests for context_config.py."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import json
import os
import subprocess
from unittest import mock

import six

from gslib import context_config
from gslib import exception
from gslib.tests import testcase
from gslib.tests.testcase import base
from gslib.tests.util import SetBotoConfigForTest

DEFAULT_CERT_PROVIDER_FILE_CONTENTS = {
    'cert_provider_command': [
        os.path.join('some', 'helper'), '--print_certificate'
    ]
}

DEFAULT_CERT_PROVIDER_FILE_CONTENTS_WITH_SPACE = {
    'cert_provider_command': ['some helper', '--print_certificate']
}

DEFAULT_CERT_PROVIDER_FILE_NO_COMMAND = {'foo': 'foo'}

CERT_SECTION = """-----BEGIN CERTIFICATE-----
LKJHLSDJKFHLEUIORWUYERWEHJHL
KLJHGFDLSJKH(@#*&$)@*#KJHFLKJDSFSD
-----END CERTIFICATE-----
"""
ENCRYPTED_KEY_SECTION = """-----BEGIN ENCRYPTED PRIVATE KEY-----
LKJWE:RUWEORIU)(#*&$@(#$KJHLKDJHF(I*F@YLFHSLDKJFS
-----END ENCRYPTED PRIVATE KEY-----
"""
KEY_SECTION = """-----BEGIN PRIVATE KEY-----
LKJWE:RUWEORIU)(#*&$@(#$KJHLKDJHF(I*F@YLFHSLDKJFS
-----END PRIVATE KEY-----
"""
CERT_ENCRYPTED_KEY_SECTION = CERT_SECTION + ENCRYPTED_KEY_SECTION
PASSWORD = '##invalid-password##'
PASSWORD_SECTION = """
-----BEGIN PASSPHRASE-----
%s
-----END PASSPHRASE-----
""" % PASSWORD
FULL_ENCRYPTED_CERT = CERT_ENCRYPTED_KEY_SECTION + PASSWORD_SECTION
FULL_CERT = CERT_SECTION + KEY_SECTION

BAD_CERT_KEY_EMBEDDED_SECTION = """-----BEGIN CERTIFICATE-----
LKJHLSDJKFHLEUIORWUYERWEHJHL
KLJHGFDLSJKH(@#*&$)@*#KJHFLKJDSFSD
-----BEGIN ENCRYPTED PRIVATE KEY-----
LKJWE:RUWEORIU)(#*&$@(#$KJHLKDJHF(I*F@YLFHSLDKJFS
-----END ENCRYPTED PRIVATE KEY-----
-----END CERTIFICATE-----
"""
BAD_CERT_KEY_MISSING_END = """-----BEGIN CERTIFICATE-----
LKJHLSDJKFHLEUIORWUYERWEHJHL
KLJHGFDLSJKH(@#*&$)@*#KJHFLKJDSFSD
-----END CERTIFICATE-----
-----BEGIN ENCRYPTED PRIVATE KEY-----
LKJWE:RUWEORIU)(#*&$@(#$KJHLKDJHF(I*F@YLFHSLDKJFS
"""
BAD_CERT_KEY_MISSING_BEGIN = """-----END CERTIFICATE-----
-----BEGIN ENCRYPTED PRIVATE KEY-----
LKJWE:RUWEORIU)(#*&$@(#$KJHLKDJHF(I*F@YLFHSLDKJFS
-----END ENCRYPTED PRIVATE KEY-----
"""
BAD_CERT_KEY_MISMATCH = """-----BEGIN CERTIFICATE-----
LKJHLSDJKFHLEUIORWUYERWEHJHL
KLJHGFDLSJKH(@#*&$)@*#KJHFLKJDSFSD
-----END ENCRYPTED PRIVATE KEY-----
"""
CERT_KEY_WITH_COMMENT_AT_BEGIN = """SOMECOMMENTS
-----BEGIN CERTIFICATE-----
LKJHLSDJKFHLEUIORWUYERWEHJHL
KLJHGFDLSJKH(@#*&$)@*#KJHFLKJDSFSD
-----END CERTIFICATE-----
-----BEGIN ENCRYPTED PRIVATE KEY-----
LKJWE:RUWEORIU)(#*&$@(#$KJHLKDJHF(I*F@YLFHSLDKJFS
-----END ENCRYPTED PRIVATE KEY-----
"""
CERT_KEY_WITH_COMMENT_AT_END = """-----BEGIN CERTIFICATE-----
LKJHLSDJKFHLEUIORWUYERWEHJHL
KLJHGFDLSJKH(@#*&$)@*#KJHFLKJDSFSD
-----END CERTIFICATE-----
-----BEGIN ENCRYPTED PRIVATE KEY-----
LKJWE:RUWEORIU)(#*&$@(#$KJHLKDJHF(I*F@YLFHSLDKJFS
-----END ENCRYPTED PRIVATE KEY-----
SOMECOMMENT
"""
CERT_KEY_WITH_COMMENT_IN_BETWEEN = """-----BEGIN CERTIFICATE-----
LKJHLSDJKFHLEUIORWUYERWEHJHL
KLJHGFDLSJKH(@#*&$)@*#KJHFLKJDSFSD
-----END CERTIFICATE-----
SOMECOMMENT
-----BEGIN ENCRYPTED PRIVATE KEY-----
LKJWE:RUWEORIU)(#*&$@(#$KJHLKDJHF(I*F@YLFHSLDKJFS
-----END ENCRYPTED PRIVATE KEY-----
"""

OPEN_TO_PATCH = '__builtin__.open' if six.PY2 else 'builtins.open'


@testcase.integration_testcase.SkipForS3('mTLS only runs on GCS JSON API.')
@testcase.integration_testcase.SkipForXML('mTLS only runs on GCS JSON API.')
class TestPemFileParser(testcase.GsUtilUnitTestCase):
  """Test PEM-format certificate parsing for mTLS."""

  def test_pem_file_with_comment_at_beginning(self):
    sections = context_config._split_pem_into_sections(
        CERT_KEY_WITH_COMMENT_AT_BEGIN, self.logger)
    self.assertEqual(sections['CERTIFICATE'], CERT_SECTION)
    self.assertEqual(sections['ENCRYPTED PRIVATE KEY'], ENCRYPTED_KEY_SECTION)

  def test_pem_file_with_comment_at_end(self):
    sections = context_config._split_pem_into_sections(
        CERT_KEY_WITH_COMMENT_AT_END, self.logger)
    self.assertEqual(sections['CERTIFICATE'], CERT_SECTION)
    self.assertEqual(sections['ENCRYPTED PRIVATE KEY'], ENCRYPTED_KEY_SECTION)

  def test_pem_file_with_comment_in_between(self):
    sections = context_config._split_pem_into_sections(
        CERT_KEY_WITH_COMMENT_IN_BETWEEN, self.logger)
    self.assertEqual(sections['CERTIFICATE'], CERT_SECTION)
    self.assertEqual(sections['ENCRYPTED PRIVATE KEY'], ENCRYPTED_KEY_SECTION)

  def test_pem_file_with_bad_format_embedded_section(self):
    sections = context_config._split_pem_into_sections(
        BAD_CERT_KEY_EMBEDDED_SECTION, self.logger)
    self.assertIsNone(sections.get('CERTIFICATE'))
    self.assertEqual(sections.get('ENCRYPTED PRIVATE KEY'),
                     ENCRYPTED_KEY_SECTION)

  def test_pem_file_with_bad_format_missing_ending(self):
    sections = context_config._split_pem_into_sections(BAD_CERT_KEY_MISSING_END,
                                                       self.logger)
    self.assertEqual(sections.get('CERTIFICATE'), CERT_SECTION)
    self.assertIsNone(sections.get('ENCRYPTED PRIVATE KEY'))

  def test_pem_file_with_bad_format_missing_beginning(self):
    sections = context_config._split_pem_into_sections(
        BAD_CERT_KEY_MISSING_BEGIN, self.logger)
    self.assertIsNone(sections.get('CERTIFICATE'))
    self.assertEqual(sections.get('ENCRYPTED PRIVATE KEY'),
                     ENCRYPTED_KEY_SECTION)

  def test_pem_file_with_bad_format_section_mismatch(self):
    sections = context_config._split_pem_into_sections(BAD_CERT_KEY_MISMATCH,
                                                       self.logger)
    self.assertIsNone(sections.get('CERTIFICATE'))
    self.assertIsNone(sections.get('ENCRYPTED PRIVATE KEY'))


# Setting global context_config singleton causes issues in parallel.
@base.NotParallelizable
@testcase.integration_testcase.SkipForS3('mTLS only runs on GCS JSON API.')
@testcase.integration_testcase.SkipForXML('mTLS only runs on GCS JSON API.')
class TestContextConfig(testcase.GsUtilUnitTestCase):
  """Test the global ContextConfig singleton."""

  def setUp(self):
    super(TestContextConfig, self).setUp()
    self._old_context_config = context_config._singleton_config
    context_config._singleton_config = None

    self.mock_logger = mock.Mock()

  def tearDown(self):
    super(TestContextConfig, self).tearDown()
    context_config._singleton_config = self._old_context_config

  def test_context_config_is_a_singleton(self):
    first = context_config.create_context_config(self.mock_logger)

    with self.assertRaises(
        context_config.ContextConfigSingletonAlreadyExistsError):
      context_config.create_context_config(self.mock_logger)

    second = context_config.get_context_config()
    self.assertEqual(first, second)

  @mock.patch.object(subprocess, 'Popen')
  def test_does_not_provision_if_use_client_certificate_not_true(
      self, mock_Popen):
    context_config.create_context_config(self.mock_logger)
    mock_Popen.assert_not_called()

  @mock.patch('os.path.exists', new=mock.Mock(return_value=True))
  @mock.patch.object(json, 'load', autospec=True)
  @mock.patch.object(subprocess, 'Popen', autospec=True)
  @mock.patch(OPEN_TO_PATCH, new_callable=mock.mock_open)
  def test_executes_provider_command_from_default_file(self, mock_open,
                                                       mock_Popen,
                                                       mock_json_load):
    mock_json_load.side_effect = [DEFAULT_CERT_PROVIDER_FILE_CONTENTS]
    with SetBotoConfigForTest([('Credentials', 'use_client_certificate', 'True')
                              ]):
      # Purposely end execution here to avoid writing a file.
      with self.assertRaises(ValueError):
        context_config.create_context_config(self.mock_logger)

        mock_open.assert_called_with(context_config._DEFAULT_METADATA_PATH)
        mock_Popen.assert_called_once_with(
            os.path.realpath(os.path.join('some', 'helper')),
            '--print_certificate', '--with_passphrase')

  @mock.patch('os.path.exists', new=mock.Mock(return_value=True))
  @mock.patch.object(json, 'load', autospec=True)
  @mock.patch.object(subprocess, 'Popen', autospec=True)
  @mock.patch(OPEN_TO_PATCH, new_callable=mock.mock_open)
  def test_executes_provider_command_with_space_from_default_file(
      self, mock_open, mock_Popen, mock_json_load):
    mock_json_load.side_effect = [
        DEFAULT_CERT_PROVIDER_FILE_CONTENTS_WITH_SPACE
    ]
    with SetBotoConfigForTest([('Credentials', 'use_client_certificate',
                                'True'),
                               ('Credentials', 'cert_provider_command', None)]):
      # Purposely end execution here to avoid writing a file.
      with self.assertRaises(ValueError):
        context_config.create_context_config(self.mock_logger)

        mock_open.assert_called_with(context_config._DEFAULT_METADATA_PATH)
        mock_Popen.assert_called_once_with(os.path.realpath('cert helper'),
                                           '--print_certificate',
                                           '--with_passphrase')

  @mock.patch('os.path.exists', new=mock.Mock(return_value=True))
  @mock.patch.object(json, 'load', autospec=True)
  @mock.patch(OPEN_TO_PATCH, new_callable=mock.mock_open)
  def test_default_provider_no_command_error(self, mock_open, mock_json_load):
    mock_json_load.return_value = DEFAULT_CERT_PROVIDER_FILE_NO_COMMAND

    with SetBotoConfigForTest([('Credentials', 'use_client_certificate',
                                'True'),
                               ('Credentials', 'cert_provider_command', None)]):
      context_config.create_context_config(self.mock_logger)

      mock_open.assert_called_with(context_config._DEFAULT_METADATA_PATH)
      self.mock_logger.error.assert_called_once_with(
          "Failed to provision client certificate: "
          "Client certificate provider command not found.")

  @mock.patch('os.path.exists', new=mock.Mock(return_value=False))
  def test_default_provider_not_found_error(self):
    with SetBotoConfigForTest([
        ('Credentials', 'use_client_certificate', 'True'),
        ('Credentials', 'cert_provider_command', None),
        # Avoids permissions error on Windows tests:
        ('GSUtil', 'state_dir', self.CreateTempDir())
    ]):
      context_config.create_context_config(self.mock_logger)

      self.mock_logger.error.assert_called_once_with(
          "Failed to provision client certificate: "
          "Client certificate provider file not found.")

  @mock.patch.object(json, 'load', autospec=True)
  @mock.patch('os.path.exists', new=mock.Mock(return_value=True))
  @mock.patch(OPEN_TO_PATCH, new_callable=mock.mock_open)
  def test_raises_cert_provision_error_on_json_load_error(
      self, mock_open, mock_json_load):
    mock_json_load.side_effect = ValueError('valueError')
    with SetBotoConfigForTest([('Credentials', 'use_client_certificate',
                                'True'),
                               ('Credentials', 'cert_provider_command', None)]):
      context_config.create_context_config(self.mock_logger)
      mock_open.assert_called_with(context_config._DEFAULT_METADATA_PATH)
      self.mock_logger.error.assert_called_once_with(
          'Failed to provision client certificate: valueError')

  @mock.patch.object(subprocess, 'Popen', autospec=True)
  def test_executes_custom_provider_command_from_boto_config(self, mock_Popen):
    with SetBotoConfigForTest([
        ('Credentials', 'use_client_certificate', 'True'),
        ('Credentials', 'cert_provider_command', 'some/path')
    ]):
      # Purposely end execution here to avoid writing a file.
      with self.assertRaises(ValueError):
        context_config.create_context_config(self.mock_logger)

        mock_Popen.assert_called_once_with(os.path.realpath('some/path'),
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)

  @mock.patch.object(subprocess, 'Popen')
  def test_converts_and_logs_provisioning_cert_provider_unexpected_exit_error(
      self, mock_Popen):
    mock_command_process = mock.Mock()
    mock_command_process.communicate.return_value = (None, 'oh no')
    mock_Popen.return_value = mock_command_process

    with SetBotoConfigForTest([
        ('Credentials', 'use_client_certificate', 'True'),
        ('Credentials', 'cert_provider_command', 'some/path')
    ]):
      context_config.create_context_config(self.mock_logger)
      self.mock_logger.error.assert_called_once_with(
          'Failed to provision client certificate: oh no')

  @mock.patch.object(subprocess, 'Popen')
  def test_converts_and_logs_provisioning_os_error(self, mock_Popen):
    mock_Popen.side_effect = OSError('foobar')

    with SetBotoConfigForTest([
        ('Credentials', 'use_client_certificate', 'True'),
        ('Credentials', 'cert_provider_command', 'some/path')
    ]):
      context_config.create_context_config(self.mock_logger)
      self.mock_logger.error.assert_called_once_with(
          'Failed to provision client certificate: foobar')

  @mock.patch.object(subprocess, 'Popen')
  def test_converts_and_logs_provisioning_external_binary_error(
      self, mock_Popen):
    mock_Popen.side_effect = exception.ExternalBinaryError('foobar')

    with SetBotoConfigForTest([
        ('Credentials', 'use_client_certificate', 'True'),
        ('Credentials', 'cert_provider_command', 'some/path')
    ]):
      context_config.create_context_config(self.mock_logger)
      self.mock_logger.error.assert_called_once_with(
          'Failed to provision client certificate: foobar')

  @mock.patch.object(subprocess, 'Popen')
  def test_converts_and_logs_provisioning_key_error(self, mock_Popen):
    # Mocking f.write would make more sense, but mocking Popen earlier in the
    # function results in much less code and tests the same error handling.
    mock_Popen.side_effect = KeyError('foobar')

    with SetBotoConfigForTest([
        ('Credentials', 'use_client_certificate', 'True'),
        ('Credentials', 'cert_provider_command', 'some/path')
    ]):
      context_config.create_context_config(self.mock_logger)

      unicode_escaped_error_string = "'foobar'" if six.PY3 else "u'foobar'"
      self.mock_logger.error.assert_called_once_with(
          "Failed to provision client certificate:"
          " Invalid output format from certificate provider, no " +
          unicode_escaped_error_string)

  @mock.patch.object(os, 'remove')
  def test_does_not_unprovision_if_no_client_certificate(self, mock_remove):
    context_config.create_context_config(self.mock_logger)
    context_config._singleton_config._unprovision_client_cert()
    mock_remove.assert_not_called()

  @mock.patch.object(os, 'remove')
  def test_handles_and_logs_unprovisioning_os_error(self, mock_remove):
    mock_remove.side_effect = OSError('no')

    context_config.create_context_config(self.mock_logger)
    context_config._singleton_config.client_cert_path = 'some/path'
    context_config._singleton_config._unprovision_client_cert()

    self.mock_logger.error.assert_called_once_with(
        'Failed to remove client certificate: no')

  @mock.patch(OPEN_TO_PATCH, new_callable=mock.mock_open)
  @mock.patch.object(os, 'remove')
  @mock.patch.object(subprocess, 'Popen')
  def test_writes_and_deletes_encrypted_certificate_file_storing_password_to_memory(
      self, mock_Popen, mock_remove, mock_open):
    mock_command_process = mock.Mock()
    mock_command_process.returncode = 0
    mock_command_process.communicate.return_value = (
        FULL_ENCRYPTED_CERT.encode(), None)
    mock_Popen.return_value = mock_command_process

    with SetBotoConfigForTest([
        ('Credentials', 'use_client_certificate', 'True'),
        ('Credentials', 'cert_provider_command', 'path --print_certificate')
    ]):
      # Mock logger argument to avoid atexit hook writing to stderr.
      test_config = context_config.create_context_config(mock.Mock())

      # Test writes certificate file.
      # Can't check whole mock_calls list because SetBotoConfigForTest also
      # uses the mock in Python 3. Should work with any_order=False based on
      # docs description but does not in current environment.
      mock_open.assert_has_calls([
          mock.call(test_config.client_cert_path, 'w+'),
          mock.call().write(CERT_SECTION),
          mock.call().write(ENCRYPTED_KEY_SECTION),
      ],
                                 any_order=True)
      # Test saves certificate password to memory.
      self.assertEqual(context_config._singleton_config.client_cert_password,
                       PASSWORD)
      # Test deletes certificate file.
      context_config._singleton_config._unprovision_client_cert()
      mock_remove.assert_called_once_with(test_config.client_cert_path)

  @mock.patch(OPEN_TO_PATCH, new_callable=mock.mock_open)
  @mock.patch.object(os, 'remove')
  @mock.patch.object(subprocess, 'Popen')
  def test_writes_and_deletes_unencrypted_certificate_file_without_storing_password(
      self, mock_Popen, mock_remove, mock_open):
    """This is the format used by gcloud by default."""
    mock_command_process = mock.Mock()
    mock_command_process.returncode = 0
    mock_command_process.communicate.return_value = (FULL_CERT.encode(), None)
    mock_Popen.return_value = mock_command_process

    with SetBotoConfigForTest([
        ('Credentials', 'use_client_certificate', 'True'),
        ('Credentials', 'cert_provider_command', 'path --print_certificate')
    ]):
      # Mock logger argument to avoid atexit hook writing to stderr.
      test_config = context_config.create_context_config(mock.Mock())

      # Test writes certificate file.
      # Can't check whole mock_calls list because SetBotoConfigForTest also
      # uses the mock in Python 3. Should work with any_order=False based on
      # docs description but does not in current environment.
      mock_open.assert_has_calls([
          mock.call(test_config.client_cert_path, 'w+'),
          mock.call().write(CERT_SECTION),
          mock.call().write(KEY_SECTION),
      ],
                                 any_order=True)
      # Does not save unnecessary password.
      self.assertIsNone(context_config._singleton_config.client_cert_password,
                        PASSWORD)
      # Test deletes certificate file.
      context_config._singleton_config._unprovision_client_cert()
      mock_remove.assert_called_once_with(test_config.client_cert_path)

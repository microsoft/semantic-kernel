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
"""Integration tests for cp command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import ast
import base64
import binascii
import datetime
import gzip
import logging
import os
import pickle
import pkgutil
import random
import re
import stat
import string
import sys
import threading
from unittest import mock

from apitools.base.py import exceptions as apitools_exceptions
import boto
from boto import storage_uri
from boto.exception import ResumableTransferDisposition
from boto.exception import StorageResponseError
from boto.storage_uri import BucketStorageUri

from gslib import command
from gslib import exception
from gslib import name_expansion
from gslib.cloud_api import ResumableUploadStartOverException
from gslib.commands.config import DEFAULT_SLICED_OBJECT_DOWNLOAD_THRESHOLD
from gslib.commands.cp import ShimTranslatePredefinedAclSubOptForCopy
from gslib.cs_api_map import ApiSelector
from gslib.daisy_chain_wrapper import _DEFAULT_DOWNLOAD_CHUNK_SIZE
from gslib.discard_messages_queue import DiscardMessagesQueue
from gslib.exception import InvalidUrlError
from gslib.gcs_json_api import GcsJsonApi
from gslib.parallel_tracker_file import ObjectFromTracker
from gslib.parallel_tracker_file import WriteParallelUploadTrackerFile
from gslib.project_id import PopulateProjectId
from gslib.storage_url import StorageUrlFromString
from gslib.tests.rewrite_helper import EnsureRewriteResumeCallbackHandler
from gslib.tests.rewrite_helper import HaltingRewriteCallbackHandler
from gslib.tests.rewrite_helper import RewriteHaltException
import gslib.tests.testcase as testcase
from gslib.tests.testcase.base import NotParallelizable
from gslib.tests.testcase.integration_testcase import SkipForGS
from gslib.tests.testcase.integration_testcase import SkipForS3
from gslib.tests.testcase.integration_testcase import SkipForXML
from gslib.tests.testcase.integration_testcase import SkipForJSON
from gslib.tests.util import AuthorizeProjectToUseTestingKmsKey
from gslib.tests.util import BuildErrorRegex
from gslib.tests.util import GenerationFromURI as urigen
from gslib.tests.util import HaltingCopyCallbackHandler
from gslib.tests.util import HaltOneComponentCopyCallbackHandler
from gslib.tests.util import HAS_GS_PORT
from gslib.tests.util import HAS_S3_CREDS
from gslib.tests.util import KmsTestingResources
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import ORPHANED_FILE
from gslib.tests.util import POSIX_GID_ERROR
from gslib.tests.util import POSIX_INSUFFICIENT_ACCESS_ERROR
from gslib.tests.util import POSIX_MODE_ERROR
from gslib.tests.util import POSIX_UID_ERROR
from gslib.tests.util import SequentialAndParallelTransfer
from gslib.tests.util import SetBotoConfigForTest
from gslib.tests.util import SetEnvironmentForTest
from gslib.tests.util import TailSet
from gslib.tests.util import TEST_ENCRYPTION_KEY1
from gslib.tests.util import TEST_ENCRYPTION_KEY1_SHA256_B64
from gslib.tests.util import TEST_ENCRYPTION_KEY2
from gslib.tests.util import TEST_ENCRYPTION_KEY3
from gslib.tests.util import unittest
from gslib.third_party.storage_apitools import storage_v1_messages as apitools_messages
from gslib.tracker_file import DeleteTrackerFile
from gslib.tracker_file import GetRewriteTrackerFilePath
from gslib.tracker_file import GetSlicedDownloadTrackerFilePaths
from gslib.ui_controller import BytesToFixedWidthString
from gslib.utils import hashing_helper
from gslib.utils.boto_util import UsingCrcmodExtension
from gslib.utils.constants import START_CALLBACK_PER_BYTES
from gslib.utils.constants import UTF8
from gslib.utils.copy_helper import GetTrackerFilePath
from gslib.utils.copy_helper import PARALLEL_UPLOAD_STATIC_SALT
from gslib.utils.copy_helper import PARALLEL_UPLOAD_TEMP_NAMESPACE
from gslib.utils.copy_helper import TrackerFileType
from gslib.utils.hashing_helper import CalculateB64EncodedMd5FromContents
from gslib.utils.hashing_helper import CalculateMd5FromContents
from gslib.utils.hashing_helper import GetMd5
from gslib.utils.metadata_util import CreateCustomMetadata
from gslib.utils.posix_util import GID_ATTR
from gslib.utils.posix_util import MODE_ATTR
from gslib.utils.posix_util import NA_ID
from gslib.utils.posix_util import NA_MODE
from gslib.utils.posix_util import UID_ATTR
from gslib.utils.posix_util import ParseAndSetPOSIXAttributes
from gslib.utils.posix_util import ValidateFilePermissionAccess
from gslib.utils.posix_util import ValidatePOSIXMode
from gslib.utils.retry_util import Retry
from gslib.utils.system_util import IS_WINDOWS
from gslib.utils.text_util import get_random_ascii_chars
from gslib.utils.unit_util import EIGHT_MIB
from gslib.utils.unit_util import HumanReadableToBytes
from gslib.utils.unit_util import MakeHumanReadable
from gslib.utils.unit_util import ONE_KIB
from gslib.utils.unit_util import ONE_MIB
from gslib.utils import shim_util

import six
from six.moves import http_client
from six.moves import range
from six.moves import xrange

if six.PY3:
  long = int  # pylint: disable=redefined-builtin,invalid-name

# These POSIX-specific variables aren't defined for Windows.
# pylint: disable=g-import-not-at-top
if not IS_WINDOWS:
  from gslib.tests import util
  from gslib.tests.util import DEFAULT_MODE
  from gslib.tests.util import GetInvalidGid
  from gslib.tests.util import GetNonPrimaryGid
  from gslib.tests.util import GetPrimaryGid
  from gslib.tests.util import INVALID_UID
  from gslib.tests.util import USER_ID
# pylint: enable=g-import-not-at-top

# (status_code, error_prefix, error_substring)
_GCLOUD_STORAGE_GZIP_FLAG_CONFLICT_OUTPUT = (
    2, 'ERROR',
    'At most one of --gzip-in-flight | --gzip-in-flight-all | --gzip-local |'
    ' --gzip-local-all can be specified')


def TestCpMvPOSIXBucketToLocalErrors(cls, bucket_uri, obj, tmpdir, is_cp=True):
  """Helper function for preserve_posix_errors tests in test_cp and test_mv.

  Args:
    cls: An instance of either TestCp or TestMv.
    bucket_uri: The uri of the bucket that the object is in.
    obj: The object to run the tests on.
    tmpdir: The local file path to cp to.
    is_cp: Whether or not the calling test suite is cp or mv.
  """
  error_key = 'error_regex'
  if cls._use_gcloud_storage:
    insufficient_access_error = no_read_access_error = re.compile(
        r"User \d+ owns file, but owner does not have read permission")
    missing_gid_error = re.compile(
        r"GID in .* metadata doesn't exist on current system")
    missing_uid_error = re.compile(
        r"UID in .* metadata doesn't exist on current system")
  else:
    insufficient_access_error = BuildErrorRegex(
        obj, POSIX_INSUFFICIENT_ACCESS_ERROR)
    missing_gid_error = BuildErrorRegex(obj, POSIX_GID_ERROR)
    missing_uid_error = BuildErrorRegex(obj, POSIX_UID_ERROR)
    no_read_access_error = BuildErrorRegex(obj, POSIX_MODE_ERROR)

  # A dict of test_name: attrs_dict.
  # attrs_dict holds the different attributes that we want for the object in a
  # specific test.
  # To minimize potential test flakes from the system's GID mapping changing
  # mid-test, we use the GID-related methods that fetch GID info each time,
  # rather than reusing the LazyWrapper-wrapped constants across operations.
  test_params = {
      'test1': {
          MODE_ATTR: '333',
          error_key: no_read_access_error,
      },
      'test2': {
          GID_ATTR: GetInvalidGid,
          error_key: missing_gid_error,
      },
      'test3': {
          GID_ATTR: GetInvalidGid,
          MODE_ATTR: '420',
          error_key: missing_gid_error,
      },
      'test4': {
          UID_ATTR: INVALID_UID,
          error_key: missing_uid_error,
      },
      'test5': {
          UID_ATTR: INVALID_UID,
          MODE_ATTR: '530',
          error_key: missing_uid_error,
      },
      'test6': {
          UID_ATTR: INVALID_UID,
          GID_ATTR: GetInvalidGid,
          error_key: missing_uid_error,
      },
      'test7': {
          UID_ATTR: INVALID_UID,
          GID_ATTR: GetInvalidGid,
          MODE_ATTR: '640',
          error_key: missing_uid_error,
      },
      'test8': {
          UID_ATTR: INVALID_UID,
          GID_ATTR: GetPrimaryGid,
          error_key: missing_uid_error,
      },
      'test9': {
          UID_ATTR: INVALID_UID,
          GID_ATTR: GetNonPrimaryGid,
          error_key: missing_uid_error,
      },
      'test10': {
          UID_ATTR: INVALID_UID,
          GID_ATTR: GetPrimaryGid,
          MODE_ATTR: '640',
          error_key: missing_uid_error,
      },
      'test11': {
          UID_ATTR: INVALID_UID,
          GID_ATTR: GetNonPrimaryGid,
          MODE_ATTR: '640',
          error_key: missing_uid_error,
      },
      'test12': {
          UID_ATTR: USER_ID,
          GID_ATTR: GetInvalidGid,
          error_key: missing_gid_error,
      },
      'test13': {
          UID_ATTR: USER_ID,
          GID_ATTR: GetInvalidGid,
          MODE_ATTR: '640',
          error_key: missing_gid_error,
      },
      'test14': {
          GID_ATTR: GetPrimaryGid,
          MODE_ATTR: '240',
          error_key: insufficient_access_error,
      }
  }
  # The first variable below can be used to help debug the test if there is a
  # problem.
  for test_name, attrs_dict in six.iteritems(test_params):
    cls.ClearPOSIXMetadata(obj)

    # Attributes default to None if they are not in attrs_dict; some attrs are
    # functions or LazyWrapper objects that should be called.
    uid = attrs_dict.get(UID_ATTR)
    if uid is not None and callable(uid):
      uid = uid()

    gid = attrs_dict.get(GID_ATTR)
    if gid is not None and callable(gid):
      gid = gid()

    mode = attrs_dict.get(MODE_ATTR)

    cls.SetPOSIXMetadata(cls.default_provider,
                         bucket_uri.bucket_name,
                         obj.object_name,
                         uid=uid,
                         gid=gid,
                         mode=mode)
    stderr = cls.RunGsUtil([
        'cp' if is_cp else 'mv', '-P',
        suri(bucket_uri, obj.object_name), tmpdir
    ],
                           expected_status=1,
                           return_stderr=True)

    if cls._use_gcloud_storage:
      general_posix_error = 'ERROR'
    else:
      general_posix_error = ORPHANED_FILE
    cls.assertIn(
        general_posix_error, stderr,
        'Error during test "%s": %s not found in stderr:\n%s' %
        (test_name, general_posix_error, stderr))

    error_regex = attrs_dict[error_key]
    cls.assertTrue(
        error_regex.search(stderr),
        'Test %s did not match expected error; could not find a match for '
        '%s\n\nin stderr:\n%s' % (test_name, error_regex.pattern, stderr))
    listing1 = TailSet(suri(bucket_uri), cls.FlatListBucket(bucket_uri))
    listing2 = TailSet(tmpdir, cls.FlatListDir(tmpdir))
    # Bucket should have un-altered content.
    cls.assertEqual(listing1, set(['/%s' % obj.object_name]))
    # Dir should have un-altered content.
    cls.assertEqual(listing2, set(['']))


def TestCpMvPOSIXBucketToLocalNoErrors(cls, bucket_uri, tmpdir, is_cp=True):
  """Helper function for preserve_posix_no_errors tests in test_cp and test_mv.

  Args:
    cls: An instance of either TestCp or TestMv.
    bucket_uri: The uri of the bucket that the object is in.
    tmpdir: The local file path to cp to.
    is_cp: Whether or not the calling test suite is cp or mv.
  """
  primary_gid = os.stat(tmpdir).st_gid
  non_primary_gid = util.GetNonPrimaryGid()
  test_params = {
      'obj1': {
          GID_ATTR: primary_gid
      },
      'obj2': {
          GID_ATTR: non_primary_gid
      },
      'obj3': {
          GID_ATTR: primary_gid,
          MODE_ATTR: '440'
      },
      'obj4': {
          GID_ATTR: non_primary_gid,
          MODE_ATTR: '444'
      },
      'obj5': {
          UID_ATTR: USER_ID
      },
      'obj6': {
          UID_ATTR: USER_ID,
          MODE_ATTR: '420'
      },
      'obj7': {
          UID_ATTR: USER_ID,
          GID_ATTR: primary_gid
      },
      'obj8': {
          UID_ATTR: USER_ID,
          GID_ATTR: non_primary_gid
      },
      'obj9': {
          UID_ATTR: USER_ID,
          GID_ATTR: primary_gid,
          MODE_ATTR: '433'
      },
      'obj10': {
          UID_ATTR: USER_ID,
          GID_ATTR: non_primary_gid,
          MODE_ATTR: '442'
      }
  }
  for obj_name, attrs_dict in six.iteritems(test_params):
    uid = attrs_dict.get(UID_ATTR)
    gid = attrs_dict.get(GID_ATTR)
    mode = attrs_dict.get(MODE_ATTR)
    cls.CreateObject(bucket_uri=bucket_uri,
                     object_name=obj_name,
                     contents=obj_name.encode(UTF8),
                     uid=uid,
                     gid=gid,
                     mode=mode)
  for obj_name in six.iterkeys(test_params):
    # Move objects one at a time to avoid listing consistency.
    cls.RunGsUtil(
        ['cp' if is_cp else 'mv', '-P',
         suri(bucket_uri, obj_name), tmpdir])
  listing = TailSet(tmpdir, cls.FlatListDir(tmpdir))
  cls.assertEqual(
      listing,
      set([
          '/obj1', '/obj2', '/obj3', '/obj4', '/obj5', '/obj6', '/obj7',
          '/obj8', '/obj9', '/obj10'
      ]))
  cls.VerifyLocalPOSIXPermissions(os.path.join(tmpdir, 'obj1'),
                                  gid=primary_gid,
                                  mode=DEFAULT_MODE)
  cls.VerifyLocalPOSIXPermissions(os.path.join(tmpdir, 'obj2'),
                                  gid=non_primary_gid,
                                  mode=DEFAULT_MODE)
  cls.VerifyLocalPOSIXPermissions(os.path.join(tmpdir, 'obj3'),
                                  gid=primary_gid,
                                  mode=0o440)
  cls.VerifyLocalPOSIXPermissions(os.path.join(tmpdir, 'obj4'),
                                  gid=non_primary_gid,
                                  mode=0o444)
  cls.VerifyLocalPOSIXPermissions(os.path.join(tmpdir, 'obj5'),
                                  uid=USER_ID,
                                  gid=primary_gid,
                                  mode=DEFAULT_MODE)
  cls.VerifyLocalPOSIXPermissions(os.path.join(tmpdir, 'obj6'),
                                  uid=USER_ID,
                                  gid=primary_gid,
                                  mode=0o420)
  cls.VerifyLocalPOSIXPermissions(os.path.join(tmpdir, 'obj7'),
                                  uid=USER_ID,
                                  gid=primary_gid,
                                  mode=DEFAULT_MODE)
  cls.VerifyLocalPOSIXPermissions(os.path.join(tmpdir, 'obj8'),
                                  uid=USER_ID,
                                  gid=non_primary_gid,
                                  mode=DEFAULT_MODE)
  cls.VerifyLocalPOSIXPermissions(os.path.join(tmpdir, 'obj9'),
                                  uid=USER_ID,
                                  gid=primary_gid,
                                  mode=0o433)
  cls.VerifyLocalPOSIXPermissions(os.path.join(tmpdir, 'obj10'),
                                  uid=USER_ID,
                                  gid=non_primary_gid,
                                  mode=0o442)


def TestCpMvPOSIXLocalToBucketNoErrors(cls, bucket_uri, is_cp=True):
  """Helper function for testing local to bucket POSIX preservation.

  Args:
    cls: An instance of either TestCp or TestMv.
    bucket_uri: The uri of the bucket to cp/mv to.
    is_cp: Whether or not the calling test suite is cp or mv.
  """
  primary_gid = os.getgid()
  non_primary_gid = util.GetNonPrimaryGid()
  test_params = {
      'obj1': {
          GID_ATTR: primary_gid
      },
      'obj2': {
          GID_ATTR: non_primary_gid
      },
      'obj3': {
          GID_ATTR: primary_gid,
          MODE_ATTR: '440'
      },
      'obj4': {
          GID_ATTR: non_primary_gid,
          MODE_ATTR: '444'
      },
      'obj5': {
          UID_ATTR: USER_ID
      },
      'obj6': {
          UID_ATTR: USER_ID,
          MODE_ATTR: '420'
      },
      'obj7': {
          UID_ATTR: USER_ID,
          GID_ATTR: primary_gid
      },
      'obj8': {
          UID_ATTR: USER_ID,
          GID_ATTR: non_primary_gid
      },
      'obj9': {
          UID_ATTR: USER_ID,
          GID_ATTR: primary_gid,
          MODE_ATTR: '433'
      },
      'obj10': {
          UID_ATTR: USER_ID,
          GID_ATTR: non_primary_gid,
          MODE_ATTR: '442'
      }
  }
  for obj_name, attrs_dict in six.iteritems(test_params):
    uid = attrs_dict.get(UID_ATTR, NA_ID)
    gid = attrs_dict.get(GID_ATTR, NA_ID)
    mode = attrs_dict.get(MODE_ATTR, NA_MODE)
    if mode != NA_MODE:
      ValidatePOSIXMode(int(mode, 8))
    ValidateFilePermissionAccess(obj_name,
                                 uid=uid,
                                 gid=int(gid),
                                 mode=int(mode))
    fpath = cls.CreateTempFile(contents=b'foo', uid=uid, gid=gid, mode=mode)
    cls.RunGsUtil(
        ['cp' if is_cp else 'mv', '-P', fpath,
         suri(bucket_uri, obj_name)])
    if uid != NA_ID:
      cls.VerifyObjectCustomAttribute(bucket_uri.bucket_name, obj_name,
                                      UID_ATTR, str(uid))
    if gid != NA_ID:
      cls.VerifyObjectCustomAttribute(bucket_uri.bucket_name, obj_name,
                                      GID_ATTR, str(gid))
    if mode != NA_MODE:
      cls.VerifyObjectCustomAttribute(bucket_uri.bucket_name, obj_name,
                                      MODE_ATTR, str(mode))


def _ReadContentsFromFifo(fifo_path, list_for_output):
  with open(fifo_path, 'rb') as f:
    list_for_output.append(f.read())


def _WriteContentsToFifo(contents, fifo_path):
  with open(fifo_path, 'wb') as f:
    f.write(contents)


class _JSONForceHTTPErrorCopyCallbackHandler(object):
  """Test callback handler that raises an arbitrary HTTP error exception."""

  def __init__(self, startover_at_byte, http_error_num):
    self._startover_at_byte = startover_at_byte
    self._http_error_num = http_error_num
    self.started_over_once = False

  # pylint: disable=invalid-name
  def call(self, total_bytes_transferred, total_size):
    """Forcibly exits if the transfer has passed the halting point."""
    if (total_bytes_transferred >= self._startover_at_byte and
        not self.started_over_once):
      sys.stderr.write('Forcing HTTP error %s after byte %s. '
                       '%s/%s transferred.\r\n' %
                       (self._http_error_num, self._startover_at_byte,
                        MakeHumanReadable(total_bytes_transferred),
                        MakeHumanReadable(total_size)))
      self.started_over_once = True
      raise apitools_exceptions.HttpError({'status': self._http_error_num},
                                          None, None)


class _XMLResumableUploadStartOverCopyCallbackHandler(object):
  """Test callback handler that raises start-over exception during upload."""

  def __init__(self, startover_at_byte):
    self._startover_at_byte = startover_at_byte
    self.started_over_once = False

  # pylint: disable=invalid-name
  def call(self, total_bytes_transferred, total_size):
    """Forcibly exits if the transfer has passed the halting point."""
    if (total_bytes_transferred >= self._startover_at_byte and
        not self.started_over_once):
      sys.stderr.write(
          'Forcing ResumableUpload start over error after byte %s. '
          '%s/%s transferred.\r\n' %
          (self._startover_at_byte, MakeHumanReadable(total_bytes_transferred),
           MakeHumanReadable(total_size)))
      self.started_over_once = True
      raise boto.exception.ResumableUploadException(
          'Forcing upload start over', ResumableTransferDisposition.START_OVER)


class _DeleteBucketThenStartOverCopyCallbackHandler(object):
  """Test callback handler that deletes bucket then raises start-over."""

  def __init__(self, startover_at_byte, bucket_uri):
    self._startover_at_byte = startover_at_byte
    self._bucket_uri = bucket_uri
    self.started_over_once = False

  # pylint: disable=invalid-name
  def call(self, total_bytes_transferred, total_size):
    """Forcibly exits if the transfer has passed the halting point."""
    if (total_bytes_transferred >= self._startover_at_byte and
        not self.started_over_once):
      sys.stderr.write('Deleting bucket (%s)' % (self._bucket_uri.bucket_name))

      @Retry(StorageResponseError, tries=5, timeout_secs=1)
      def DeleteBucket():
        bucket_list = list(self._bucket_uri.list_bucket(all_versions=True))
        for k in bucket_list:
          self._bucket_uri.get_bucket().delete_key(k.name,
                                                   version_id=k.version_id)
        self._bucket_uri.delete_bucket()

      DeleteBucket()
      sys.stderr.write(
          'Forcing ResumableUpload start over error after byte %s. '
          '%s/%s transferred.\r\n' %
          (self._startover_at_byte, MakeHumanReadable(total_bytes_transferred),
           MakeHumanReadable(total_size)))
      self.started_over_once = True
      raise ResumableUploadStartOverException('Artificially forcing start-over')


class _ResumableUploadRetryHandler(object):
  """Test callback handler for causing retries during a resumable transfer."""

  def __init__(self,
               retry_at_byte,
               exception_to_raise,
               exc_args,
               num_retries=1):
    self._retry_at_byte = retry_at_byte
    self._exception_to_raise = exception_to_raise
    self._exception_args = exc_args
    self._num_retries = num_retries

    self._retries_made = 0

  # pylint: disable=invalid-name
  def call(self, total_bytes_transferred, unused_total_size):
    """Cause a single retry at the retry point."""
    if (total_bytes_transferred >= self._retry_at_byte and
        self._retries_made < self._num_retries):
      self._retries_made += 1
      raise self._exception_to_raise(*self._exception_args)


class TestCp(testcase.GsUtilIntegrationTestCase):
  """Integration tests for cp command."""

  # For tests that artificially halt, we need to ensure at least one callback
  # occurs.
  halt_size = START_CALLBACK_PER_BYTES * 2

  def _get_test_file(self, name):
    contents = pkgutil.get_data('gslib', 'tests/test_data/%s' % name)
    return self.CreateTempFile(file_name=name, contents=contents)

  def _CpWithFifoViaGsUtilAndAppendOutputToList(self, src_path_tuple, dst_path,
                                                list_for_return_value,
                                                **kwargs):
    arg_list = ['cp']
    arg_list.extend(src_path_tuple)
    arg_list.append(dst_path)
    # Append stderr, stdout, or return status (if specified in kwargs) to the
    # given list.
    list_for_return_value.append(self.RunGsUtil(arg_list, **kwargs))

  @SequentialAndParallelTransfer
  def test_noclobber(self):
    key_uri = self.CreateObject(contents=b'foo')
    fpath = self.CreateTempFile(contents=b'bar')
    stderr = self.RunGsUtil(
        ['cp', '-n', fpath, suri(key_uri)], return_stderr=True)
    self.assertRegex(stderr, r'Skipping.*: {}'.format(re.escape(suri(key_uri))))
    self.assertEqual(key_uri.get_contents_as_string(), b'foo')
    stderr = self.RunGsUtil(['cp', '-n', suri(key_uri), fpath],
                            return_stderr=True)
    with open(fpath, 'rb') as f:
      self.assertRegex(stderr, r'Skipping.*: {}'.format(re.escape(suri(f))))
      self.assertEqual(f.read(), b'bar')

  @SequentialAndParallelTransfer
  def test_noclobber_different_size(self):
    key_uri = self.CreateObject(contents=b'foo')
    fpath = self.CreateTempFile(contents=b'quux')
    stderr = self.RunGsUtil(
        ['cp', '-n', fpath, suri(key_uri)], return_stderr=True)
    self.assertRegex(stderr, r'Skipping.*: {}'.format(re.escape(suri(key_uri))))
    self.assertEqual(key_uri.get_contents_as_string(), b'foo')
    stderr = self.RunGsUtil(['cp', '-n', suri(key_uri), fpath],
                            return_stderr=True)
    with open(fpath, 'rb') as f:
      self.assertRegex(stderr, r'Skipping.*: {}'.format(re.escape(suri(f))))
      self.assertEqual(f.read(), b'quux')

  def test_dest_bucket_not_exist(self):
    fpath = self.CreateTempFile(contents=b'foo')
    invalid_bucket_uri = ('%s://%s' %
                          (self.default_provider, self.nonexistent_bucket_name))
    # TODO(b/135780661): Remove retry after bug resolved
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check():
      stderr = self.RunGsUtil(['cp', fpath, invalid_bucket_uri],
                              expected_status=1,
                              return_stderr=True)
      if self._use_gcloud_storage:
        self.assertIn('not found: 404', stderr)
      else:
        self.assertIn('does not exist', stderr)

    _Check()

  def test_copy_in_cloud_noclobber(self):
    bucket1_uri = self.CreateBucket()
    bucket2_uri = self.CreateBucket()
    key_uri = self.CreateObject(bucket_uri=bucket1_uri, contents=b'foo')
    stderr = self.RunGsUtil(
        ['cp', suri(key_uri), suri(bucket2_uri)], return_stderr=True)
    # Rewrite API may output an additional 'Copying' progress notification.
    self.assertGreaterEqual(stderr.count('Copying'), 1)
    self.assertLessEqual(stderr.count('Copying'), 2)
    stderr = self.RunGsUtil(
        ['cp', '-n', suri(key_uri),
         suri(bucket2_uri)], return_stderr=True)
    self.assertRegex(
        stderr, r'Skipping.*: {}'.format(suri(bucket2_uri,
                                              key_uri.object_name)))

  @SequentialAndParallelTransfer
  @SkipForXML('Boto library does not handle objects with .. in them.')
  def test_skip_object_with_parent_directory_symbol_in_name(self):
    bucket_uri = self.CreateBucket()
    key_uri = self.CreateObject(bucket_uri=bucket_uri,
                                object_name='dir/../../../file',
                                contents=b'data',
                                prefer_json_api=True)
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name='file2',
                      contents=b'data')
    directory = self.CreateTempDir()

    stderr = self.RunGsUtil(
        ['cp', '-r', suri(bucket_uri), directory], return_stderr=True)

    # By default, deletes in the tearDown method run with the XML API. Boto
    # does not handle names with '..', so we need to delete problematic
    # objects with the json API. Delete happens before assertions, in case they
    # raise errors and prevent cleanup.
    self.json_api.DeleteObject(bucket_uri.bucket_name, key_uri.object_name)

    self.assertIn(
        'Skipping copy of source URL %s because it would be copied '
        'outside the expected destination directory: %s.' %
        (suri(key_uri), os.path.abspath(directory)), stderr)
    self.assertFalse(os.path.exists(os.path.join(directory, 'file')))
    self.assertTrue(
        os.path.exists(os.path.join(directory, bucket_uri.bucket_name,
                                    'file2')))

  @SequentialAndParallelTransfer
  @SkipForXML('Boto library does not handle objects with .. in them.')
  def test_skip_parent_directory_symbol_in_name_is_reflected_in_manifest(self):
    bucket_uri = self.CreateBucket()
    key_uri = self.CreateObject(bucket_uri=bucket_uri,
                                object_name='dir/../../../file',
                                contents=b'data',
                                prefer_json_api=True)
    directory = self.CreateTempDir()
    log_path = os.path.join(directory, 'log.csv')

    stderr = self.RunGsUtil(
        ['cp', '-r', '-L', log_path,
         suri(bucket_uri), directory],
        return_stderr=True)

    # By default, deletes in the tearDown method run with the XML API. Boto
    # does not handle names with '..', so we need to delete problematic
    # objects with the json API. Delete happens before assertions, in case they
    # raise errors and prevent cleanup.
    self.json_api.DeleteObject(bucket_uri.bucket_name, key_uri.object_name)

    self.assertIn(
        'Skipping copy of source URL %s because it would be copied '
        'outside the expected destination directory: %s.' %
        (suri(key_uri), os.path.abspath(directory)), stderr)
    self.assertFalse(os.path.exists(os.path.join(directory, 'file')))
    with open(log_path, 'r') as f:
      lines = f.readlines()
      results = lines[1].strip().split(',')
      self.assertEqual(results[0], suri(key_uri))  # The 'Source' column.
      self.assertEqual(results[8], 'skip')  # The 'Result' column.

  @SequentialAndParallelTransfer
  @SkipForXML('Boto library does not handle objects with .. in them.')
  @unittest.skipIf(IS_WINDOWS, 'os.symlink() is not available on Windows.')
  def test_skip_parent_directory_symbol_object_with_symlink_destination(self):
    bucket_uri = self.CreateBucket()
    key_uri = self.CreateObject(bucket_uri=bucket_uri,
                                object_name='dir/../../../file',
                                contents=b'data',
                                prefer_json_api=True)
    second_key_uri = self.CreateObject(bucket_uri=bucket_uri,
                                       object_name='file2',
                                       contents=b'data')

    directory = self.CreateTempDir()
    linked_destination = os.path.join(directory, 'linked_destination')
    destination = os.path.join(directory, 'destination')
    os.mkdir(destination)
    os.symlink(destination, linked_destination)

    stderr = self.RunGsUtil([
        '-D', 'cp', '-r',
        suri(bucket_uri),
        suri(second_key_uri), linked_destination
    ],
                            return_stderr=True)

    # By default, deletes in the tearDown method run with the XML API. Boto
    # does not handle names with '..', so we need to delete problematic
    # objects with the json API. Delete happens before assertions, in case they
    # raise errors and prevent cleanup.
    self.json_api.DeleteObject(bucket_uri.bucket_name, key_uri.object_name)

    self.assertIn(
        'Skipping copy of source URL %s because it would be copied '
        'outside the expected destination directory: %s.' %
        (suri(key_uri), linked_destination), stderr)
    self.assertFalse(os.path.exists(os.path.join(linked_destination, 'file')))
    self.assertTrue(os.path.exists(os.path.join(linked_destination, 'file2')))

  @unittest.skipIf(IS_WINDOWS, 'os.mkfifo not available on Windows.')
  @SequentialAndParallelTransfer
  def test_cp_from_local_file_to_fifo(self):
    contents = b'bar'
    fifo_path = self.CreateTempFifo()
    file_path = self.CreateTempFile(contents=contents)
    list_for_output = []

    read_thread = threading.Thread(target=_ReadContentsFromFifo,
                                   args=(fifo_path, list_for_output))
    read_thread.start()
    write_thread = threading.Thread(
        target=self._CpWithFifoViaGsUtilAndAppendOutputToList,
        args=((file_path,), fifo_path, []))
    write_thread.start()
    write_thread.join(120)
    read_thread.join(120)
    if not list_for_output:
      self.fail('Reading/writing to the fifo timed out.')
    self.assertEqual(list_for_output[0].strip(), contents)

  @unittest.skipIf(IS_WINDOWS, 'os.mkfifo not available on Windows.')
  @SequentialAndParallelTransfer
  def test_cp_from_one_object_to_fifo(self):
    fifo_path = self.CreateTempFifo()
    bucket_uri = self.CreateBucket()
    contents = b'bar'
    obj_uri = self.CreateObject(bucket_uri=bucket_uri, contents=contents)
    list_for_output = []

    read_thread = threading.Thread(target=_ReadContentsFromFifo,
                                   args=(fifo_path, list_for_output))
    read_thread.start()
    write_thread = threading.Thread(
        target=self._CpWithFifoViaGsUtilAndAppendOutputToList,
        args=((suri(obj_uri),), fifo_path, []))
    write_thread.start()
    write_thread.join(120)
    read_thread.join(120)
    if not list_for_output:
      self.fail('Reading/writing to the fifo timed out.')
    self.assertEqual(list_for_output[0].strip(), contents)

  @unittest.skipIf(IS_WINDOWS, 'os.mkfifo not available on Windows.')
  @SequentialAndParallelTransfer
  def test_cp_from_multiple_objects_to_fifo(self):
    fifo_path = self.CreateTempFifo()
    bucket_uri = self.CreateBucket()
    contents1 = b'foo and bar'
    contents2 = b'baz and qux'
    obj1_uri = self.CreateObject(bucket_uri=bucket_uri, contents=contents1)
    obj2_uri = self.CreateObject(bucket_uri=bucket_uri, contents=contents2)
    list_for_output = []

    read_thread = threading.Thread(target=_ReadContentsFromFifo,
                                   args=(fifo_path, list_for_output))
    read_thread.start()
    write_thread = threading.Thread(
        target=self._CpWithFifoViaGsUtilAndAppendOutputToList,
        args=((suri(obj1_uri), suri(obj2_uri)), fifo_path, []))
    write_thread.start()
    write_thread.join(120)
    read_thread.join(120)
    if not list_for_output:
      self.fail('Reading/writing to the fifo timed out.')
    self.assertIn(contents1, list_for_output[0])
    self.assertIn(contents2, list_for_output[0])

  @SequentialAndParallelTransfer
  def test_streaming(self):
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(
        ['cp', '-', '%s' % suri(bucket_uri, 'foo')],
        stdin='bar',
        return_stderr=True)
    if self._use_gcloud_storage:
      self.assertIn('Copying file://- to ' + suri(bucket_uri, 'foo'), stderr)
    else:
      self.assertIn('Copying from <STDIN>', stderr)
    key_uri = self.StorageUriCloneReplaceName(bucket_uri, 'foo')
    self.assertEqual(key_uri.get_contents_as_string(), b'bar')

  @unittest.skipIf(IS_WINDOWS, 'os.mkfifo not available on Windows.')
  @SequentialAndParallelTransfer
  def test_streaming_from_fifo_to_object(self):
    bucket_uri = self.CreateBucket()
    fifo_path = self.CreateTempFifo()
    object_name = 'foo'
    object_contents = b'bar'
    list_for_output = []

    # Start writer in the background, which won't finish until a corresponding
    # read operation is performed on the fifo.
    write_thread = threading.Thread(target=_WriteContentsToFifo,
                                    args=(object_contents, fifo_path))
    write_thread.start()
    # The fifo requires both a pending read and write before either operation
    # will complete. Regardless of which operation occurs first, the
    # corresponding subsequent operation will unblock the first one.
    # We run gsutil in a thread so that it can timeout rather than hang forever
    # if the write thread fails.
    read_thread = threading.Thread(
        target=self._CpWithFifoViaGsUtilAndAppendOutputToList,
        args=((fifo_path,), suri(bucket_uri, object_name), list_for_output),
        kwargs={'return_stderr': True})
    read_thread.start()

    read_thread.join(120)
    write_thread.join(120)
    if not list_for_output:
      self.fail('Reading/writing to the fifo timed out.')

    if self._use_gcloud_storage:
      self.assertIn(
          'Copying file://{} to {}'.format(fifo_path,
                                           suri(bucket_uri, object_name)),
          list_for_output[0])
    else:
      self.assertIn('Copying from named pipe', list_for_output[0])

    key_uri = self.StorageUriCloneReplaceName(bucket_uri, object_name)
    self.assertEqual(key_uri.get_contents_as_string(), object_contents)

  @unittest.skipIf(IS_WINDOWS, 'os.mkfifo not available on Windows.')
  @SequentialAndParallelTransfer
  def test_streaming_from_fifo_to_stdout(self):
    fifo_path = self.CreateTempFifo()
    contents = b'bar'
    list_for_output = []

    write_thread = threading.Thread(target=_WriteContentsToFifo,
                                    args=(contents, fifo_path))
    write_thread.start()
    read_thread = threading.Thread(
        target=self._CpWithFifoViaGsUtilAndAppendOutputToList,
        args=((fifo_path,), '-', list_for_output),
        kwargs={'return_stdout': True})
    read_thread.start()
    read_thread.join(120)
    write_thread.join(120)
    if not list_for_output:
      self.fail('Reading/writing to the fifo timed out.')
    self.assertEqual(list_for_output[0].strip().encode('ascii'), contents)

  @unittest.skipIf(IS_WINDOWS, 'os.mkfifo not available on Windows.')
  @SequentialAndParallelTransfer
  def test_streaming_from_stdout_to_fifo(self):
    fifo_path = self.CreateTempFifo()
    contents = b'bar'
    list_for_output = []
    list_for_gsutil_output = []

    read_thread = threading.Thread(target=_ReadContentsFromFifo,
                                   args=(fifo_path, list_for_output))
    read_thread.start()
    write_thread = threading.Thread(
        target=self._CpWithFifoViaGsUtilAndAppendOutputToList,
        args=(('-',), fifo_path, list_for_gsutil_output),
        kwargs={
            'return_stderr': True,
            'stdin': contents
        })
    write_thread.start()
    write_thread.join(120)
    read_thread.join(120)
    if not list_for_output:
      self.fail('Reading/writing to the fifo timed out.')
    self.assertEqual(list_for_output[0].strip(), contents)

  def test_streaming_multiple_arguments(self):
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(['cp', '-', '-', suri(bucket_uri)],
                            stdin='bar',
                            return_stderr=True,
                            expected_status=1)
    if self._use_gcloud_storage:
      self.assertIn(
          'Multiple URL strings are not supported when transferring'
          ' from stdin.', stderr)
    else:
      self.assertIn('Multiple URL strings are not supported with streaming',
                    stderr)

  # TODO: Implement a way to test both with and without using magic file.

  @SequentialAndParallelTransfer
  def test_detect_content_type(self):
    """Tests local detection of content type."""
    bucket_uri = self.CreateBucket()
    dsturi = suri(bucket_uri, 'foo')

    self.RunGsUtil(['cp', self._get_test_file('test.mp3'), dsturi])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-L', dsturi], return_stdout=True)
      if IS_WINDOWS:
        self.assertTrue(
            re.search(r'Content-Type:\s+audio/x-mpg', stdout) or
            re.search(r'Content-Type:\s+audio/mpeg', stdout))
      else:
        self.assertRegex(stdout, r'Content-Type:\s+audio/mpeg')

    _Check1()

    self.RunGsUtil(['cp', self._get_test_file('test.gif'), dsturi])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check2():
      stdout = self.RunGsUtil(['ls', '-L', dsturi], return_stdout=True)
      self.assertRegex(stdout, r'Content-Type:\s+image/gif')

    _Check2()

  def test_content_type_override_default(self):
    """Tests overriding content type with the default value."""
    bucket_uri = self.CreateBucket()
    dsturi = suri(bucket_uri, 'foo')

    self.RunGsUtil(
        ['-h', 'Content-Type:', 'cp',
         self._get_test_file('test.mp3'), dsturi])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-L', dsturi], return_stdout=True)
      self.assertRegex(stdout, r'Content-Type:\s+application/octet-stream')

    _Check1()

    self.RunGsUtil(
        ['-h', 'Content-Type:', 'cp',
         self._get_test_file('test.gif'), dsturi])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check2():
      stdout = self.RunGsUtil(['ls', '-L', dsturi], return_stdout=True)
      self.assertRegex(stdout, r'Content-Type:\s+application/octet-stream')

    _Check2()

  def test_content_type_override(self):
    """Tests overriding content type with a value."""
    bucket_uri = self.CreateBucket()
    dsturi = suri(bucket_uri, 'foo')

    self.RunGsUtil([
        '-h', 'Content-Type:text/plain', 'cp',
        self._get_test_file('test.mp3'), dsturi
    ])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-L', dsturi], return_stdout=True)
      self.assertRegex(stdout, r'Content-Type:\s+text/plain')

    _Check1()

    self.RunGsUtil([
        '-h', 'Content-Type:text/plain', 'cp',
        self._get_test_file('test.gif'), dsturi
    ])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check2():
      stdout = self.RunGsUtil(['ls', '-L', dsturi], return_stdout=True)
      self.assertRegex(stdout, r'Content-Type:\s+text/plain')

    _Check2()

  @unittest.skipIf(IS_WINDOWS, 'magicfile is not available on Windows.')
  @SequentialAndParallelTransfer
  def test_magicfile_override(self):
    """Tests content type override with magicfile value."""
    bucket_uri = self.CreateBucket()
    dsturi = suri(bucket_uri, 'foo')
    fpath = self.CreateTempFile(contents=b'foo/bar\n')
    self.RunGsUtil(['cp', fpath, dsturi])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-L', dsturi], return_stdout=True)
      use_magicfile = boto.config.getbool('GSUtil', 'use_magicfile', False)
      content_type = ('text/plain'
                      if use_magicfile else 'application/octet-stream')
      self.assertRegex(stdout, r'Content-Type:\s+%s' % content_type)

    _Check1()

  @SequentialAndParallelTransfer
  def test_content_type_mismatches(self):
    """Tests overriding content type when it does not match the file type."""
    bucket_uri = self.CreateBucket()
    dsturi = suri(bucket_uri, 'foo')
    fpath = self.CreateTempFile(contents=b'foo/bar\n')

    self.RunGsUtil([
        '-h', 'Content-Type:image/gif', 'cp',
        self._get_test_file('test.mp3'), dsturi
    ])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-L', dsturi], return_stdout=True)
      self.assertRegex(stdout, r'Content-Type:\s+image/gif')

    _Check1()

    self.RunGsUtil([
        '-h', 'Content-Type:image/gif', 'cp',
        self._get_test_file('test.gif'), dsturi
    ])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check2():
      stdout = self.RunGsUtil(['ls', '-L', dsturi], return_stdout=True)
      self.assertRegex(stdout, r'Content-Type:\s+image/gif')

    _Check2()

    self.RunGsUtil(['-h', 'Content-Type:image/gif', 'cp', fpath, dsturi])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check3():
      stdout = self.RunGsUtil(['ls', '-L', dsturi], return_stdout=True)
      self.assertRegex(stdout, r'Content-Type:\s+image/gif')

    _Check3()

  @SequentialAndParallelTransfer
  def test_content_type_header_case_insensitive(self):
    """Tests that content type header is treated with case insensitivity."""
    bucket_uri = self.CreateBucket()
    dsturi = suri(bucket_uri, 'foo')
    fpath = self._get_test_file('test.gif')

    self.RunGsUtil(['-h', 'content-Type:text/plain', 'cp', fpath, dsturi])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-L', dsturi], return_stdout=True)
      self.assertRegex(stdout, r'Content-Type:\s+text/plain')
      self.assertNotRegex(stdout, r'image/gif')

    _Check1()

    self.RunGsUtil([
        '-h', 'CONTENT-TYPE:image/gif', '-h', 'content-type:image/gif', 'cp',
        fpath, dsturi
    ])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check2():
      stdout = self.RunGsUtil(['ls', '-L', dsturi], return_stdout=True)
      self.assertRegex(stdout, r'Content-Type:\s+image/gif')
      self.assertNotRegex(stdout, r'image/gif,\s*image/gif')

    _Check2()

  @SequentialAndParallelTransfer
  def test_other_headers(self):
    """Tests that non-content-type headers are applied successfully on copy."""
    bucket_uri = self.CreateBucket()
    dst_uri = suri(bucket_uri, 'foo')
    fpath = self._get_test_file('test.gif')

    self.RunGsUtil([
        '-h', 'Cache-Control:public,max-age=12', '-h',
        'x-%s-meta-1:abcd' % self.provider_custom_meta, 'cp', fpath, dst_uri
    ])

    stdout = self.RunGsUtil(['ls', '-L', dst_uri], return_stdout=True)
    self.assertRegex(stdout, r'Cache-Control\s*:\s*public,max-age=12')

    self.assertRegex(stdout, r'Metadata:\s*1:\s*abcd')

    dst_uri2 = suri(bucket_uri, 'bar')
    self.RunGsUtil(['cp', dst_uri, dst_uri2])
    # Ensure metadata was preserved across copy.
    stdout = self.RunGsUtil(['ls', '-L', dst_uri2], return_stdout=True)
    self.assertRegex(stdout, r'Cache-Control\s*:\s*public,max-age=12')
    self.assertRegex(stdout, r'Metadata:\s*1:\s*abcd')

  @SequentialAndParallelTransfer
  def test_request_reason_header(self):
    """Test that x-goog-request-header can be set using the environment variable."""
    os.environ['CLOUDSDK_CORE_REQUEST_REASON'] = 'b/this_is_env_reason'
    bucket_uri = self.CreateBucket()
    dst_uri = suri(bucket_uri, 'foo')
    fpath = self._get_test_file('test.gif')
    # Ensure x-goog-request-header is set in cp command
    stderr = self.RunGsUtil(['-DD', 'cp', fpath, dst_uri], return_stderr=True)

    if self._use_gcloud_storage:
      reason_regex = r"b'X-Goog-Request-Reason': b'b/this_is_env_reason'"
    else:
      reason_regex = r"'x-goog-request-reason': 'b/this_is_env_reason'"

    self.assertRegex(stderr, reason_regex)
    # Ensure x-goog-request-header is set in ls command
    stderr = self.RunGsUtil(['-DD', 'ls', '-L', dst_uri], return_stderr=True)
    self.assertRegex(stderr, reason_regex)

  @SequentialAndParallelTransfer
  @SkipForXML('XML APIs use a different debug log format.')
  def test_request_reason_header_persists_multiple_requests_json(self):
    """Test that x-goog-request-header works when cp sends multiple requests."""
    os.environ['CLOUDSDK_CORE_REQUEST_REASON'] = 'b/this_is_env_reason'
    bucket_uri = self.CreateBucket()
    dst_uri = suri(bucket_uri, 'foo')
    fpath = self._get_test_file('test.gif')

    boto_config_for_test = ('GSUtil', 'resumable_threshold', '0')
    with SetBotoConfigForTest([boto_config_for_test]):
      stderr = self.RunGsUtil(['-DD', 'cp', fpath, dst_uri], return_stderr=True)

    if self._use_gcloud_storage:
      reason_regex = r'X-Goog-Request-Reason\': b\'b/this_is_env_reason'
    else:
      reason_regex = r'x-goog-request-reason\': \'b/this_is_env_reason'

    self.assertRegex(
        stderr,
        # POST follows GET request. Both need the request-reason header.
        r'GET[\s\S]*' + reason_regex + r'[\s\S]*POST[\s\S]*' + reason_regex)

  @SequentialAndParallelTransfer
  @SkipForJSON('JSON API uses a different debug log format.')
  def test_request_reason_header_persists_multiple_requests_xml(self):
    """Test that x-goog-request-header works when cp sends multiple requests."""
    os.environ['CLOUDSDK_CORE_REQUEST_REASON'] = 'b/this_is_env_reason'
    bucket_uri = self.CreateBucket()
    dst_uri = suri(bucket_uri, 'foo')
    fpath = self._get_test_file('test.gif')

    boto_config_for_test = ('GSUtil', 'resumable_threshold', '0')
    with SetBotoConfigForTest([boto_config_for_test]):
      stderr = self.RunGsUtil(['-D', 'cp', fpath, dst_uri], return_stderr=True)

    reason_regex = (
        r'Final headers: \{[\s\S]*\''
        r'x-goog-request-reason\': \'b/this_is_env_reason\'[\s\S]*}')

    # Pattern should match twice since two requests should have a reason header.
    self.assertRegex(stderr, reason_regex + r'[\s\S]*' + reason_regex)

  @SequentialAndParallelTransfer
  def test_versioning(self):
    """Tests copy with versioning."""
    bucket_uri = self.CreateVersionedBucket()
    k1_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'data2')
    k2_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'data1')
    g1 = urigen(k2_uri)
    self.RunGsUtil(['cp', suri(k1_uri), suri(k2_uri)])
    k2_uri = self.StorageUriCloneReplaceName(bucket_uri, k2_uri.object_name)
    k2_uri = self.StorageUriCloneReplaceKey(bucket_uri, k2_uri.get_key())
    g2 = urigen(k2_uri)
    self.StorageUriSetContentsFromString(k2_uri, 'data3')
    g3 = urigen(k2_uri)

    fpath = self.CreateTempFile()
    # Check to make sure current version is data3.
    self.RunGsUtil(['cp', k2_uri.versionless_uri, fpath])
    with open(fpath, 'rb') as f:
      self.assertEqual(f.read(), b'data3')

    # Check contents of all three versions
    self.RunGsUtil(['cp', '%s#%s' % (k2_uri.versionless_uri, g1), fpath])
    with open(fpath, 'rb') as f:
      self.assertEqual(f.read(), b'data1')
    self.RunGsUtil(['cp', '%s#%s' % (k2_uri.versionless_uri, g2), fpath])
    with open(fpath, 'rb') as f:
      self.assertEqual(f.read(), b'data2')
    self.RunGsUtil(['cp', '%s#%s' % (k2_uri.versionless_uri, g3), fpath])
    with open(fpath, 'rb') as f:
      self.assertEqual(f.read(), b'data3')

    # Copy first version to current and verify.
    self.RunGsUtil(
        ['cp',
         '%s#%s' % (k2_uri.versionless_uri, g1), k2_uri.versionless_uri])
    self.RunGsUtil(['cp', k2_uri.versionless_uri, fpath])
    with open(fpath, 'rb') as f:
      self.assertEqual(f.read(), b'data1')

    # Attempt to specify a version-specific URI for destination.
    stderr = self.RunGsUtil(['cp', fpath, k2_uri.uri],
                            return_stderr=True,
                            expected_status=1)
    if self._use_gcloud_storage:
      self.assertIn(
          'destination argument of the cp command cannot'
          ' be a version-specific URL', stderr)
    else:
      self.assertIn('cannot be the destination for gsutil cp', stderr)

  def test_versioning_no_parallelism(self):
    """Tests that copy all-versions errors when parallelism is enabled."""
    # TODO(b/135780661): Remove retry after bug resolved
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check():
      stderr = self.RunGsUtil([
          '-m', 'cp', '-A',
          suri(self.nonexistent_bucket_name, 'foo'),
          suri(self.nonexistent_bucket_name, 'bar')
      ],
                              expected_status=1,
                              return_stderr=True)
      if self._use_gcloud_storage:
        self.assertIn('sequential instead of parallel task execution', stderr)
      else:
        self.assertIn('-m option is not supported with the cp -A flag', stderr)

    _Check()

  @SkipForS3('S3 lists versioned objects in reverse timestamp order.')
  def test_recursive_copying_versioned_bucket(self):
    """Tests cp -R with versioned buckets."""
    bucket1_uri = self.CreateVersionedBucket()
    bucket2_uri = self.CreateVersionedBucket()
    bucket3_uri = self.CreateVersionedBucket()

    # Write two versions of an object to the bucket1.
    v1_uri = self.CreateObject(bucket_uri=bucket1_uri,
                               object_name='k',
                               contents=b'data0')
    self.CreateObject(bucket_uri=bucket1_uri,
                      object_name='k',
                      contents=b'longer_data1',
                      gs_idempotent_generation=urigen(v1_uri))

    self.AssertNObjectsInBucket(bucket1_uri, 2, versioned=True)
    self.AssertNObjectsInBucket(bucket2_uri, 0, versioned=True)
    self.AssertNObjectsInBucket(bucket3_uri, 0, versioned=True)

    # Recursively copy to second versioned bucket.
    # -A flag should copy all versions in order.
    self.RunGsUtil(
        ['cp', '-R', '-A',
         suri(bucket1_uri, '*'),
         suri(bucket2_uri)])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check2():
      """Validates the results of the cp -R."""
      listing1 = self.RunGsUtil(['ls', '-la', suri(bucket1_uri)],
                                return_stdout=True).split('\n')
      listing2 = self.RunGsUtil(['ls', '-la', suri(bucket2_uri)],
                                return_stdout=True).split('\n')
      # 2 lines of listing output, 1 summary line, 1 empty line from \n split.
      self.assertEqual(len(listing1), 4)
      self.assertEqual(len(listing2), 4)

      # First object in each bucket should match in size and version-less name.
      size1, _, uri_str1, _ = listing1[0].split()
      self.assertEqual(size1, str(len('data0')))
      self.assertEqual(storage_uri(uri_str1).object_name, 'k')
      size2, _, uri_str2, _ = listing2[0].split()
      self.assertEqual(size2, str(len('data0')))
      self.assertEqual(storage_uri(uri_str2).object_name, 'k')

      # Similarly for second object in each bucket.
      size1, _, uri_str1, _ = listing1[1].split()
      self.assertEqual(size1, str(len('longer_data1')))
      self.assertEqual(storage_uri(uri_str1).object_name, 'k')
      size2, _, uri_str2, _ = listing2[1].split()
      self.assertEqual(size2, str(len('longer_data1')))
      self.assertEqual(storage_uri(uri_str2).object_name, 'k')

    _Check2()

    # Recursively copy to second versioned bucket with no -A flag.
    # This should copy only the live object.
    self.RunGsUtil(['cp', '-R', suri(bucket1_uri, '*'), suri(bucket3_uri)])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check3():
      """Validates the results of the cp -R."""
      listing1 = self.RunGsUtil(['ls', '-la', suri(bucket1_uri)],
                                return_stdout=True).split('\n')
      listing2 = self.RunGsUtil(['ls', '-la', suri(bucket3_uri)],
                                return_stdout=True).split('\n')
      # 2 lines of listing output, 1 summary line, 1 empty line from \n split.
      self.assertEqual(len(listing1), 4)
      # 1 lines of listing output, 1 summary line, 1 empty line from \n split.
      self.assertEqual(len(listing2), 3)

      # Live (second) object in bucket 1 should match the single live object.
      size1, _, uri_str1, _ = listing2[0].split()
      self.assertEqual(size1, str(len('longer_data1')))
      self.assertEqual(storage_uri(uri_str1).object_name, 'k')

    _Check3()

  @SequentialAndParallelTransfer
  @SkipForS3('Preconditions not supported for S3.')
  def test_cp_generation_zero_match(self):
    """Tests that cp handles an object-not-exists precondition header."""
    bucket_uri = self.CreateBucket()
    fpath1 = self.CreateTempFile(contents=b'data1')
    # Match 0 means only write the object if it doesn't already exist.
    gen_match_header = 'x-goog-if-generation-match:0'

    # First copy should succeed.
    # TODO: This can fail (rarely) if the server returns a 5xx but actually
    # commits the bytes. If we add restarts on small uploads, handle this
    # case.
    self.RunGsUtil(['-h', gen_match_header, 'cp', fpath1, suri(bucket_uri)])

    # Second copy should fail with a precondition error.
    stderr = self.RunGsUtil(
        ['-h', gen_match_header, 'cp', fpath1,
         suri(bucket_uri)],
        return_stderr=True,
        expected_status=1)
    if self._use_gcloud_storage:
      self.assertIn(
          'HTTPError 412: At least one of the pre-conditions you specified'
          ' did not hold.', stderr)
    else:
      self.assertIn('PreconditionException', stderr)

  @SequentialAndParallelTransfer
  @SkipForS3('Preconditions not supported for S3.')
  def test_cp_v_generation_match(self):
    """Tests that cp -v option handles the if-generation-match header."""
    bucket_uri = self.CreateVersionedBucket()
    k1_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'data1')
    g1 = k1_uri.generation

    tmpdir = self.CreateTempDir()
    fpath1 = self.CreateTempFile(tmpdir=tmpdir, contents=b'data2')

    gen_match_header = 'x-goog-if-generation-match:%s' % g1
    # First copy should succeed.
    self.RunGsUtil(['-h', gen_match_header, 'cp', fpath1, suri(k1_uri)])

    # Second copy should fail the precondition.
    stderr = self.RunGsUtil(
        ['-h', gen_match_header, 'cp', fpath1,
         suri(k1_uri)],
        return_stderr=True,
        expected_status=1)

    if self._use_gcloud_storage:
      self.assertIn('pre-condition', stderr)
    else:
      self.assertIn('PreconditionException', stderr)

    # Specifiying a generation with -n should fail before the request hits the
    # server.
    stderr = self.RunGsUtil(
        ['-h', gen_match_header, 'cp', '-n', fpath1,
         suri(k1_uri)],
        return_stderr=True,
        expected_status=1)

    if self._use_gcloud_storage:
      self.assertIn(
          'Cannot specify both generation precondition and no-clobber', stderr)
    else:
      self.assertIn('ArgumentException', stderr)
      self.assertIn(
          'Specifying x-goog-if-generation-match is not supported '
          'with cp -n', stderr)

  @SequentialAndParallelTransfer
  def test_cp_nv(self):
    """Tests that cp -nv works when skipping existing file."""
    bucket_uri = self.CreateVersionedBucket()
    k1_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'data1')

    tmpdir = self.CreateTempDir()
    fpath1 = self.CreateTempFile(tmpdir=tmpdir, contents=b'data2')

    # First copy should succeed.
    self.RunGsUtil(['cp', '-nv', fpath1, suri(k1_uri)])

    # Second copy should skip copying.
    stderr = self.RunGsUtil(
        ['cp', '-nv', fpath1, suri(k1_uri)], return_stderr=True)
    self.assertIn('Skipping existing', stderr)

  @SequentialAndParallelTransfer
  @SkipForS3('S3 lists versioned objects in reverse timestamp order.')
  def test_cp_v_option(self):
    """"Tests that cp -v returns the created object's version-specific URI."""
    bucket_uri = self.CreateVersionedBucket()
    k1_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'data1')
    k2_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'data2')

    # Case 1: Upload file to object using one-shot PUT.
    tmpdir = self.CreateTempDir()
    fpath1 = self.CreateTempFile(tmpdir=tmpdir, contents=b'data1')
    self._run_cp_minus_v_test('-v', fpath1, k2_uri.uri)

    # Case 2: Upload file to object using resumable upload.
    size_threshold = ONE_KIB
    boto_config_for_test = ('GSUtil', 'resumable_threshold',
                            str(size_threshold))
    with SetBotoConfigForTest([boto_config_for_test]):
      file_as_string = os.urandom(size_threshold)
      tmpdir = self.CreateTempDir()
      fpath1 = self.CreateTempFile(tmpdir=tmpdir, contents=file_as_string)
      self._run_cp_minus_v_test('-v', fpath1, k2_uri.uri)

    # Case 3: Upload stream to object.
    self._run_cp_minus_v_test('-v', '-', k2_uri.uri)

    # Case 4: Download object to file. For this case we just expect output of
    # gsutil cp -v to be the URI of the file.
    tmpdir = self.CreateTempDir()
    fpath1 = self.CreateTempFile(tmpdir=tmpdir)
    dst_uri = storage_uri(fpath1)
    stderr = self.RunGsUtil(
        ['cp', '-v', suri(k1_uri), suri(dst_uri)], return_stderr=True)
    # TODO: Add ordering assertion (should be in stderr.split('\n)[-2]) back
    # once both the creation and status messages are handled by the UI thread.
    self.assertIn('Created: %s\n' % dst_uri.uri, stderr)

    # Case 5: Daisy-chain from object to object.
    self._run_cp_minus_v_test('-Dv', k1_uri.uri, k2_uri.uri)

    # Case 6: Copy object to object in-the-cloud.
    self._run_cp_minus_v_test('-v', k1_uri.uri, k2_uri.uri)

  def _run_cp_minus_v_test(self, opt, src_str, dst_str):
    """Runs cp -v with the options and validates the results."""
    stderr = self.RunGsUtil(['cp', opt, src_str, dst_str], return_stderr=True)
    match = re.search(r'Created: (.*)\n', stderr)
    self.assertIsNotNone(match)
    created_uri = match.group(1)

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-a', dst_str], return_stdout=True)
      lines = stdout.split('\n')
      # Final (most recent) object should match the "Created:" URI. This is
      # in second-to-last line (last line is '\n').
      self.assertGreater(len(lines), 2)
      self.assertEqual(created_uri, lines[-2])

    _Check1()

  @SequentialAndParallelTransfer
  def test_stdin_args(self):
    """Tests cp with the -I option."""
    tmpdir = self.CreateTempDir()
    fpath1 = self.CreateTempFile(tmpdir=tmpdir, contents=b'data1')
    fpath2 = self.CreateTempFile(tmpdir=tmpdir, contents=b'data2')
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(['cp', '-I', suri(bucket_uri)],
                   stdin='\n'.join((fpath1, fpath2)))

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', suri(bucket_uri)], return_stdout=True)
      self.assertIn(os.path.basename(fpath1), stdout)
      self.assertIn(os.path.basename(fpath2), stdout)
      self.assertNumLines(stdout, 2)

    _Check1()

  def test_cross_storage_class_cloud_cp(self):
    bucket1_uri = self.CreateBucket(storage_class='standard')
    bucket2_uri = self.CreateBucket(
        storage_class='durable_reduced_availability')
    key_uri = self.CreateObject(bucket_uri=bucket1_uri, contents=b'foo')
    # Server now allows copy-in-the-cloud across storage classes.
    self.RunGsUtil(['cp', suri(key_uri), suri(bucket2_uri)])

  @unittest.skipUnless(HAS_S3_CREDS, 'Test requires both S3 and GS credentials')
  def test_cross_provider_cp(self):
    s3_bucket = self.CreateBucket(provider='s3')
    gs_bucket = self.CreateBucket(provider='gs')
    s3_key = self.CreateObject(bucket_uri=s3_bucket, contents=b'foo')
    gs_key = self.CreateObject(bucket_uri=gs_bucket, contents=b'bar')
    self.RunGsUtil(['cp', suri(s3_key), suri(gs_bucket)])
    self.RunGsUtil(['cp', suri(gs_key), suri(s3_bucket)])

  @unittest.skipUnless(HAS_S3_CREDS, 'Test requires both S3 and GS credentials')
  @unittest.skip('This test performs a large copy but remains here for '
                 'debugging purposes.')
  def test_cross_provider_large_cp(self):
    s3_bucket = self.CreateBucket(provider='s3')
    gs_bucket = self.CreateBucket(provider='gs')
    s3_key = self.CreateObject(bucket_uri=s3_bucket,
                               contents=b'f' * 1024 * 1024)
    gs_key = self.CreateObject(bucket_uri=gs_bucket,
                               contents=b'b' * 1024 * 1024)
    self.RunGsUtil(['cp', suri(s3_key), suri(gs_bucket)])
    self.RunGsUtil(['cp', suri(gs_key), suri(s3_bucket)])
    with SetBotoConfigForTest([('GSUtil', 'resumable_threshold', str(ONE_KIB)),
                               ('GSUtil', 'json_resumable_chunk_size',
                                str(ONE_KIB * 256))]):
      # Ensure copy also works across json upload chunk boundaries.
      self.RunGsUtil(['cp', suri(s3_key), suri(gs_bucket)])

  @unittest.skipUnless(HAS_S3_CREDS, 'Test requires both S3 and GS credentials')
  def test_gs_to_s3_multipart_cp(self):
    """Ensure daisy_chain works for an object that is downloaded in 2 parts."""
    s3_bucket = self.CreateBucket(provider='s3')
    gs_bucket = self.CreateBucket(provider='gs', prefer_json_api=True)
    num_bytes = int(_DEFAULT_DOWNLOAD_CHUNK_SIZE * 1.1)
    gs_key = self.CreateObject(bucket_uri=gs_bucket,
                               contents=b'b' * num_bytes,
                               prefer_json_api=True)
    self.RunGsUtil([
        '-o', 's3:use-sigv4=True', '-o', 's3:host=s3.amazonaws.com', 'cp',
        suri(gs_key),
        suri(s3_bucket)
    ])

  @unittest.skip('This test is slow due to creating many objects, '
                 'but remains here for debugging purposes.')
  def test_daisy_chain_cp_file_sizes(self):
    """Ensure daisy chain cp works with a wide of file sizes."""
    bucket_uri = self.CreateBucket()
    bucket2_uri = self.CreateBucket()
    exponent_cap = 28  # Up to 256 MiB in size.
    for i in range(exponent_cap):
      one_byte_smaller = 2**i - 1
      normal = 2**i
      one_byte_larger = 2**i + 1
      self.CreateObject(bucket_uri=bucket_uri, contents=b'a' * one_byte_smaller)
      self.CreateObject(bucket_uri=bucket_uri, contents=b'b' * normal)
      self.CreateObject(bucket_uri=bucket_uri, contents=b'c' * one_byte_larger)

    self.AssertNObjectsInBucket(bucket_uri, exponent_cap * 3)
    self.RunGsUtil(
        ['-m', 'cp', '-D',
         suri(bucket_uri, '**'),
         suri(bucket2_uri)])

    self.AssertNObjectsInBucket(bucket2_uri, exponent_cap * 3)

  def test_daisy_chain_cp(self):
    """Tests cp with the -D option."""
    bucket1_uri = self.CreateBucket(storage_class='standard')
    bucket2_uri = self.CreateBucket(
        storage_class='durable_reduced_availability')
    key_uri = self.CreateObject(bucket_uri=bucket1_uri, contents=b'foo')
    # Set some headers on source object so we can verify that headers are
    # presereved by daisy-chain copy.
    self.RunGsUtil([
        'setmeta', '-h', 'Cache-Control:public,max-age=12', '-h',
        'Content-Type:image/gif', '-h',
        'x-%s-meta-1:abcd' % self.provider_custom_meta,
        suri(key_uri)
    ])
    # Set public-read (non-default) ACL so we can verify that cp -D -p works.
    self.RunGsUtil(['acl', 'set', 'public-read', suri(key_uri)])
    acl_json = self.RunGsUtil(['acl', 'get', suri(key_uri)], return_stdout=True)
    # Perform daisy-chain copy and verify that source object headers and ACL
    # were preserved. Also specify -n option to test that gsutil correctly
    # removes the x-goog-if-generation-match:0 header that was set at uploading
    # time when updating the ACL.
    stderr = self.RunGsUtil(
        ['cp', '-Dpn', suri(key_uri),
         suri(bucket2_uri)], return_stderr=True)
    self.assertNotIn('Copy-in-the-cloud disallowed', stderr)

    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check():
      uri = suri(bucket2_uri, key_uri.object_name)
      stdout = self.RunGsUtil(['ls', '-L', uri], return_stdout=True)
      self.assertRegex(stdout, r'Cache-Control:\s+public,max-age=12')
      self.assertRegex(stdout, r'Content-Type:\s+image/gif')
      self.assertRegex(stdout, r'Metadata:\s+1:\s+abcd')
      new_acl_json = self.RunGsUtil(['acl', 'get', uri], return_stdout=True)
      self.assertEqual(acl_json, new_acl_json)

    _Check()

  @unittest.skipUnless(
      not HAS_GS_PORT, 'gs_port is defined in config which can cause '
      'problems when uploading and downloading to the same local host port')
  def test_daisy_chain_cp_download_failure(self):
    """Tests cp with the -D option when the download thread dies."""
    bucket1_uri = self.CreateBucket()
    bucket2_uri = self.CreateBucket()
    key_uri = self.CreateObject(bucket_uri=bucket1_uri,
                                contents=b'a' * self.halt_size)
    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))
    with SetBotoConfigForTest([boto_config_for_test]):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file, '-D',
          suri(key_uri),
          suri(bucket2_uri)
      ],
                              expected_status=1,
                              return_stderr=True)
      # Should have three exception traces; one from the download thread and
      # two from the upload thread (expection message is repeated in main's
      # _OutputAndExit).
      self.assertEqual(
          stderr.count(
              'ResumableDownloadException: Artifically halting download'), 3)

  def test_streaming_gzip_upload(self):
    """Tests error when compression flag is requested on a streaming source."""
    bucket_uri = self.CreateBucket()
    stderr = self.RunGsUtil(
        ['cp', '-Z', '-', suri(bucket_uri, 'foo')],
        return_stderr=True,
        expected_status=1,
        stdin='streaming data')
    if self._use_gcloud_storage:
      self.assertIn(
          'Gzip content encoding is not currently supported for streaming '
          'uploads.', stderr)
    else:
      self.assertIn(
          'gzip compression is not currently supported on streaming uploads',
          stderr)

  def test_seek_ahead_upload_cp(self):
    """Tests that the seek-ahead iterator estimates total upload work."""
    tmpdir = self.CreateTempDir(test_files=3)
    bucket_uri = self.CreateBucket()

    with SetBotoConfigForTest([('GSUtil', 'task_estimation_threshold', '1'),
                               ('GSUtil', 'task_estimation_force', 'True')]):
      stderr = self.RunGsUtil(
          ['-m', 'cp', '-r', tmpdir, suri(bucket_uri)], return_stderr=True)
      self.assertIn(
          'Estimated work for this command: objects: 3, total size: 18', stderr)

    with SetBotoConfigForTest([('GSUtil', 'task_estimation_threshold', '0'),
                               ('GSUtil', 'task_estimation_force', 'True')]):
      stderr = self.RunGsUtil(
          ['-m', 'cp', '-r', tmpdir, suri(bucket_uri)], return_stderr=True)
      self.assertNotIn('Estimated work', stderr)

  def test_seek_ahead_download_cp(self):
    tmpdir = self.CreateTempDir()
    bucket_uri = self.CreateBucket(test_objects=3)
    self.AssertNObjectsInBucket(bucket_uri, 3)

    with SetBotoConfigForTest([('GSUtil', 'task_estimation_threshold', '1'),
                               ('GSUtil', 'task_estimation_force', 'True')]):
      stderr = self.RunGsUtil(
          ['-m', 'cp', '-r', suri(bucket_uri), tmpdir], return_stderr=True)
      self.assertIn(
          'Estimated work for this command: objects: 3, total size: 18', stderr)

    with SetBotoConfigForTest([('GSUtil', 'task_estimation_threshold', '0'),
                               ('GSUtil', 'task_estimation_force', 'True')]):
      stderr = self.RunGsUtil(
          ['-m', 'cp', '-r', suri(bucket_uri), tmpdir], return_stderr=True)
      self.assertNotIn('Estimated work', stderr)

  def test_canned_acl_cp(self):
    """Tests copying with a canned ACL."""
    bucket1_uri = self.CreateBucket()
    bucket2_uri = self.CreateBucket()
    key_uri = self.CreateObject(bucket_uri=bucket1_uri, contents=b'foo')
    self.RunGsUtil(
        ['cp', '-a', 'public-read',
         suri(key_uri),
         suri(bucket2_uri)])
    # Set public-read on the original key after the copy so we can compare
    # the ACLs.
    self.RunGsUtil(['acl', 'set', 'public-read', suri(key_uri)])
    public_read_acl = self.RunGsUtil(['acl', 'get', suri(key_uri)],
                                     return_stdout=True)

    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check():
      uri = suri(bucket2_uri, key_uri.object_name)
      new_acl_json = self.RunGsUtil(['acl', 'get', uri], return_stdout=True)
      self.assertEqual(public_read_acl, new_acl_json)

    _Check()

  @SequentialAndParallelTransfer
  def test_canned_acl_upload(self):
    """Tests uploading a file with a canned ACL."""
    bucket1_uri = self.CreateBucket()
    key_uri = self.CreateObject(bucket_uri=bucket1_uri, contents=b'foo')
    # Set public-read on the object so we can compare the ACLs.
    self.RunGsUtil(['acl', 'set', 'public-read', suri(key_uri)])
    public_read_acl = self.RunGsUtil(['acl', 'get', suri(key_uri)],
                                     return_stdout=True)

    file_name = 'bar'
    fpath = self.CreateTempFile(file_name=file_name, contents=b'foo')
    self.RunGsUtil(['cp', '-a', 'public-read', fpath, suri(bucket1_uri)])
    new_acl_json = self.RunGsUtil(
        ['acl', 'get', suri(bucket1_uri, file_name)], return_stdout=True)
    self.assertEqual(public_read_acl, new_acl_json)

    resumable_size = ONE_KIB
    boto_config_for_test = ('GSUtil', 'resumable_threshold',
                            str(resumable_size))
    with SetBotoConfigForTest([boto_config_for_test]):
      resumable_file_name = 'resumable_bar'
      resumable_contents = os.urandom(resumable_size)
      resumable_fpath = self.CreateTempFile(file_name=resumable_file_name,
                                            contents=resumable_contents)
      self.RunGsUtil(
          ['cp', '-a', 'public-read', resumable_fpath,
           suri(bucket1_uri)])
      new_resumable_acl_json = self.RunGsUtil(
          ['acl', 'get', suri(bucket1_uri, resumable_file_name)],
          return_stdout=True)
      self.assertEqual(public_read_acl, new_resumable_acl_json)

  def test_cp_key_to_local_stream(self):
    bucket_uri = self.CreateBucket()
    contents = b'foo'
    key_uri = self.CreateObject(bucket_uri=bucket_uri, contents=contents)
    stdout = self.RunGsUtil(['cp', suri(key_uri), '-'], return_stdout=True)
    self.assertIn(contents, stdout.encode('ascii'))

  def test_cp_local_file_to_local_stream(self):
    contents = b'content'
    fpath = self.CreateTempFile(contents=contents)
    stdout = self.RunGsUtil(['cp', fpath, '-'], return_stdout=True)
    self.assertIn(contents, stdout.encode(UTF8))

  @SequentialAndParallelTransfer
  def test_cp_zero_byte_file(self):
    dst_bucket_uri = self.CreateBucket()
    src_dir = self.CreateTempDir()
    fpath = os.path.join(src_dir, 'zero_byte')
    with open(fpath, 'w') as unused_out_file:
      pass  # Write a zero byte file
    self.RunGsUtil(['cp', fpath, suri(dst_bucket_uri)])

    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', suri(dst_bucket_uri)], return_stdout=True)
      self.assertIn(os.path.basename(fpath), stdout)

    _Check1()

    download_path = os.path.join(src_dir, 'zero_byte_download')
    self.RunGsUtil(['cp', suri(dst_bucket_uri, 'zero_byte'), download_path])
    self.assertTrue(os.stat(download_path))

  def test_copy_bucket_to_bucket(self):
    """Tests recursively copying from bucket to bucket.

    This should produce identically named objects (and not, in particular,
    destination objects named by the version-specific URI from source objects).
    """
    src_bucket_uri = self.CreateVersionedBucket()
    dst_bucket_uri = self.CreateVersionedBucket()
    self.CreateObject(bucket_uri=src_bucket_uri,
                      object_name='obj0',
                      contents=b'abc')
    self.CreateObject(bucket_uri=src_bucket_uri,
                      object_name='obj1',
                      contents=b'def')

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _CopyAndCheck():
      self.RunGsUtil(['cp', '-R', suri(src_bucket_uri), suri(dst_bucket_uri)])
      stdout = self.RunGsUtil(['ls', '-R', dst_bucket_uri.uri],
                              return_stdout=True)
      self.assertIn(
          '%s%s/obj0\n' % (dst_bucket_uri, src_bucket_uri.bucket_name), stdout)
      self.assertIn(
          '%s%s/obj1\n' % (dst_bucket_uri, src_bucket_uri.bucket_name), stdout)

    _CopyAndCheck()

  def test_copy_duplicate_nested_object_names_to_new_cloud_dir(self):
    """Tests copying from bucket to same bucket preserves file structure."""
    bucket_uri = self.CreateBucket()
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name='dir1/file.txt',
                      contents=b'data')
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name='dir2/file.txt',
                      contents=b'data')

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _CopyAndCheck():
      self.RunGsUtil(
          ['cp', '-R',
           suri(bucket_uri) + '/*',
           suri(bucket_uri) + '/dst'])
      stdout = self.RunGsUtil(['ls', '-R', bucket_uri.uri], return_stdout=True)
      self.assertIn(suri(bucket_uri) + '/dst/dir1/file.txt', stdout)
      self.assertIn(suri(bucket_uri) + '/dst/dir2/file.txt', stdout)

    _CopyAndCheck()

  def test_copy_duplicate_nested_object_names_to_existing_cloud_dir(self):
    """Tests copying from bucket to same bucket preserves file structure."""
    bucket_uri = self.CreateBucket()
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name='dir1/file.txt',
                      contents=b'data')
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name='dir2/file.txt',
                      contents=b'data')
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name='dst/existing_file.txt',
                      contents=b'data')

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _CopyAndCheck():
      self.RunGsUtil(
          ['cp', '-R',
           suri(bucket_uri) + '/*',
           suri(bucket_uri) + '/dst'])
      stdout = self.RunGsUtil(['ls', '-R', bucket_uri.uri], return_stdout=True)
      self.assertIn(suri(bucket_uri) + '/dst/dir1/file.txt', stdout)
      self.assertIn(suri(bucket_uri) + '/dst/dir2/file.txt', stdout)
      self.assertIn(suri(bucket_uri) + '/dst/existing_file.txt', stdout)

    _CopyAndCheck()

  @SkipForGS('Only s3 V4 signatures error on location mismatches.')
  def test_copy_bucket_to_bucket_with_location_redirect(self):
    # cp uses a sender function that raises an exception on location mismatches,
    # instead of returning a response. This integration test ensures retries
    # from exceptions work correctly.

    src_bucket_region = 'ap-east-1'
    dest_bucket_region = 'us-east-2'
    src_bucket_host = 's3.%s.amazonaws.com' % src_bucket_region
    dest_bucket_host = 's3.%s.amazonaws.com' % dest_bucket_region
    client_host = 's3.eu-west-1.amazonaws.com'

    with SetBotoConfigForTest([('s3', 'host', src_bucket_host)]):
      src_bucket_uri = self.CreateBucket(location=src_bucket_region)
      self.CreateObject(bucket_uri=src_bucket_uri,
                        object_name='obj0',
                        contents=b'abc')
      self.CreateObject(bucket_uri=src_bucket_uri,
                        object_name='obj1',
                        contents=b'def')

    with SetBotoConfigForTest([('s3', 'host', dest_bucket_host)]):
      dst_bucket_uri = self.CreateBucket(location=dest_bucket_region)

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _CopyAndCheck():
      self.RunGsUtil(['cp', '-R', suri(src_bucket_uri), suri(dst_bucket_uri)])
      stdout = self.RunGsUtil(['ls', '-R', dst_bucket_uri.uri],
                              return_stdout=True)
      self.assertIn(
          '%s%s/obj0\n' % (dst_bucket_uri, src_bucket_uri.bucket_name), stdout)
      self.assertIn(
          '%s%s/obj1\n' % (dst_bucket_uri, src_bucket_uri.bucket_name), stdout)

    with SetBotoConfigForTest([('s3', 'host', client_host)]):
      _CopyAndCheck()

  def test_copy_bucket_to_dir(self):
    """Tests recursively copying from bucket to a directory.

    This should produce identically named objects (and not, in particular,
    destination objects named by the version- specific URI from source objects).
    """
    src_bucket_uri = self.CreateBucket()
    dst_dir = self.CreateTempDir()
    self.CreateObject(bucket_uri=src_bucket_uri,
                      object_name='obj0',
                      contents=b'abc')
    self.CreateObject(bucket_uri=src_bucket_uri,
                      object_name='obj1',
                      contents=b'def')

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _CopyAndCheck():
      """Copies the bucket recursively and validates the results."""
      self.RunGsUtil(['cp', '-R', suri(src_bucket_uri), dst_dir])
      dir_list = []
      for dirname, _, filenames in os.walk(dst_dir):
        for filename in filenames:
          dir_list.append(os.path.join(dirname, filename))
      dir_list = sorted(dir_list)
      self.assertEqual(len(dir_list), 2)
      self.assertEqual(
          os.path.join(dst_dir, src_bucket_uri.bucket_name, 'obj0'),
          dir_list[0])
      self.assertEqual(
          os.path.join(dst_dir, src_bucket_uri.bucket_name, 'obj1'),
          dir_list[1])

    _CopyAndCheck()

  @unittest.skipUnless(HAS_S3_CREDS, 'Test requires both S3 and GS credentials')
  def test_copy_object_to_dir_s3_v4(self):
    """Tests copying object from s3 to local dir with v4 signature.

    Regions like us-east2 accept only V4 signature, hence we will create
    the bucket in us-east2 region to enforce testing with V4 signature.
    """
    src_bucket_uri = self.CreateBucket(provider='s3', location='us-east-2')
    dst_dir = self.CreateTempDir()
    self.CreateObject(bucket_uri=src_bucket_uri,
                      object_name='obj0',
                      contents=b'abc')
    self.CreateObject(bucket_uri=src_bucket_uri,
                      object_name='obj1',
                      contents=b'def')

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _CopyAndCheck():
      """Copies the bucket recursively and validates the results."""
      self.RunGsUtil(['cp', '-R', suri(src_bucket_uri), dst_dir])
      dir_list = []
      for dirname, _, filenames in os.walk(dst_dir):
        for filename in filenames:
          dir_list.append(os.path.join(dirname, filename))
      dir_list = sorted(dir_list)
      self.assertEqual(len(dir_list), 2)
      self.assertEqual(
          os.path.join(dst_dir, src_bucket_uri.bucket_name, 'obj0'),
          dir_list[0])
      self.assertEqual(
          os.path.join(dst_dir, src_bucket_uri.bucket_name, 'obj1'),
          dir_list[1])

    _CopyAndCheck()

  @SkipForS3('The boto lib used for S3 does not handle objects '
             'starting with slashes if we use V4 signature')
  def test_recursive_download_with_leftover_slash_only_dir_placeholder(self):
    """Tests that we correctly handle leftover dir placeholders."""
    src_bucket_uri = self.CreateBucket()
    dst_dir = self.CreateTempDir()
    self.CreateObject(bucket_uri=src_bucket_uri,
                      object_name='obj0',
                      contents=b'abc')
    self.CreateObject(bucket_uri=src_bucket_uri,
                      object_name='obj1',
                      contents=b'def')

    # Create a placeholder like what can be left over by web GUI tools.
    key_uri = self.StorageUriCloneReplaceName(src_bucket_uri, '/')
    self.StorageUriSetContentsFromString(key_uri, '')
    self.AssertNObjectsInBucket(src_bucket_uri, 3)

    self.RunGsUtil(['cp', '-R', suri(src_bucket_uri), dst_dir])
    dir_list = []
    for dirname, _, filenames in os.walk(dst_dir):
      for filename in filenames:
        dir_list.append(os.path.join(dirname, filename))
    dir_list = sorted(dir_list)
    self.assertEqual(len(dir_list), 2)
    self.assertEqual(os.path.join(dst_dir, src_bucket_uri.bucket_name, 'obj0'),
                     dir_list[0])
    self.assertEqual(os.path.join(dst_dir, src_bucket_uri.bucket_name, 'obj1'),
                     dir_list[1])

  def test_recursive_download_with_leftover_dir_placeholder(self):
    """Tests that we correctly handle leftover dir placeholders."""
    src_bucket_uri = self.CreateBucket()
    dst_dir = self.CreateTempDir()
    self.CreateObject(bucket_uri=src_bucket_uri,
                      object_name='obj0',
                      contents=b'abc')
    self.CreateObject(bucket_uri=src_bucket_uri,
                      object_name='obj1',
                      contents=b'def')

    # Create a placeholder like what can be left over by web GUI tools.
    key_uri = self.StorageUriCloneReplaceName(src_bucket_uri, 'foo/')
    self.StorageUriSetContentsFromString(key_uri, '')
    self.AssertNObjectsInBucket(src_bucket_uri, 3)

    self.RunGsUtil(['cp', '-R', suri(src_bucket_uri), dst_dir])
    dir_list = []
    for dirname, _, filenames in os.walk(dst_dir):
      for filename in filenames:
        dir_list.append(os.path.join(dirname, filename))
    dir_list = sorted(dir_list)
    self.assertEqual(len(dir_list), 2)
    self.assertEqual(os.path.join(dst_dir, src_bucket_uri.bucket_name, 'obj0'),
                     dir_list[0])
    self.assertEqual(os.path.join(dst_dir, src_bucket_uri.bucket_name, 'obj1'),
                     dir_list[1])

  def test_copy_quiet(self):
    bucket_uri = self.CreateBucket()
    key_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
    stderr = self.RunGsUtil([
        '-q', 'cp',
        suri(key_uri),
        suri(self.StorageUriCloneReplaceName(bucket_uri, 'o2'))
    ],
                            return_stderr=True)
    self.assertEqual(stderr.count('Copying '), 0)

  def test_cp_md5_match(self):
    """Tests that the uploaded object has the expected MD5.

    Note that while this does perform a file to object upload, MD5's are
    not supported for composite objects so we don't use the decorator in this
    case.
    """
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=b'bar')
    with open(fpath, 'rb') as f_in:
      md5 = binascii.unhexlify(CalculateMd5FromContents(f_in))
      try:
        encoded_bytes = base64.encodebytes(md5)
      except AttributeError:
        # For Python 2 compatability.
        encoded_bytes = base64.encodestring(md5)
      file_md5 = encoded_bytes.rstrip(b'\n')
    self.RunGsUtil(['cp', fpath, suri(bucket_uri)])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _Check1():
      stdout = self.RunGsUtil(['ls', '-L', suri(bucket_uri)],
                              return_stdout=True)
      self.assertRegex(
          stdout, r'Hash\s+\(md5\):\s+%s' % re.escape(file_md5.decode('ascii')))

    _Check1()

  @unittest.skipIf(
      IS_WINDOWS, 'Unicode handling on Windows requires mods to site-packages')
  @SequentialAndParallelTransfer
  def test_cp_manifest_upload_unicode(self):
    return self._ManifestUpload('foo-unicöde'.encode(UTF8),
                                'bar-unicöde'.encode(UTF8),
                                'manifest-unicöde'.encode(UTF8))

  @SequentialAndParallelTransfer
  def test_cp_manifest_upload(self):
    """Tests uploading with a mnifest file."""
    return self._ManifestUpload('foo', 'bar', 'manifest')

  def _ManifestUpload(self, file_name, object_name, manifest_name):
    """Tests uploading with a manifest file."""
    bucket_uri = self.CreateBucket()
    dsturi = suri(bucket_uri, object_name)

    fpath = self.CreateTempFile(file_name=file_name, contents=b'bar')
    logpath = self.CreateTempFile(file_name=manifest_name, contents=b'')
    # Ensure the file is empty.
    open(logpath, 'w').close()
    self.RunGsUtil(['cp', '-L', logpath, fpath, dsturi])

    with open(logpath, 'r') as f:
      lines = f.readlines()
    if six.PY2:
      lines = [six.text_type(line, UTF8) for line in lines]

    self.assertEqual(len(lines), 2)

    expected_headers = [
        'Source', 'Destination', 'Start', 'End', 'Md5', 'UploadId',
        'Source Size', 'Bytes Transferred', 'Result', 'Description'
    ]
    self.assertEqual(expected_headers, lines[0].strip().split(','))
    results = lines[1].strip().split(',')

    results = dict(zip(expected_headers, results))

    self.assertEqual(
        results['Source'],
        'file://' + fpath,
    )
    self.assertEqual(
        results['Destination'],
        dsturi,
    )

    date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    start_date = datetime.datetime.strptime(results['Start'], date_format)
    end_date = datetime.datetime.strptime(results['End'], date_format)
    self.assertEqual(end_date > start_date, True)

    if self.RunGsUtil == testcase.GsUtilIntegrationTestCase.RunGsUtil:
      # Check that we didn't do automatic parallel uploads - compose doesn't
      # calculate the MD5 hash. Since RunGsUtil is overriden in
      # TestCpParallelUploads to force parallel uploads, we can check which
      # method was used.
      self.assertEqual(results['Md5'], 'rL0Y20zC+Fzt72VPzMSk2A==')

    self.assertEqual(int(results['Source Size']), 3)
    self.assertEqual(int(results['Bytes Transferred']), 3)
    self.assertEqual(results['Result'], 'OK')

  @SequentialAndParallelTransfer
  def test_cp_manifest_download(self):
    """Tests downloading with a manifest file."""
    key_uri = self.CreateObject(contents=b'foo')
    fpath = self.CreateTempFile(contents=b'')
    logpath = self.CreateTempFile(contents=b'')
    # Ensure the file is empty.
    open(logpath, 'w').close()
    self.RunGsUtil(
        ['cp', '-L', logpath, suri(key_uri), fpath], return_stdout=True)
    with open(logpath, 'r') as f:
      lines = f.readlines()
    if six.PY3:
      decode_lines = []
      for line in lines:
        if line.startswith("b'"):
          some_strs = line.split(',')
          line_parts = []
          for some_str in some_strs:
            if some_str.startswith("b'"):
              line_parts.append(ast.literal_eval(some_str).decode(UTF8))
            else:
              line_parts.append(some_str)
          decode_lines.append(','.join(line_parts))
        else:
          decode_lines.append(line)
      lines = decode_lines
    self.assertEqual(len(lines), 2)

    expected_headers = [
        'Source', 'Destination', 'Start', 'End', 'Md5', 'UploadId',
        'Source Size', 'Bytes Transferred', 'Result', 'Description'
    ]
    self.assertEqual(expected_headers, lines[0].strip().split(','))

    results = lines[1].strip().split(',')
    self.assertEqual(results[0][:5], '%s://' % self.default_provider)  # source
    self.assertEqual(results[1][:7], 'file://')  # destination
    date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
    start_date = datetime.datetime.strptime(results[2], date_format)
    end_date = datetime.datetime.strptime(results[3], date_format)
    self.assertEqual(end_date > start_date, True)
    self.assertEqual(int(results[6]), 3)  # Source Size
    # Bytes transferred might be more than 3 if the file was gzipped, since
    # the minimum gzip header is 10 bytes.
    self.assertGreaterEqual(int(results[7]), 3)  # Bytes Transferred
    self.assertEqual(results[8], 'OK')  # Result

  @SequentialAndParallelTransfer
  def test_copy_unicode_non_ascii_filename(self):
    key_uri = self.CreateObject()
    # Try with and without resumable upload threshold, to ensure that each
    # scenario works. In particular, resumable uploads have tracker filename
    # logic.
    file_contents = b'x' * START_CALLBACK_PER_BYTES * 2
    fpath = self.CreateTempFile(file_name='Аудиоархив', contents=file_contents)
    with SetBotoConfigForTest([('GSUtil', 'resumable_threshold', '1')]):
      # fpath_bytes = fpath.encode(UTF8)
      self.RunGsUtil(['cp', fpath, suri(key_uri)], return_stderr=True)
      stdout = self.RunGsUtil(['cat', suri(key_uri)],
                              return_stdout=True,
                              force_gsutil=True)
      self.assertEqual(stdout.encode('ascii'), file_contents)
    with SetBotoConfigForTest([('GSUtil', 'resumable_threshold',
                                str(START_CALLBACK_PER_BYTES * 3))]):
      self.RunGsUtil(['cp', fpath, suri(key_uri)], return_stderr=True)
      stdout = self.RunGsUtil(['cat', suri(key_uri)],
                              return_stdout=True,
                              force_gsutil=True)
      self.assertEqual(stdout.encode('ascii'), file_contents)

  # Note: We originally one time implemented a test
  # (test_copy_invalid_unicode_filename) that invalid unicode filenames were
  # skipped, but it turns out os.walk() on macOS doesn't have problems with
  # such files (so, failed that test). Given that, we decided to remove the
  # test.

  @SequentialAndParallelTransfer
  def test_gzip_upload_and_download(self):
    bucket_uri = self.CreateBucket()
    contents = b'x' * 10000
    tmpdir = self.CreateTempDir()
    self.CreateTempFile(file_name='test.html', tmpdir=tmpdir, contents=contents)
    self.CreateTempFile(file_name='test.js', tmpdir=tmpdir, contents=contents)
    self.CreateTempFile(file_name='test.txt', tmpdir=tmpdir, contents=contents)
    # Test that copying specifying only 2 of the 3 prefixes gzips the correct
    # files, and test that including whitespace in the extension list works.
    self.RunGsUtil([
        'cp', '-z', 'js, html',
        os.path.join(tmpdir, 'test.*'),
        suri(bucket_uri)
    ])
    self.AssertNObjectsInBucket(bucket_uri, 3)
    uri1 = suri(bucket_uri, 'test.html')
    uri2 = suri(bucket_uri, 'test.js')
    uri3 = suri(bucket_uri, 'test.txt')
    stdout = self.RunGsUtil(['stat', uri1], return_stdout=True)
    self.assertRegex(stdout, r'Content-Encoding:\s+gzip')
    stdout = self.RunGsUtil(['stat', uri2], return_stdout=True)
    self.assertRegex(stdout, r'Content-Encoding:\s+gzip')
    stdout = self.RunGsUtil(['stat', uri3], return_stdout=True)
    self.assertNotRegex(stdout, r'Content-Encoding:\s+gzip')
    fpath4 = self.CreateTempFile()
    for uri in (uri1, uri2, uri3):
      self.RunGsUtil(['cp', uri, suri(fpath4)])
      with open(fpath4, 'rb') as f:
        self.assertEqual(f.read(), contents)

  @SkipForS3('No compressed transport encoding support for S3.')
  @SkipForXML('No compressed transport encoding support for the XML API.')
  @SequentialAndParallelTransfer
  def test_gzip_transport_encoded_upload_and_download(self):
    """Test gzip encoded files upload correctly.

    This checks that files are not tagged with a gzip content encoding and
    that the contents of the files are uncompressed in GCS. This test uses the
    -j flag to target specific extensions.
    """

    def _create_test_data():  # pylint: disable=invalid-name
      """Setup the bucket and local data to test with.

      Returns:
        Triplet containing the following values:
          bucket_uri: String URI of cloud storage bucket to upload mock data
                      to.
          tmpdir: String, path of a temporary directory to write mock data to.
          local_uris: Tuple of three strings; each is the file path to a file
                      containing mock data.
      """
      bucket_uri = self.CreateBucket()
      contents = b'x' * 10000
      tmpdir = self.CreateTempDir()

      local_uris = []
      for filename in ('test.html', 'test.js', 'test.txt'):
        local_uris.append(
            self.CreateTempFile(file_name=filename,
                                tmpdir=tmpdir,
                                contents=contents))

      return (bucket_uri, tmpdir, local_uris)

    def _upload_test_data(tmpdir, bucket_uri):  # pylint: disable=invalid-name
      """Upload local test data.

      Args:
        tmpdir: String, path of a temporary directory to write mock data to.
        bucket_uri: String URI of cloud storage bucket to upload mock data to.

      Returns:
        stderr: String output from running the gsutil command to upload mock
                  data.
      """
      if self._use_gcloud_storage:
        extension_list_string = 'js,html'
      else:
        extension_list_string = 'js, html'
      stderr = self.RunGsUtil([
          '-D', 'cp', '-j', extension_list_string,
          os.path.join(tmpdir, 'test*'),
          suri(bucket_uri)
      ],
                              return_stderr=True)
      self.AssertNObjectsInBucket(bucket_uri, 3)
      return stderr

    def _assert_sent_compressed(local_uris, stderr):  # pylint: disable=invalid-name
      """Ensure the correct files were marked for compression.

      Args:
        local_uris: Tuple of three strings; each is the file path to a file
                    containing mock data.
        stderr: String output from running the gsutil command to upload mock
                data.
      """
      local_uri_html, local_uri_js, local_uri_txt = local_uris
      assert_base_string = 'Using compressed transport encoding for file://{}.'
      self.assertIn(assert_base_string.format(local_uri_html), stderr)
      self.assertIn(assert_base_string.format(local_uri_js), stderr)
      self.assertNotIn(assert_base_string.format(local_uri_txt), stderr)

    def _assert_stored_uncompressed(bucket_uri, contents=b'x' * 10000):  # pylint: disable=invalid-name
      """Ensure the files are not compressed when they are stored in the bucket.

      Args:
        bucket_uri: String with URI for bucket containing uploaded test data.
        contents: Byte string that are stored in each file in the bucket.
      """
      local_uri_html = suri(bucket_uri, 'test.html')
      local_uri_js = suri(bucket_uri, 'test.js')
      local_uri_txt = suri(bucket_uri, 'test.txt')
      fpath4 = self.CreateTempFile()

      for uri in (local_uri_html, local_uri_js, local_uri_txt):
        stdout = self.RunGsUtil(['stat', uri], return_stdout=True)
        self.assertNotRegex(stdout, r'Content-Encoding:\s+gzip')
        self.RunGsUtil(['cp', uri, suri(fpath4)])
        with open(fpath4, 'rb') as f:
          self.assertEqual(f.read(), contents)

    # Get mock data, run tests
    bucket_uri, tmpdir, local_uris = _create_test_data()
    stderr = _upload_test_data(tmpdir, bucket_uri)
    _assert_sent_compressed(local_uris, stderr)
    _assert_stored_uncompressed(bucket_uri)

  @SkipForS3('No compressed transport encoding support for S3.')
  @SkipForXML('No compressed transport encoding support for the XML API.')
  @SequentialAndParallelTransfer
  def test_gzip_transport_encoded_parallel_upload_non_resumable(self):
    """Test non resumable, gzip encoded files upload correctly in parallel.

    This test generates a small amount of data (e.g. 100 chars) to upload.
    Due to the small size, it will be below the resumable threshold,
    and test the behavior of non-resumable uploads.
    """
    # Setup the bucket and local data.
    bucket_uri = self.CreateBucket()
    contents = b'x' * 100
    tmpdir = self.CreateTempDir(test_files=10, contents=contents)
    # Upload the data.
    with SetBotoConfigForTest([('GSUtil', 'resumable_threshold', str(ONE_KIB))
                              ]):
      stderr = self.RunGsUtil(
          ['-D', '-m', 'cp', '-J', '-r', tmpdir,
           suri(bucket_uri)],
          return_stderr=True)
      # Ensure all objects are uploaded.
      self.AssertNObjectsInBucket(bucket_uri, 10)
      if not self._use_gcloud_storage:
        # Ensure the progress logger sees a gzip encoding.
        self.assertIn('send: Using gzip transport encoding for the request.',
                      stderr)

  @SkipForS3('No compressed transport encoding support for S3.')
  @SkipForXML('No compressed transport encoding support for the XML API.')
  @SequentialAndParallelTransfer
  def test_gzip_transport_encoded_parallel_upload_resumable(self):
    """Test resumable, gzip encoded files upload correctly in parallel.

    This test generates a large amount of data (e.g. halt_size amount of chars)
    to upload. Due to the large size, it will be above the resumable threshold,
    and test the behavior of resumable uploads.
    """
    # Setup the bucket and local data.
    bucket_uri = self.CreateBucket()
    contents = get_random_ascii_chars(size=self.halt_size)
    tmpdir = self.CreateTempDir(test_files=10, contents=contents)
    # Upload the data.
    with SetBotoConfigForTest([('GSUtil', 'resumable_threshold', str(ONE_KIB))
                              ]):
      stderr = self.RunGsUtil(
          ['-D', '-m', 'cp', '-J', '-r', tmpdir,
           suri(bucket_uri)],
          return_stderr=True)
      # Ensure all objects are uploaded.
      self.AssertNObjectsInBucket(bucket_uri, 10)
      if not self._use_gcloud_storage:
        # Ensure the progress logger sees a gzip encoding.
        self.assertIn('send: Using gzip transport encoding for the request.',
                      stderr)

  @SequentialAndParallelTransfer
  def test_gzip_all_upload_and_download(self):
    bucket_uri = self.CreateBucket()
    contents = b'x' * 10000
    tmpdir = self.CreateTempDir()
    self.CreateTempFile(file_name='test.html', tmpdir=tmpdir, contents=contents)
    self.CreateTempFile(file_name='test.js', tmpdir=tmpdir, contents=contents)
    self.CreateTempFile(file_name='test.txt', tmpdir=tmpdir, contents=contents)
    self.CreateTempFile(file_name='test', tmpdir=tmpdir, contents=contents)
    # Test that all files are compressed.
    self.RunGsUtil(
        ['cp', '-Z',
         os.path.join(tmpdir, 'test*'),
         suri(bucket_uri)])
    self.AssertNObjectsInBucket(bucket_uri, 4)
    uri1 = suri(bucket_uri, 'test.html')
    uri2 = suri(bucket_uri, 'test.js')
    uri3 = suri(bucket_uri, 'test.txt')
    uri4 = suri(bucket_uri, 'test')
    stdout = self.RunGsUtil(['stat', uri1], return_stdout=True)
    self.assertRegex(stdout, r'Content-Encoding:\s+gzip')
    stdout = self.RunGsUtil(['stat', uri2], return_stdout=True)
    self.assertRegex(stdout, r'Content-Encoding:\s+gzip')
    stdout = self.RunGsUtil(['stat', uri3], return_stdout=True)
    self.assertRegex(stdout, r'Content-Encoding:\s+gzip')
    stdout = self.RunGsUtil(['stat', uri4], return_stdout=True)
    self.assertRegex(stdout, r'Content-Encoding:\s+gzip')
    fpath4 = self.CreateTempFile()
    for uri in (uri1, uri2, uri3, uri4):
      self.RunGsUtil(['cp', uri, suri(fpath4)])
      with open(fpath4, 'rb') as f:
        self.assertEqual(f.read(), contents)

  @SkipForS3('No compressed transport encoding support for S3.')
  @SkipForXML('No compressed transport encoding support for the XML API.')
  @SequentialAndParallelTransfer
  def test_gzip_transport_encoded_all_upload_and_download(self):
    """Test gzip encoded files upload correctly.

    This checks that files are not tagged with a gzip content encoding and
    that the contents of the files are uncompressed in GCS. This test uses the
    -J flag to target all files.
    """
    # Setup the bucket and local data.
    bucket_uri = self.CreateBucket()
    contents = b'x' * 10000
    tmpdir = self.CreateTempDir()
    local_uri1 = self.CreateTempFile(file_name='test.txt',
                                     tmpdir=tmpdir,
                                     contents=contents)
    local_uri2 = self.CreateTempFile(file_name='test',
                                     tmpdir=tmpdir,
                                     contents=contents)
    # Upload the data.
    stderr = self.RunGsUtil(
        ['-D', 'cp', '-J',
         os.path.join(tmpdir, 'test*'),
         suri(bucket_uri)],
        return_stderr=True)
    self.AssertNObjectsInBucket(bucket_uri, 2)
    # Ensure the correct files were marked for compression.
    self.assertIn(
        'Using compressed transport encoding for file://%s.' % (local_uri1),
        stderr)
    self.assertIn(
        'Using compressed transport encoding for file://%s.' % (local_uri2),
        stderr)
    if not self._use_gcloud_storage:
      # Ensure the progress logger sees a gzip encoding.
      self.assertIn('send: Using gzip transport encoding for the request.',
                    stderr)
    # Ensure the files do not have a stored encoding of gzip and are stored
    # uncompressed.
    remote_uri1 = suri(bucket_uri, 'test.txt')
    remote_uri2 = suri(bucket_uri, 'test')
    fpath4 = self.CreateTempFile()
    for uri in (remote_uri1, remote_uri2):
      stdout = self.RunGsUtil(['stat', uri], return_stdout=True)
      self.assertNotRegex(stdout, r'Content-Encoding:\s+gzip')
      self.RunGsUtil(['cp', uri, suri(fpath4)])
      with open(fpath4, 'rb') as f:
        self.assertEqual(f.read(), contents)

  def test_both_gzip_options_error(self):
    """Test that mixing compression flags error."""
    cases = (
        # Test with -Z and -z
        ['cp', '-Z', '-z', 'html, js', 'a.js', 'b.js'],
        # Same test, but with arguments in the opposite order.
        ['cp', '-z', 'html, js', '-Z', 'a.js', 'b.js'])

    if self._use_gcloud_storage:
      expected_status, expected_error_prefix, expected_error_substring = (
          _GCLOUD_STORAGE_GZIP_FLAG_CONFLICT_OUTPUT)
    else:
      expected_status = 1
      expected_error_prefix = 'CommandException'
      expected_error_substring = (
          'Specifying both the -z and -Z options together is invalid.')
    for case in cases:
      stderr = self.RunGsUtil(case,
                              return_stderr=True,
                              expected_status=expected_status)
      self.assertIn(expected_error_prefix, stderr)
      self.assertIn(expected_error_substring, stderr)

  def test_both_gzip_transport_encoding_options_error(self):
    """Test that mixing transport encoding flags error."""
    cases = (
        # Test with -J and -j
        ['cp', '-J', '-j', 'html, js', 'a.js', 'b.js'],
        # Same test, but with arguments in the opposite order.
        ['cp', '-j', 'html, js', '-J', 'a.js', 'b.js'])

    if self._use_gcloud_storage:
      expected_status, expected_error_prefix, expected_error_substring = (
          _GCLOUD_STORAGE_GZIP_FLAG_CONFLICT_OUTPUT)
    else:
      expected_status = 1
      expected_error_prefix = 'CommandException'
      expected_error_substring = (
          'Specifying both the -j and -J options together is invalid.')

    for case in cases:
      stderr = self.RunGsUtil(case,
                              return_stderr=True,
                              expected_status=expected_status)
      self.assertIn(expected_error_prefix, stderr)
      self.assertIn(expected_error_substring, stderr)

  def test_combined_gzip_options_error(self):
    """Test that mixing transport encoding and compression flags error."""
    cases = (['cp', '-Z', '-j', 'html, js', 'a.js',
              'b.js'], ['cp', '-J', '-z', 'html, js', 'a.js',
                        'b.js'], ['cp', '-j', 'html, js', '-Z', 'a.js', 'b.js'],
             ['cp', '-z', 'html, js', '-J', 'a.js', 'b.js'])

    if self._use_gcloud_storage:
      expected_status, expected_error_prefix, expected_error_substring = (
          _GCLOUD_STORAGE_GZIP_FLAG_CONFLICT_OUTPUT)
    else:
      expected_status = 1
      expected_error_prefix = 'CommandException'
      expected_error_substring = (
          'Specifying both the -j/-J and -z/-Z options together is invalid.')

    for case in cases:
      stderr = self.RunGsUtil(case,
                              return_stderr=True,
                              expected_status=expected_status)
      self.assertIn(expected_error_prefix, stderr)
      self.assertIn(expected_error_substring, stderr)

  def test_upload_with_subdir_and_unexpanded_wildcard(self):
    fpath1 = self.CreateTempFile(file_name=('tmp', 'x', 'y', 'z'))
    bucket_uri = self.CreateBucket()
    wildcard_uri = '%s*' % fpath1[:-5]
    stderr = self.RunGsUtil(
        ['cp', '-R', wildcard_uri, suri(bucket_uri)], return_stderr=True)
    self.assertIn('Copying file:', stderr)
    self.AssertNObjectsInBucket(bucket_uri, 1)

  def test_upload_does_not_raise_with_content_md5_and_check_hashes_never(self):
    fpath1 = self.CreateTempFile(file_name=('foo'))
    bucket_uri = self.CreateBucket()
    with SetBotoConfigForTest([('GSUtil', 'check_hashes', 'never')]):
      stderr = self.RunGsUtil(
          ['-h', 'Content-MD5: invalid-md5', 'cp', fpath1,
           suri(bucket_uri)],
          return_stderr=True)
      self.assertIn('Copying file:', stderr)
    self.AssertNObjectsInBucket(bucket_uri, 1)

  @SequentialAndParallelTransfer
  def test_cp_object_ending_with_slash(self):
    """Tests that cp works with object names ending with slash."""
    tmpdir = self.CreateTempDir()
    bucket_uri = self.CreateBucket()
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name='abc/',
                      contents=b'dir')
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name='abc/def',
                      contents=b'def')
    self.AssertNObjectsInBucket(bucket_uri, 2)
    self.RunGsUtil(['cp', '-R', suri(bucket_uri), tmpdir])
    # Check that files in the subdir got copied even though subdir object
    # download was skipped.
    with open(os.path.join(tmpdir, bucket_uri.bucket_name, 'abc', 'def')) as f:
      self.assertEqual('def', '\n'.join(f.readlines()))

  def test_cp_without_read_access(self):
    """Tests that cp fails without read access to the object."""
    # TODO: With 401's triggering retries in apitools, this test will take
    # a long time.  Ideally, make apitools accept a num_retries config for this
    # until we stop retrying the 401's.
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')

    # Use @Retry as hedge against bucket listing eventual consistency.
    self.AssertNObjectsInBucket(bucket_uri, 1)

    if self.default_provider == 's3':
      expected_error_regex = r'AccessDenied'
    else:
      expected_error_regex = r'Anonymous \S+ do(es)? not have'

    with self.SetAnonymousBotoCreds():
      stderr = self.RunGsUtil(['cp', suri(object_uri), 'foo'],
                              return_stderr=True,
                              expected_status=1)
    self.assertRegex(stderr, expected_error_regex)

  @unittest.skipIf(IS_WINDOWS, 'os.symlink() is not available on Windows.')
  def test_cp_minus_r_minus_e(self):
    """Tests that cp -e -r ignores symlinks when recursing."""
    bucket_uri = self.CreateBucket()
    tmpdir = self.CreateTempDir()
    # Create a valid file, since cp expects to copy at least one source URL
    # successfully.
    self.CreateTempFile(tmpdir=tmpdir, contents=b'foo')
    subdir = os.path.join(tmpdir, 'subdir')
    os.mkdir(subdir)
    os.mkdir(os.path.join(tmpdir, 'missing'))
    # Create a blank directory that is a broken symlink to ensure that we
    # don't fail recursive enumeration with a bad symlink.
    os.symlink(os.path.join(tmpdir, 'missing'), os.path.join(subdir, 'missing'))
    os.rmdir(os.path.join(tmpdir, 'missing'))
    self.RunGsUtil(['cp', '-r', '-e', tmpdir, suri(bucket_uri)])

  @unittest.skipIf(IS_WINDOWS, 'os.symlink() is not available on Windows.')
  def test_cp_minus_e(self):
    fpath_dir = self.CreateTempDir()
    fpath1 = self.CreateTempFile(tmpdir=fpath_dir)
    fpath2 = os.path.join(fpath_dir, 'cp_minus_e')
    bucket_uri = self.CreateBucket()
    os.symlink(fpath1, fpath2)
    # We also use -c to continue on errors. One of the expanded glob entries
    # should be the symlinked file, which should throw a CommandException since
    # no valid (non-symlinked) files could be found at that path; we don't want
    # the command to terminate if that's the first file we attempt to copy.
    stderr = self.RunGsUtil([
        '-m', 'cp', '-e',
        '%s%s*' % (fpath_dir, os.path.sep),
        suri(bucket_uri, 'files')
    ],
                            return_stderr=True)
    self.assertIn('Copying file', stderr)
    if self._use_gcloud_storage:
      self.assertIn('Skipping symlink', stderr)
    else:
      self.assertIn('Skipping symbolic link', stderr)

    # Ensure that top-level arguments are ignored if they are symlinks. The file
    # at fpath1 should be successfully copied, then copying the symlink at
    # fpath2 should fail.
    stderr = self.RunGsUtil(
        ['cp', '-e', '-r', fpath1, fpath2,
         suri(bucket_uri, 'files')],
        return_stderr=True,
        expected_status=1)
    self.assertIn('Copying file', stderr)
    if self._use_gcloud_storage:
      self.assertIn('Skipping symlink', stderr)
      self.assertIn('URL matched no objects or files: %s' % fpath2, stderr)
    else:
      self.assertIn('Skipping symbolic link', stderr)
      self.assertIn('CommandException: No URLs matched: %s' % fpath2, stderr)

  def test_cp_multithreaded_wildcard(self):
    """Tests that cp -m works with a wildcard."""
    num_test_files = 5
    tmp_dir = self.CreateTempDir(test_files=num_test_files)
    bucket_uri = self.CreateBucket()
    wildcard_uri = '%s%s*' % (tmp_dir, os.sep)
    self.RunGsUtil(['-m', 'cp', wildcard_uri, suri(bucket_uri)])
    self.AssertNObjectsInBucket(bucket_uri, num_test_files)

  @SequentialAndParallelTransfer
  def test_cp_duplicate_source_args(self):
    """Tests that cp -m works when a source argument is provided twice."""
    object_contents = b'edge'
    object_uri = self.CreateObject(object_name='foo', contents=object_contents)
    tmp_dir = self.CreateTempDir()
    self.RunGsUtil(['-m', 'cp', suri(object_uri), suri(object_uri), tmp_dir])
    with open(os.path.join(tmp_dir, 'foo'), 'rb') as in_fp:
      contents = in_fp.read()
      # Contents should be not duplicated.
      self.assertEqual(contents, object_contents)

  @SkipForS3('gsutil doesn\'t support S3 customer-supplied encryption keys.')
  @SequentialAndParallelTransfer
  def test_cp_download_encrypted_object(self):
    """Tests downloading an encrypted object."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    object_contents = b'bar'
    object_uri = self.CreateObject(object_name='foo',
                                   contents=object_contents,
                                   encryption_key=TEST_ENCRYPTION_KEY1)
    fpath = self.CreateTempFile()
    boto_config_for_test = [('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY1)]

    with SetBotoConfigForTest(boto_config_for_test):
      self.RunGsUtil(['cp', suri(object_uri), suri(fpath)])
    with open(fpath, 'rb') as f:
      self.assertEqual(f.read(), object_contents)

    # If multiple keys are supplied and one is correct, download should succeed.
    fpath2 = self.CreateTempFile()
    boto_config_for_test2 = [
        ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY3),
        ('GSUtil', 'decryption_key1', TEST_ENCRYPTION_KEY2),
        ('GSUtil', 'decryption_key2', TEST_ENCRYPTION_KEY1)
    ]

    with SetBotoConfigForTest(boto_config_for_test2):
      self.RunGsUtil(['cp', suri(object_uri), suri(fpath2)])
    with open(fpath2, 'rb') as f:
      self.assertEqual(f.read(), object_contents)

  @SkipForS3('gsutil doesn\'t support S3 customer-supplied encryption keys.')
  @SequentialAndParallelTransfer
  def test_cp_download_encrypted_object_without_key(self):
    """Tests downloading an encrypted object without the necessary key."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    object_contents = b'bar'
    object_uri = self.CreateObject(object_name='foo',
                                   contents=object_contents,
                                   encryption_key=TEST_ENCRYPTION_KEY1)
    fpath = self.CreateTempFile()

    stderr = self.RunGsUtil(
        ['cp', suri(object_uri), suri(fpath)],
        expected_status=1,
        return_stderr=True)
    self.assertIn(
        'Missing decryption key with SHA256 hash %s' %
        TEST_ENCRYPTION_KEY1_SHA256_B64, stderr)

  @SkipForS3('gsutil doesn\'t support S3 customer-supplied encryption keys.')
  @SequentialAndParallelTransfer
  def test_cp_upload_encrypted_object(self):
    """Tests uploading an encrypted object."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    bucket_uri = self.CreateBucket()
    object_uri = suri(bucket_uri, 'foo')
    file_contents = b'bar'
    fpath = self.CreateTempFile(contents=file_contents, file_name='foo')

    boto_config_for_test = [('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY1)]

    # Uploading the object should succeed.
    with SetBotoConfigForTest(boto_config_for_test):
      self.RunGsUtil(['cp', suri(fpath), suri(bucket_uri)])

    self.AssertObjectUsesCSEK(object_uri, TEST_ENCRYPTION_KEY1)

    with SetBotoConfigForTest(boto_config_for_test):
      # Reading the object back should succeed.
      fpath2 = self.CreateTempFile()
      self.RunGsUtil(['cp', suri(bucket_uri, 'foo'), suri(fpath2)])
      with open(fpath2, 'rb') as f:
        self.assertEqual(f.read(), file_contents)

  @SkipForS3('No resumable upload or encryption support for S3.')
  def test_cp_resumable_upload_encrypted_object_break(self):
    """Tests that an encrypted upload resumes after a connection break."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    bucket_uri = self.CreateBucket()
    object_uri_str = suri(bucket_uri, 'foo')
    fpath = self.CreateTempFile(contents=b'a' * self.halt_size)
    boto_config_for_test = [('GSUtil', 'resumable_threshold', str(ONE_KIB)),
                            ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY1)]
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(True, 5)))

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file, fpath, object_uri_str
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting upload', stderr)
      stderr = self.RunGsUtil(['cp', fpath, object_uri_str], return_stderr=True)
      self.assertIn('Resuming upload', stderr)
      stdout = self.RunGsUtil(['stat', object_uri_str], return_stdout=True)
      with open(fpath, 'rb') as fp:
        self.assertIn(CalculateB64EncodedMd5FromContents(fp), stdout)

    self.AssertObjectUsesCSEK(object_uri_str, TEST_ENCRYPTION_KEY1)

  @SkipForS3('No resumable upload or encryption support for S3.')
  def test_cp_resumable_upload_encrypted_object_different_key(self):
    """Tests that an encrypted upload resume uses original encryption key."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    bucket_uri = self.CreateBucket()
    object_uri_str = suri(bucket_uri, 'foo')
    file_contents = b'a' * self.halt_size
    fpath = self.CreateTempFile(contents=file_contents)
    boto_config_for_test = [('GSUtil', 'resumable_threshold', str(ONE_KIB)),
                            ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY1)]
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(True, 5)))

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file, fpath, object_uri_str
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting upload', stderr)

    # Resume the upload with multiple keys, including the original.
    boto_config_for_test2 = [('GSUtil', 'resumable_threshold', str(ONE_KIB)),
                             ('GSUtil', 'decryption_key1',
                              TEST_ENCRYPTION_KEY2),
                             ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY1)]

    with SetBotoConfigForTest(boto_config_for_test2):
      stderr = self.RunGsUtil(['cp', fpath, object_uri_str], return_stderr=True)
      self.assertIn('Resuming upload', stderr)

    # Object should have the original key.
    self.AssertObjectUsesCSEK(object_uri_str, TEST_ENCRYPTION_KEY1)

  @SkipForS3('No resumable upload or encryption support for S3.')
  def test_cp_resumable_upload_encrypted_object_missing_key(self):
    """Tests that an encrypted upload does not resume without original key."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    bucket_uri = self.CreateBucket()
    object_uri_str = suri(bucket_uri, 'foo')
    file_contents = b'a' * self.halt_size
    fpath = self.CreateTempFile(contents=file_contents)
    boto_config_for_test = [('GSUtil', 'resumable_threshold', str(ONE_KIB)),
                            ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY1)]
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(True, 5)))

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file, fpath, object_uri_str
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting upload', stderr)

    # Resume the upload without the original key.
    boto_config_for_test2 = [('GSUtil', 'resumable_threshold', str(ONE_KIB)),
                             ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY2)]

    with SetBotoConfigForTest(boto_config_for_test2):
      stderr = self.RunGsUtil(['cp', fpath, object_uri_str], return_stderr=True)
      self.assertNotIn('Resuming upload', stderr)
      self.assertIn('does not match current encryption key', stderr)
      self.assertIn('Restarting upload from scratch', stderr)

      # Object should have the new key.
      self.AssertObjectUsesCSEK(object_uri_str, TEST_ENCRYPTION_KEY2)

  def _ensure_object_unencrypted(self, object_uri_str):
    """Strongly consistent check that the object is unencrypted."""
    stdout = self.RunGsUtil(['stat', object_uri_str], return_stdout=True)
    self.assertNotIn('Encryption Key', stdout)

  @SkipForS3('No resumable upload support for S3.')
  def test_cp_resumable_upload_break(self):
    """Tests that an upload can be resumed after a connection break."""
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=b'a' * self.halt_size)
    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(True, 5)))

    with SetBotoConfigForTest([boto_config_for_test]):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file, fpath,
          suri(bucket_uri)
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting upload', stderr)
      stderr = self.RunGsUtil(['cp', fpath, suri(bucket_uri)],
                              return_stderr=True)
      self.assertIn('Resuming upload', stderr)

  @SkipForS3('No compressed transport encoding support for S3.')
  @SkipForXML('No compressed transport encoding support for the XML API.')
  @SequentialAndParallelTransfer
  def test_cp_resumable_upload_gzip_encoded_break(self):
    """Tests that a gzip encoded upload can be resumed."""
    # Setup the bucket and local data. File contents are randomized to prevent
    # them from compressing below the resumable-threshold and failing the test.
    bucket_uri = self.CreateBucket()
    contents = get_random_ascii_chars(size=self.halt_size)
    local_uri = self.CreateTempFile(file_name='test.txt', contents=contents)
    # Configure boto
    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(True, 5)))

    with SetBotoConfigForTest([boto_config_for_test]):
      stderr = self.RunGsUtil([
          '-D', 'cp', '-J', '--testcallbackfile', test_callback_file, local_uri,
          suri(bucket_uri)
      ],
                              expected_status=1,
                              return_stderr=True)
      # Ensure the progress logger sees a gzip encoding.
      self.assertIn('send: Using gzip transport encoding for the request.',
                    stderr)
      self.assertIn('Artifically halting upload', stderr)
      stderr = self.RunGsUtil(['-D', 'cp', '-J', local_uri,
                               suri(bucket_uri)],
                              return_stderr=True)
      self.assertIn('Resuming upload', stderr)
      # Ensure the progress logger is still seeing a gzip encoding.
      self.assertIn('send: Using gzip transport encoding for the request.',
                    stderr)
    # Ensure the files do not have a stored encoding of gzip and are stored
    # uncompressed.
    temp_uri = self.CreateTempFile()
    remote_uri = suri(bucket_uri, 'test.txt')
    stdout = self.RunGsUtil(['stat', remote_uri], return_stdout=True)
    self.assertNotRegex(stdout, r'Content-Encoding:\s+gzip')
    self.RunGsUtil(['cp', remote_uri, suri(temp_uri)])
    with open(temp_uri, 'rb') as f:
      self.assertEqual(f.read(), contents)

  @SkipForS3('No resumable upload support for S3.')
  def test_cp_resumable_upload_retry(self):
    """Tests that a resumable upload completes with one retry."""
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=b'a' * self.halt_size)
    # TODO: Raising an httplib or socket error blocks bucket teardown
    # in JSON for 60-120s on a multiprocessing lock acquire. Figure out why;
    # until then, raise an apitools retryable exception.
    if self.test_api == ApiSelector.XML:
      test_callback_file = self.CreateTempFile(contents=pickle.dumps(
          _ResumableUploadRetryHandler(5, http_client.BadStatusLine, (
              'unused',))))
    else:
      test_callback_file = self.CreateTempFile(contents=pickle.dumps(
          _ResumableUploadRetryHandler(
              5, apitools_exceptions.BadStatusCodeError, ('unused', 'unused',
                                                          'unused'))))
    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    with SetBotoConfigForTest([boto_config_for_test]):
      stderr = self.RunGsUtil([
          '-D', 'cp', '--testcallbackfile', test_callback_file, fpath,
          suri(bucket_uri)
      ],
                              return_stderr=1)
      if self.test_api == ApiSelector.XML:
        self.assertIn('Got retryable failure', stderr)
      else:
        self.assertIn('Retrying', stderr)

  @SkipForS3('No resumable upload support for S3.')
  def test_cp_resumable_streaming_upload_retry(self):
    """Tests that a streaming resumable upload completes with one retry."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip('XML does not support resumable streaming uploads.')
    bucket_uri = self.CreateBucket()

    test_callback_file = self.CreateTempFile(contents=pickle.dumps(
        _ResumableUploadRetryHandler(5, apitools_exceptions.BadStatusCodeError,
                                     ('unused', 'unused', 'unused'))))
    # Need to reduce the JSON chunk size since streaming uploads buffer a
    # full chunk.
    boto_configs_for_test = [('GSUtil', 'json_resumable_chunk_size',
                              str(256 * ONE_KIB)), ('Boto', 'num_retries', '2')]
    with SetBotoConfigForTest(boto_configs_for_test):
      stderr = self.RunGsUtil([
          '-D', 'cp', '--testcallbackfile', test_callback_file, '-',
          suri(bucket_uri, 'foo')
      ],
                              stdin='a' * 512 * ONE_KIB,
                              return_stderr=1)
      self.assertIn('Retrying', stderr)

  @SkipForS3('preserve_acl flag not supported for S3.')
  def test_cp_preserve_no_owner(self):
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
    # Anonymous user can read the object and write to the bucket, but does
    # not own the object.
    self.RunGsUtil(['acl', 'ch', '-u', 'AllUsers:R', suri(object_uri)])
    self.RunGsUtil(['acl', 'ch', '-u', 'AllUsers:W', suri(bucket_uri)])
    with self.SetAnonymousBotoCreds():
      stderr = self.RunGsUtil(
          ['cp', '-p', suri(object_uri),
           suri(bucket_uri, 'foo')],
          return_stderr=True,
          expected_status=1)
      self.assertIn('OWNER permission is required for preserving ACLs', stderr)

  @SkipForS3('No resumable upload support for S3.')
  def test_cp_progress_callbacks(self):
    bucket_uri = self.CreateBucket()
    final_size_string = BytesToFixedWidthString(1024**2)
    final_progress_callback = final_size_string + '/' + final_size_string
    fpath = self.CreateTempFile(contents=b'a' * ONE_MIB, file_name='foo')
    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    with SetBotoConfigForTest([boto_config_for_test]):
      stderr = self.RunGsUtil(['cp', fpath, suri(bucket_uri)],
                              return_stderr=True)
      self.assertEqual(1, stderr.count(final_progress_callback))
    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(2 * ONE_MIB))
    with SetBotoConfigForTest([boto_config_for_test]):
      stderr = self.RunGsUtil(['cp', fpath, suri(bucket_uri)],
                              return_stderr=True)
      self.assertEqual(1, stderr.count(final_progress_callback))
    stderr = self.RunGsUtil(['cp', suri(bucket_uri, 'foo'), fpath],
                            return_stderr=True)
    self.assertEqual(1, stderr.count(final_progress_callback))

  @SkipForS3('No resumable upload support for S3.')
  def test_cp_resumable_upload(self):
    """Tests that a basic resumable upload completes successfully."""
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=b'a' * self.halt_size)
    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    with SetBotoConfigForTest([boto_config_for_test]):
      self.RunGsUtil(['cp', fpath, suri(bucket_uri)])

  @SkipForS3('No resumable upload support for S3.')
  def test_resumable_upload_break_leaves_tracker(self):
    """Tests that a tracker file is created with a resumable upload."""
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(file_name='foo', contents=b'a' * self.halt_size)
    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    with SetBotoConfigForTest([boto_config_for_test]):
      tracker_filename = GetTrackerFilePath(
          StorageUrlFromString(suri(bucket_uri, 'foo')), TrackerFileType.UPLOAD,
          self.test_api)
      test_callback_file = self.CreateTempFile(
          contents=pickle.dumps(HaltingCopyCallbackHandler(True, 5)))
      try:
        stderr = self.RunGsUtil([
            'cp', '--testcallbackfile', test_callback_file, fpath,
            suri(bucket_uri, 'foo')
        ],
                                expected_status=1,
                                return_stderr=True)
        self.assertIn('Artifically halting upload', stderr)
        self.assertTrue(os.path.exists(tracker_filename),
                        'Tracker file %s not present.' % tracker_filename)
        # Test the permissions
        if os.name == 'posix':
          mode = oct(stat.S_IMODE(os.stat(tracker_filename).st_mode))
          # Assert that only user has read/write permission
          self.assertEqual(oct(0o600), mode)
      finally:
        DeleteTrackerFile(tracker_filename)

  @SkipForS3('No resumable upload support for S3.')
  def test_cp_resumable_upload_break_file_size_change(self):
    """Tests a resumable upload where the uploaded file changes size.

    This should fail when we read the tracker data.
    """
    bucket_uri = self.CreateBucket()
    tmp_dir = self.CreateTempDir()
    fpath = self.CreateTempFile(file_name='foo',
                                tmpdir=tmp_dir,
                                contents=b'a' * self.halt_size)
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(True, 5)))

    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    with SetBotoConfigForTest([boto_config_for_test]):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file, fpath,
          suri(bucket_uri)
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting upload', stderr)
      fpath = self.CreateTempFile(file_name='foo',
                                  tmpdir=tmp_dir,
                                  contents=b'a' * self.halt_size * 2)
      stderr = self.RunGsUtil(['cp', fpath, suri(bucket_uri)],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('ResumableUploadAbortException', stderr)

  @SkipForS3('No resumable upload support for S3.')
  def test_cp_resumable_upload_break_file_content_change(self):
    """Tests a resumable upload where the uploaded file changes content."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'XML doesn\'t make separate HTTP calls at fixed-size boundaries for '
          'resumable uploads, so we can\'t guarantee that the server saves a '
          'specific part of the upload.')
    bucket_uri = self.CreateBucket()
    tmp_dir = self.CreateTempDir()
    fpath = self.CreateTempFile(file_name='foo',
                                tmpdir=tmp_dir,
                                contents=b'a' * ONE_KIB * ONE_KIB)
    test_callback_file = self.CreateTempFile(contents=pickle.dumps(
        HaltingCopyCallbackHandler(True,
                                   int(ONE_KIB) * 512)))
    resumable_threshold_for_test = ('GSUtil', 'resumable_threshold',
                                    str(ONE_KIB))
    resumable_chunk_size_for_test = ('GSUtil', 'json_resumable_chunk_size',
                                     str(ONE_KIB * 256))
    with SetBotoConfigForTest(
        [resumable_threshold_for_test, resumable_chunk_size_for_test]):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file, fpath,
          suri(bucket_uri)
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting upload', stderr)
      fpath = self.CreateTempFile(file_name='foo',
                                  tmpdir=tmp_dir,
                                  contents=b'b' * ONE_KIB * ONE_KIB)
      stderr = self.RunGsUtil(['cp', fpath, suri(bucket_uri)],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('doesn\'t match cloud-supplied digest', stderr)

  @SkipForS3('No resumable upload support for S3.')
  def test_cp_resumable_upload_break_file_smaller_size(self):
    """Tests a resumable upload where the uploaded file changes content.

    This should fail hash validation.
    """
    bucket_uri = self.CreateBucket()
    tmp_dir = self.CreateTempDir()
    fpath = self.CreateTempFile(file_name='foo',
                                tmpdir=tmp_dir,
                                contents=b'a' * ONE_KIB * ONE_KIB)
    test_callback_file = self.CreateTempFile(contents=pickle.dumps(
        HaltingCopyCallbackHandler(True,
                                   int(ONE_KIB) * 512)))
    resumable_threshold_for_test = ('GSUtil', 'resumable_threshold',
                                    str(ONE_KIB))
    resumable_chunk_size_for_test = ('GSUtil', 'json_resumable_chunk_size',
                                     str(ONE_KIB * 256))
    with SetBotoConfigForTest(
        [resumable_threshold_for_test, resumable_chunk_size_for_test]):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file, fpath,
          suri(bucket_uri)
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting upload', stderr)
      fpath = self.CreateTempFile(file_name='foo',
                                  tmpdir=tmp_dir,
                                  contents=b'a' * ONE_KIB)
      stderr = self.RunGsUtil(['cp', fpath, suri(bucket_uri)],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('ResumableUploadAbortException', stderr)

  @SkipForS3('No resumable upload support for S3.')
  def test_cp_composite_encrypted_upload_resume(self):
    """Tests that an encrypted composite upload resumes successfully."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    bucket_uri = self.CreateBucket()
    dst_url = StorageUrlFromString(suri(bucket_uri, 'foo'))

    file_contents = b'foobar'
    file_name = 'foobar'
    source_file = self.CreateTempFile(contents=file_contents,
                                      file_name=file_name)
    src_url = StorageUrlFromString(source_file)

    # Simulate an upload that had occurred by writing a tracker file
    # that points to a previously uploaded component.
    tracker_file_name = GetTrackerFilePath(dst_url,
                                           TrackerFileType.PARALLEL_UPLOAD,
                                           self.test_api, src_url)
    tracker_prefix = '123'

    # Create component 0 to be used in the resume; it must match the name
    # that will be generated in copy_helper, so we use the same scheme.
    encoded_name = (PARALLEL_UPLOAD_STATIC_SALT + source_file).encode(UTF8)
    content_md5 = GetMd5()
    content_md5.update(encoded_name)
    digest = content_md5.hexdigest()
    component_object_name = (tracker_prefix + PARALLEL_UPLOAD_TEMP_NAMESPACE +
                             digest + '_0')

    component_size = 3
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name=component_object_name,
                                   contents=file_contents[:component_size],
                                   encryption_key=TEST_ENCRYPTION_KEY1)
    existing_component = ObjectFromTracker(component_object_name,
                                           str(object_uri.generation))
    existing_components = [existing_component]
    enc_key_sha256 = TEST_ENCRYPTION_KEY1_SHA256_B64

    WriteParallelUploadTrackerFile(tracker_file_name,
                                   tracker_prefix,
                                   existing_components,
                                   encryption_key_sha256=enc_key_sha256)

    try:
      # Now "resume" the upload using the original encryption key.
      with SetBotoConfigForTest([
          ('GSUtil', 'parallel_composite_upload_threshold', '1'),
          ('GSUtil', 'parallel_composite_upload_component_size',
           str(component_size)),
          ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY1)
      ]):
        stderr = self.RunGsUtil(
            ['cp', source_file, suri(bucket_uri, 'foo')], return_stderr=True)
        self.assertIn('Found 1 existing temporary components to reuse.', stderr)
        self.assertFalse(
            os.path.exists(tracker_file_name),
            'Tracker file %s should have been deleted.' % tracker_file_name)
        read_contents = self.RunGsUtil(['cat', suri(bucket_uri, 'foo')],
                                       return_stdout=True)
        self.assertEqual(read_contents.encode('ascii'), file_contents)
    finally:
      # Clean up if something went wrong.
      DeleteTrackerFile(tracker_file_name)

  @SkipForS3('No resumable upload support for S3.')
  def test_cp_composite_encrypted_upload_restart(self):
    """Tests that encrypted composite upload restarts given a different key."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    bucket_uri = self.CreateBucket()
    dst_url = StorageUrlFromString(suri(bucket_uri, 'foo'))

    file_contents = b'foobar'
    source_file = self.CreateTempFile(contents=file_contents, file_name='foo')
    src_url = StorageUrlFromString(source_file)

    # Simulate an upload that had occurred by writing a tracker file.
    tracker_file_name = GetTrackerFilePath(dst_url,
                                           TrackerFileType.PARALLEL_UPLOAD,
                                           self.test_api, src_url)
    tracker_prefix = '123'
    existing_component_name = 'foo_1'
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo_1',
                                   contents=b'foo',
                                   encryption_key=TEST_ENCRYPTION_KEY1)
    existing_component = ObjectFromTracker(existing_component_name,
                                           str(object_uri.generation))
    existing_components = [existing_component]
    enc_key_sha256 = TEST_ENCRYPTION_KEY1_SHA256_B64
    WriteParallelUploadTrackerFile(tracker_file_name, tracker_prefix,
                                   existing_components,
                                   enc_key_sha256.decode('ascii'))

    try:
      # Now "resume" the upload using the original encryption key.
      with SetBotoConfigForTest([
          ('GSUtil', 'parallel_composite_upload_threshold', '1'),
          ('GSUtil', 'parallel_composite_upload_component_size', '3'),
          ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY2)
      ]):
        stderr = self.RunGsUtil(
            ['cp', source_file, suri(bucket_uri, 'foo')], return_stderr=True)
        self.assertIn(
            'does not match current encryption key. '
            'Deleting old components and restarting upload', stderr)
        self.assertNotIn('existing temporary components to reuse.', stderr)
        self.assertFalse(
            os.path.exists(tracker_file_name),
            'Tracker file %s should have been deleted.' % tracker_file_name)
        read_contents = self.RunGsUtil(['cat', suri(bucket_uri, 'foo')],
                                       return_stdout=True)
        self.assertEqual(read_contents.encode('ascii'), file_contents)
    finally:
      # Clean up if something went wrong.
      DeleteTrackerFile(tracker_file_name)

  @SkipForS3('Test uses gs-specific KMS encryption')
  def test_kms_key_correctly_applied_to_composite_upload(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=b'abcd')
    obj_suri = suri(bucket_uri, 'composed')
    key_fqn = AuthorizeProjectToUseTestingKmsKey()

    with SetBotoConfigForTest([
        ('GSUtil', 'encryption_key', key_fqn),
        ('GSUtil', 'parallel_composite_upload_threshold', '1'),
        ('GSUtil', 'parallel_composite_upload_component_size', '1')
    ]):
      self.RunGsUtil(['cp', fpath, obj_suri])

    with SetBotoConfigForTest([('GSUtil', 'prefer_api', 'json')]):
      self.AssertObjectUsesCMEK(obj_suri, key_fqn)

  @SkipForS3('No composite upload support for S3.')
  def test_nearline_applied_to_parallel_composite_upload(self):
    bucket_uri = self.CreateBucket(storage_class='standard')
    fpath = self.CreateTempFile(contents=b'abcd')
    obj_suri = suri(bucket_uri, 'composed')

    with SetBotoConfigForTest([
        ('GSUtil', 'parallel_composite_upload_threshold', '1'),
        ('GSUtil', 'parallel_composite_upload_component_size', '1')
    ]):
      self.RunGsUtil(['cp', '-s', 'nearline', fpath, obj_suri])
    stdout = self.RunGsUtil(['ls', '-L', obj_suri], return_stdout=True)
    if self._use_gcloud_storage:
      self.assertRegexpMatchesWithFlags(
          stdout, r'Storage class:               NEARLINE', flags=re.IGNORECASE)
    else:
      self.assertRegexpMatchesWithFlags(stdout,
                                        r'Storage class:          NEARLINE',
                                        flags=re.IGNORECASE)

  # This temporarily changes the tracker directory to unwritable which
  # interferes with any parallel running tests that use the tracker directory.
  @NotParallelizable
  @SkipForS3('No resumable upload support for S3.')
  @unittest.skipIf(IS_WINDOWS, 'chmod on dir unsupported on Windows.')
  @SequentialAndParallelTransfer
  def test_cp_unwritable_tracker_file(self):
    """Tests a resumable upload with an unwritable tracker file."""
    bucket_uri = self.CreateBucket()
    tracker_filename = GetTrackerFilePath(
        StorageUrlFromString(suri(bucket_uri, 'foo')), TrackerFileType.UPLOAD,
        self.test_api)
    tracker_dir = os.path.dirname(tracker_filename)
    fpath = self.CreateTempFile(file_name='foo', contents=b'a' * ONE_KIB)
    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    save_mod = os.stat(tracker_dir).st_mode

    try:
      os.chmod(tracker_dir, 0)
      with SetBotoConfigForTest([boto_config_for_test]):
        stderr = self.RunGsUtil(['cp', fpath, suri(bucket_uri)],
                                expected_status=1,
                                return_stderr=True)
        self.assertIn('Couldn\'t write tracker file', stderr)
    finally:
      os.chmod(tracker_dir, save_mod)
      if os.path.exists(tracker_filename):
        os.unlink(tracker_filename)

  # This temporarily changes the tracker directory to unwritable which
  # interferes with any parallel running tests that use the tracker directory.
  @NotParallelizable
  @unittest.skipIf(IS_WINDOWS, 'chmod on dir unsupported on Windows.')
  @SequentialAndParallelTransfer
  def test_cp_unwritable_tracker_file_download(self):
    """Tests downloads with an unwritable tracker file."""
    object_uri = self.CreateObject(contents=b'foo' * ONE_KIB)
    tracker_filename = GetTrackerFilePath(
        StorageUrlFromString(suri(object_uri)), TrackerFileType.DOWNLOAD,
        self.test_api)
    tracker_dir = os.path.dirname(tracker_filename)
    fpath = self.CreateTempFile()
    save_mod = os.stat(tracker_dir).st_mode

    try:
      os.chmod(tracker_dir, 0)
      boto_config_for_test = ('GSUtil', 'resumable_threshold', str(EIGHT_MIB))
      with SetBotoConfigForTest([boto_config_for_test]):
        # Should succeed because we are below the threshold.
        self.RunGsUtil(['cp', suri(object_uri), fpath])
      boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
      with SetBotoConfigForTest([boto_config_for_test]):
        stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                                expected_status=1,
                                return_stderr=True)
        self.assertIn('Couldn\'t write tracker file', stderr)
    finally:
      os.chmod(tracker_dir, save_mod)
      if os.path.exists(tracker_filename):
        os.unlink(tracker_filename)

  def _test_cp_resumable_download_break_helper(self,
                                               boto_config,
                                               encryption_key=None):
    """Helper function for different modes of resumable download break.

    Args:
      boto_config: List of boto configuration tuples for use with
          SetBotoConfigForTest.
      encryption_key: Base64 encryption key for object encryption (if any).
    """
    bucket_uri = self.CreateBucket()
    file_contents = b'a' * self.halt_size
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=file_contents,
                                   encryption_key=encryption_key)
    fpath = self.CreateTempFile()
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))

    with SetBotoConfigForTest(boto_config):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri), fpath
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting download.', stderr)
      tracker_filename = GetTrackerFilePath(StorageUrlFromString(fpath),
                                            TrackerFileType.DOWNLOAD,
                                            self.test_api)
      self.assertTrue(os.path.isfile(tracker_filename))
      stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                              return_stderr=True)
      self.assertIn('Resuming download', stderr)
    with open(fpath, 'rb') as f:
      self.assertEqual(f.read(), file_contents, 'File contents differ')

  def test_cp_resumable_download_break(self):
    """Tests that a download can be resumed after a connection break."""
    self._test_cp_resumable_download_break_helper([
        ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    ])

  @SkipForS3('gsutil doesn\'t support S3 customer-supplied encryption keys.')
  def test_cp_resumable_encrypted_download_break(self):
    """Tests that an encrypted download resumes after a connection break."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    self._test_cp_resumable_download_break_helper(
        [('GSUtil', 'resumable_threshold', str(ONE_KIB)),
         ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY1)],
        encryption_key=TEST_ENCRYPTION_KEY1)

  @SkipForS3('gsutil doesn\'t support S3 customer-supplied encryption keys.')
  def test_cp_resumable_encrypted_download_key_rotation(self):
    """Tests that a download restarts with a rotated encryption key."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip(
          'gsutil does not support encryption with the XML API')
    bucket_uri = self.CreateBucket()
    file_contents = b'a' * self.halt_size
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=file_contents,
                                   encryption_key=TEST_ENCRYPTION_KEY1)
    fpath = self.CreateTempFile()
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))

    boto_config_for_test = [('GSUtil', 'resumable_threshold', str(ONE_KIB)),
                            ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY1)]

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri), fpath
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting download.', stderr)
      tracker_filename = GetTrackerFilePath(StorageUrlFromString(fpath),
                                            TrackerFileType.DOWNLOAD,
                                            self.test_api)
      self.assertTrue(os.path.isfile(tracker_filename))

    # After simulated connection break, rotate the key on the object.
    boto_config_for_test2 = [('GSUtil', 'resumable_threshold', str(ONE_KIB)),
                             ('GSUtil', 'decryption_key1',
                              TEST_ENCRYPTION_KEY1),
                             ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY2)]
    with SetBotoConfigForTest(boto_config_for_test2):
      self.RunGsUtil(['rewrite', '-k', suri(object_uri)])

    # Now resume the download using only the new encryption key. Since its
    # generation changed, we must restart it.
    boto_config_for_test3 = [('GSUtil', 'resumable_threshold', str(ONE_KIB)),
                             ('GSUtil', 'encryption_key', TEST_ENCRYPTION_KEY2)]
    with SetBotoConfigForTest(boto_config_for_test3):
      stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                              return_stderr=True)
      self.assertIn('Restarting download', stderr)
    with open(fpath, 'rb') as f:
      self.assertEqual(f.read(), file_contents, 'File contents differ')

  @SequentialAndParallelTransfer
  def test_cp_resumable_download_etag_differs(self):
    """Tests that download restarts the file when the source object changes.

    This causes the etag not to match.
    """
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'abc' * self.halt_size)
    fpath = self.CreateTempFile()
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))
    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    with SetBotoConfigForTest([boto_config_for_test]):
      # This will create a tracker file with an ETag.
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri), fpath
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting download.', stderr)
      # Create a new object with different contents - it should have a
      # different ETag since the content has changed.
      object_uri = self.CreateObject(
          bucket_uri=bucket_uri,
          object_name='foo',
          contents=b'b' * self.halt_size,
          gs_idempotent_generation=object_uri.generation)
      stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                              return_stderr=True)
      self.assertNotIn('Resuming download', stderr)

  # TODO: Enable this test for sequential downloads when their tracker files are
  # modified to contain the source object generation.
  @unittest.skipUnless(UsingCrcmodExtension(),
                       'Sliced download requires fast crcmod.')
  @SkipForS3('No sliced download support for S3.')
  def test_cp_resumable_download_generation_differs(self):
    """Tests that a resumable download restarts if the generation differs."""
    bucket_uri = self.CreateBucket()
    file_contents = b'abcd' * self.halt_size
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=file_contents)
    fpath = self.CreateTempFile()

    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))

    boto_config_for_test = [
        ('GSUtil', 'resumable_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_max_components', '3')
    ]

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri),
          suri(fpath)
      ],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('Artifically halting download.', stderr)

      # Overwrite the object with an identical object, increasing
      # the generation but leaving other metadata the same.
      identical_file = self.CreateTempFile(contents=file_contents)
      self.RunGsUtil(['cp', suri(identical_file), suri(object_uri)])

      stderr = self.RunGsUtil(
          ['cp', suri(object_uri), suri(fpath)], return_stderr=True)
      self.assertIn('Restarting download from scratch', stderr)
      with open(fpath, 'rb') as f:
        self.assertEqual(f.read(), file_contents, 'File contents differ')

  def test_cp_resumable_download_file_larger(self):
    """Tests download deletes the tracker file when existing file is larger."""
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'a' * self.halt_size)
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))
    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    with SetBotoConfigForTest([boto_config_for_test]):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri), fpath
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting download.', stderr)
      with open(fpath + '_.gstmp', 'w') as larger_file:
        for _ in range(self.halt_size * 2):
          larger_file.write('a')
      stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                              expected_status=1,
                              return_stderr=True)
      self.assertNotIn('Resuming download', stderr)
      self.assertIn('Deleting tracker file', stderr)

  def test_cp_resumable_download_content_differs(self):
    """Tests that we do not re-download when tracker file matches existing file.

    We only compare size, not contents, so re-download should not occur even
    though the contents are technically different. However, hash validation on
    the file should still occur and we will delete the file then because
    the hashes differ.
    """
    bucket_uri = self.CreateBucket()
    tmp_dir = self.CreateTempDir()
    fpath = self.CreateTempFile(tmpdir=tmp_dir)
    temp_download_file = fpath + '_.gstmp'
    with open(temp_download_file, 'w') as fp:
      fp.write('abcd' * ONE_KIB)

    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'efgh' * ONE_KIB)
    stdout = self.RunGsUtil(['ls', '-L', suri(object_uri)], return_stdout=True)
    etag_match = re.search(r'\s*ETag:\s*(.*)', stdout)
    self.assertIsNotNone(etag_match, 'Could not get object ETag')
    self.assertEqual(len(etag_match.groups()), 1,
                     'Did not match expected single ETag')
    etag = etag_match.group(1)

    tracker_filename = GetTrackerFilePath(StorageUrlFromString(fpath),
                                          TrackerFileType.DOWNLOAD,
                                          self.test_api)
    try:
      with open(tracker_filename, 'w') as tracker_fp:
        tracker_fp.write(etag)
      boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
      with SetBotoConfigForTest([boto_config_for_test]):
        stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                                return_stderr=True,
                                expected_status=1)
        self.assertIn('Download already complete', stderr)
        self.assertIn('doesn\'t match cloud-supplied digest', stderr)
        # File and tracker file should be deleted.
        self.assertFalse(os.path.isfile(temp_download_file))
        self.assertFalse(os.path.isfile(tracker_filename))
        # Permanent file should not have been created.
        self.assertFalse(os.path.isfile(fpath))
    finally:
      if os.path.exists(tracker_filename):
        os.unlink(tracker_filename)

  def test_cp_resumable_download_content_matches(self):
    """Tests download no-ops when tracker file matches existing file."""
    bucket_uri = self.CreateBucket()
    tmp_dir = self.CreateTempDir()
    fpath = self.CreateTempFile(tmpdir=tmp_dir)
    matching_contents = b'abcd' * ONE_KIB
    temp_download_file = fpath + '_.gstmp'
    with open(temp_download_file, 'wb') as fp:
      fp.write(matching_contents)

    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=matching_contents)
    stdout = self.RunGsUtil(['ls', '-L', suri(object_uri)], return_stdout=True)
    etag_match = re.search(r'\s*ETag:\s*(.*)', stdout)
    self.assertIsNotNone(etag_match, 'Could not get object ETag')
    self.assertEqual(len(etag_match.groups()), 1,
                     'Did not match expected single ETag')
    etag = etag_match.group(1)
    tracker_filename = GetTrackerFilePath(StorageUrlFromString(fpath),
                                          TrackerFileType.DOWNLOAD,
                                          self.test_api)
    with open(tracker_filename, 'w') as tracker_fp:
      tracker_fp.write(etag)
    try:
      boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
      with SetBotoConfigForTest([boto_config_for_test]):
        stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                                return_stderr=True)
        self.assertIn('Download already complete', stderr)
        # Tracker file should be removed after successful hash validation.
        self.assertFalse(os.path.isfile(tracker_filename))
    finally:
      if os.path.exists(tracker_filename):
        os.unlink(tracker_filename)

  def test_cp_resumable_download_tracker_file_not_matches(self):
    """Tests that download overwrites when tracker file etag does not match."""
    bucket_uri = self.CreateBucket()
    tmp_dir = self.CreateTempDir()
    fpath = self.CreateTempFile(tmpdir=tmp_dir, contents=b'abcd' * ONE_KIB)
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'efgh' * ONE_KIB)
    stdout = self.RunGsUtil(['ls', '-L', suri(object_uri)], return_stdout=True)
    etag_match = re.search(r'\s*ETag:\s*(.*)', stdout)
    self.assertIsNotNone(etag_match, 'Could not get object ETag')
    self.assertEqual(len(etag_match.groups()), 1,
                     'Did not match regex for exactly one object ETag')
    etag = etag_match.group(1)
    etag += 'nonmatching'
    tracker_filename = GetTrackerFilePath(StorageUrlFromString(fpath),
                                          TrackerFileType.DOWNLOAD,
                                          self.test_api)
    with open(tracker_filename, 'w') as tracker_fp:
      tracker_fp.write(etag)
    try:
      boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
      with SetBotoConfigForTest([boto_config_for_test]):
        stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                                return_stderr=True)
        self.assertNotIn('Resuming download', stderr)
        # Ensure the file was overwritten.
        with open(fpath, 'r') as in_fp:
          contents = in_fp.read()
          self.assertEqual(
              contents, 'efgh' * ONE_KIB,
              'File not overwritten when it should have been '
              'due to a non-matching tracker file.')
        self.assertFalse(os.path.isfile(tracker_filename))
    finally:
      if os.path.exists(tracker_filename):
        os.unlink(tracker_filename)

  def test_cp_double_gzip(self):
    """Tests that upload and download of a doubly-gzipped file succeeds."""
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(file_name='looks-zipped.gz', contents=b'foo')
    self.RunGsUtil([
        '-h', 'content-type:application/gzip', 'cp', '-Z',
        suri(fpath),
        suri(bucket_uri, 'foo')
    ])
    self.RunGsUtil(['cp', suri(bucket_uri, 'foo'), fpath])

  @SkipForS3('No compressed transport encoding support for S3.')
  @SkipForXML('No compressed transport encoding support for the XML API.')
  @SequentialAndParallelTransfer
  def test_cp_double_gzip_transport_encoded(self):
    """Tests that upload and download of a doubly-gzipped file succeeds."""
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(file_name='looks-zipped.gz', contents=b'foo')
    stderr = self.RunGsUtil([
        '-DD', '-h', 'content-type:application/gzip', 'cp', '-J',
        suri(fpath),
        suri(bucket_uri, 'foo')
    ],
                            return_stderr=True)
    if self._use_gcloud_storage:
      self.assertIn("b\'Content-Encoding\': b\'gzip\'", stderr)
      self.assertIn('"contentType": "application/gzip"', stderr)
    else:
      self.assertIn("\'Content-Encoding\': \'gzip\'", stderr)
      self.assertIn('contentType: \'application/gzip\'', stderr)
    self.RunGsUtil(['cp', suri(bucket_uri, 'foo'), fpath])

  @unittest.skipIf(IS_WINDOWS, 'TODO(b/293885158) Timeout on Windows.')
  @SequentialAndParallelTransfer
  def test_cp_resumable_download_gzip(self):
    """Tests that download can be resumed successfully with a gzipped file."""
    # Generate some reasonably incompressible data.  This compresses to a bit
    # around 128K in practice, but we assert specifically below that it is
    # larger than self.halt_size to guarantee that we can halt the download
    # partway through.
    object_uri = self.CreateObject()
    random.seed(0)
    contents = str([
        random.choice(string.ascii_letters) for _ in xrange(self.halt_size)
    ]).encode('ascii')
    random.seed()  # Reset the seed for any other tests.
    fpath1 = self.CreateTempFile(file_name='unzipped.txt', contents=contents)
    self.RunGsUtil(['cp', '-z', 'txt', suri(fpath1), suri(object_uri)])

    # Use @Retry as hedge against bucket listing eventual consistency.
    @Retry(AssertionError, tries=3, timeout_secs=1)
    def _GetObjectSize():
      stdout = self.RunGsUtil(['du', suri(object_uri)], return_stdout=True)
      size_match = re.search(r'(\d+)\s+.*', stdout)
      self.assertIsNotNone(size_match, 'Could not get object size')
      self.assertEqual(len(size_match.groups()), 1,
                       'Did not match regex for exactly one object size.')
      return long(size_match.group(1))

    object_size = _GetObjectSize()
    self.assertGreaterEqual(
        object_size, self.halt_size,
        'Compresed object size was not large enough to '
        'allow for a halted download, so the test results '
        'would be invalid. Please increase the compressed '
        'object size in the test.')
    fpath2 = self.CreateTempFile()
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))

    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    with SetBotoConfigForTest([boto_config_for_test]):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri),
          suri(fpath2)
      ],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('Artifically halting download.', stderr)
      self.assertIn('Downloading to temp gzip filename', stderr)

      # Tracker files will have different names depending on if we are
      # downloading sequentially or in parallel.
      sliced_download_threshold = HumanReadableToBytes(
          boto.config.get('GSUtil', 'sliced_object_download_threshold',
                          DEFAULT_SLICED_OBJECT_DOWNLOAD_THRESHOLD))
      sliced_download = (len(contents) > sliced_download_threshold and
                         sliced_download_threshold > 0 and
                         UsingCrcmodExtension())
      if sliced_download:
        trackerfile_type = TrackerFileType.SLICED_DOWNLOAD
      else:
        trackerfile_type = TrackerFileType.DOWNLOAD
      tracker_filename = GetTrackerFilePath(StorageUrlFromString(fpath2),
                                            trackerfile_type, self.test_api)

      # We should have a temporary gzipped file, a tracker file, and no
      # final file yet.
      self.assertTrue(os.path.isfile(tracker_filename))
      self.assertTrue(os.path.isfile('%s_.gztmp' % fpath2))
      stderr = self.RunGsUtil(
          ['cp', suri(object_uri), suri(fpath2)], return_stderr=True)
      self.assertIn('Resuming download', stderr)
      with open(fpath2, 'rb') as f:
        self.assertEqual(f.read(), contents, 'File contents did not match.')
      self.assertFalse(os.path.isfile(tracker_filename))
      self.assertFalse(os.path.isfile('%s_.gztmp' % fpath2))

  def _GetFaviconFile(self):
    # Make a temp file from favicon.ico.gz. Finding the location of our test
    # data varies depending on how/where gsutil was installed, so we get the
    # data via pkgutil and use this workaround.
    if not hasattr(self, 'test_data_favicon_file'):
      contents = pkgutil.get_data('gslib', 'tests/test_data/favicon.ico.gz')
      self.test_data_favicon_file = self.CreateTempFile(contents=contents)
    return self.test_data_favicon_file

  def test_cp_download_transfer_encoded(self):
    """Tests chunked transfer encoded download handling.

    Tests that download works correctly with a gzipped chunked transfer-encoded
    object (which therefore lacks Content-Length) of a size that gets fetched
    in a single chunk (exercising downloading of objects lacking a length
    response header).
    """
    # Upload a file / content-encoding / content-type that triggers this flow.
    # Note: We need to use the file with pre-zipped format and manually set the
    # content-encoding and content-type because the Python gzip module (used by
    # gsutil cp -Z) won't reproduce the bytes that trigger this problem.
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri, object_name='foo')
    input_filename = self._GetFaviconFile()
    self.RunGsUtil([
        '-h', 'Content-Encoding:gzip', '-h', 'Content-Type:image/x-icon', 'cp',
        suri(input_filename),
        suri(object_uri)
    ])
    # Compute the MD5 of the uncompressed bytes.
    with gzip.open(input_filename) as fp:
      hash_dict = {'md5': GetMd5()}
      hashing_helper.CalculateHashesFromContents(fp, hash_dict)
      in_file_md5 = hash_dict['md5'].digest()

    # Downloading this file triggers the flow.
    fpath2 = self.CreateTempFile()
    self.RunGsUtil(['cp', suri(object_uri), suri(fpath2)])
    # Compute MD5 of the downloaded (uncompressed) file, and validate it.
    with open(fpath2, 'rb') as fp:
      hash_dict = {'md5': GetMd5()}
      hashing_helper.CalculateHashesFromContents(fp, hash_dict)
      out_file_md5 = hash_dict['md5'].digest()
    self.assertEqual(in_file_md5, out_file_md5)

  @SequentialAndParallelTransfer
  def test_cp_resumable_download_check_hashes_never(self):
    """Tests that resumble downloads work with check_hashes = never."""
    bucket_uri = self.CreateBucket()
    contents = b'abcd' * self.halt_size
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=contents)
    fpath = self.CreateTempFile()
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))

    boto_config_for_test = [('GSUtil', 'resumable_threshold', str(ONE_KIB)),
                            ('GSUtil', 'check_hashes', 'never')]
    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri), fpath
      ],
                              expected_status=1,
                              return_stderr=True)
      self.assertIn('Artifically halting download.', stderr)
      stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                              return_stderr=True)
      self.assertIn('Resuming download', stderr)
      self.assertIn('Found no hashes to validate object downloaded', stderr)
      with open(fpath, 'rb') as f:
        self.assertEqual(f.read(), contents, 'File contents did not match.')

  @SkipForS3('No resumable upload support for S3.')
  def test_cp_resumable_upload_bucket_deleted(self):
    """Tests that a not found exception is raised if bucket no longer exists."""
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=b'a' * 2 * ONE_KIB)
    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    test_callback_file = self.CreateTempFile(contents=pickle.dumps(
        _DeleteBucketThenStartOverCopyCallbackHandler(5, bucket_uri)))

    with SetBotoConfigForTest([boto_config_for_test]):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file, fpath,
          suri(bucket_uri)
      ],
                              return_stderr=True,
                              expected_status=1)
    self.assertIn('Deleting bucket', stderr)
    self.assertIn('bucket does not exist', stderr)

  @SkipForS3('No sliced download support for S3.')
  def test_cp_sliced_download(self):
    """Tests that sliced object download works in the general case."""
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'abc' * ONE_KIB)
    fpath = self.CreateTempFile()

    # Force fast crcmod to return True to test the basic sliced download
    # scenario, ensuring that if the user installs crcmod, it will work.
    boto_config_for_test = [
        ('GSUtil', 'resumable_threshold', str(ONE_KIB)),
        ('GSUtil', 'test_assume_fast_crcmod', 'True'),
        ('GSUtil', 'sliced_object_download_threshold', str(ONE_KIB)),
        ('GSUtil', 'sliced_object_download_max_components', '3')
    ]

    with SetBotoConfigForTest(boto_config_for_test):
      self.RunGsUtil(['cp', suri(object_uri), fpath])

      # Each tracker file should have been deleted.
      tracker_filenames = GetSlicedDownloadTrackerFilePaths(
          StorageUrlFromString(fpath), self.test_api)
      for tracker_filename in tracker_filenames:
        self.assertFalse(os.path.isfile(tracker_filename))

      with open(fpath, 'rb') as f:
        self.assertEqual(f.read(), b'abc' * ONE_KIB, 'File contents differ')

  @unittest.skipUnless(UsingCrcmodExtension(),
                       'Sliced download requires fast crcmod.')
  @SkipForS3('No sliced download support for S3.')
  def test_cp_unresumable_sliced_download(self):
    """Tests sliced download works when resumability is disabled."""
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'abcd' * self.halt_size)
    fpath = self.CreateTempFile()
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))

    boto_config_for_test = [
        ('GSUtil', 'resumable_threshold', str(self.halt_size * 5)),
        ('GSUtil', 'sliced_object_download_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_max_components', '4')
    ]

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri),
          suri(fpath)
      ],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('not downloaded successfully', stderr)
      # Temporary download file should exist.
      self.assertTrue(os.path.isfile(fpath + '_.gstmp'))

      # No tracker files should exist.
      tracker_filenames = GetSlicedDownloadTrackerFilePaths(
          StorageUrlFromString(fpath), self.test_api)
      for tracker_filename in tracker_filenames:
        self.assertFalse(os.path.isfile(tracker_filename))

    # Perform the entire download, without resuming.
    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil(
          ['cp', suri(object_uri), suri(fpath)], return_stderr=True)
      self.assertNotIn('Resuming download', stderr)
      # Temporary download file should have been deleted.
      self.assertFalse(os.path.isfile(fpath + '_.gstmp'))
      with open(fpath, 'rb') as f:
        self.assertEqual(f.read(), b'abcd' * self.halt_size,
                         'File contents differ')

  @unittest.skipUnless(UsingCrcmodExtension(),
                       'Sliced download requires fast crcmod.')
  @SkipForS3('No sliced download support for S3.')
  def test_cp_sliced_download_resume(self):
    """Tests that sliced object download is resumable."""
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'abc' * self.halt_size)
    fpath = self.CreateTempFile()
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))

    boto_config_for_test = [
        ('GSUtil', 'resumable_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_max_components', '3')
    ]

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri),
          suri(fpath)
      ],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('not downloaded successfully', stderr)

      # Each tracker file should exist.
      tracker_filenames = GetSlicedDownloadTrackerFilePaths(
          StorageUrlFromString(fpath), self.test_api)
      for tracker_filename in tracker_filenames:
        self.assertTrue(os.path.isfile(tracker_filename))

      stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                              return_stderr=True)
      self.assertIn('Resuming download', stderr)

      # Each tracker file should have been deleted.
      tracker_filenames = GetSlicedDownloadTrackerFilePaths(
          StorageUrlFromString(fpath), self.test_api)
      for tracker_filename in tracker_filenames:
        self.assertFalse(os.path.isfile(tracker_filename))

      with open(fpath, 'rb') as f:
        self.assertEqual(f.read(), b'abc' * self.halt_size,
                         'File contents differ')

  @unittest.skipUnless(UsingCrcmodExtension(),
                       'Sliced download requires fast crcmod.')
  @SkipForS3('No sliced download support for S3.')
  def test_cp_sliced_download_partial_resume(self):
    """Test sliced download resumability when some components are finished."""
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'abc' * self.halt_size)
    fpath = self.CreateTempFile()
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltOneComponentCopyCallbackHandler(5)))

    boto_config_for_test = [
        ('GSUtil', 'resumable_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_max_components', '3')
    ]

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri),
          suri(fpath)
      ],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('not downloaded successfully', stderr)

      # Each tracker file should exist.
      tracker_filenames = GetSlicedDownloadTrackerFilePaths(
          StorageUrlFromString(fpath), self.test_api)
      for tracker_filename in tracker_filenames:
        self.assertTrue(os.path.isfile(tracker_filename))

      stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                              return_stderr=True)
      self.assertIn('Resuming download', stderr)
      self.assertIn('Download already complete', stderr)

      # Each tracker file should have been deleted.
      tracker_filenames = GetSlicedDownloadTrackerFilePaths(
          StorageUrlFromString(fpath), self.test_api)
      for tracker_filename in tracker_filenames:
        self.assertFalse(os.path.isfile(tracker_filename))

      with open(fpath, 'rb') as f:
        self.assertEqual(f.read(), b'abc' * self.halt_size,
                         'File contents differ')

  @unittest.skipUnless(UsingCrcmodExtension(),
                       'Sliced download requires fast crcmod.')
  @SkipForS3('No sliced download support for S3.')
  def test_cp_sliced_download_resume_content_differs(self):
    """Tests differing file contents are detected by sliced downloads."""
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'abc' * self.halt_size)
    fpath = self.CreateTempFile(contents=b'')
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))

    boto_config_for_test = [
        ('GSUtil', 'resumable_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_max_components', '3')
    ]

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri),
          suri(fpath)
      ],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('not downloaded successfully', stderr)

      # Temporary download file should exist.
      self.assertTrue(os.path.isfile(fpath + '_.gstmp'))

      # Each tracker file should exist.
      tracker_filenames = GetSlicedDownloadTrackerFilePaths(
          StorageUrlFromString(fpath), self.test_api)
      for tracker_filename in tracker_filenames:
        self.assertTrue(os.path.isfile(tracker_filename))

      with open(fpath + '_.gstmp', 'r+b') as f:
        f.write(b'altered file contents')

      stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('Resuming download', stderr)
      self.assertIn('doesn\'t match cloud-supplied digest', stderr)
      self.assertIn('HashMismatchException: crc32c', stderr)

      # Each tracker file should have been deleted.
      tracker_filenames = GetSlicedDownloadTrackerFilePaths(
          StorageUrlFromString(fpath), self.test_api)
      for tracker_filename in tracker_filenames:
        self.assertFalse(os.path.isfile(tracker_filename))

      # Temporary file should have been deleted due to hash mismatch.
      self.assertFalse(os.path.isfile(fpath + '_.gstmp'))
      # Final file should not exist.
      self.assertFalse(os.path.isfile(fpath))

  @unittest.skipUnless(UsingCrcmodExtension(),
                       'Sliced download requires fast crcmod.')
  @SkipForS3('No sliced download support for S3.')
  def test_cp_sliced_download_component_size_changed(self):
    """Tests sliced download doesn't break when the boto config changes.

    If the number of components used changes cross-process, the download should
    be restarted.
    """
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'abcd' * self.halt_size)
    fpath = self.CreateTempFile()
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))

    boto_config_for_test = [
        ('GSUtil', 'resumable_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_component_size',
         str(self.halt_size // 4)),
        ('GSUtil', 'sliced_object_download_max_components', '4')
    ]

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri),
          suri(fpath)
      ],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('not downloaded successfully', stderr)

    boto_config_for_test = [
        ('GSUtil', 'resumable_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_component_size',
         str(self.halt_size // 2)),
        ('GSUtil', 'sliced_object_download_max_components', '2')
    ]

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                              return_stderr=True)
      self.assertIn('Sliced download tracker file doesn\'t match ', stderr)
      self.assertIn('Restarting download from scratch', stderr)
      self.assertNotIn('Resuming download', stderr)

  @unittest.skipUnless(UsingCrcmodExtension(),
                       'Sliced download requires fast crcmod.')
  @SkipForS3('No sliced download support for S3.')
  def test_cp_sliced_download_disabled_cross_process(self):
    """Tests temporary files are not orphaned if sliced download is disabled.

    Specifically, temporary files should be deleted when the corresponding
    non-sliced download is completed.
    """
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'abcd' * self.halt_size)
    fpath = self.CreateTempFile()
    test_callback_file = self.CreateTempFile(
        contents=pickle.dumps(HaltingCopyCallbackHandler(False, 5)))

    boto_config_for_test = [
        ('GSUtil', 'resumable_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_max_components', '4')
    ]

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file,
          suri(object_uri),
          suri(fpath)
      ],
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('not downloaded successfully', stderr)
      # Temporary download file should exist.
      self.assertTrue(os.path.isfile(fpath + '_.gstmp'))

      # Each tracker file should exist.
      tracker_filenames = GetSlicedDownloadTrackerFilePaths(
          StorageUrlFromString(fpath), self.test_api)
      for tracker_filename in tracker_filenames:
        self.assertTrue(os.path.isfile(tracker_filename))

    # Disable sliced downloads by increasing the threshold
    boto_config_for_test = [
        ('GSUtil', 'resumable_threshold', str(self.halt_size)),
        ('GSUtil', 'sliced_object_download_threshold', str(self.halt_size * 5)),
        ('GSUtil', 'sliced_object_download_max_components', '4')
    ]

    with SetBotoConfigForTest(boto_config_for_test):
      stderr = self.RunGsUtil(['cp', suri(object_uri), fpath],
                              return_stderr=True)
      self.assertNotIn('Resuming download', stderr)
      # Temporary download file should have been deleted.
      self.assertFalse(os.path.isfile(fpath + '_.gstmp'))

      # Each tracker file should have been deleted.
      for tracker_filename in tracker_filenames:
        self.assertFalse(os.path.isfile(tracker_filename))
      with open(fpath, 'rb') as f:
        self.assertEqual(f.read(), b'abcd' * self.halt_size)

  @SkipForS3('No resumable upload support for S3.')
  def test_cp_resumable_upload_start_over_http_error(self):
    for start_over_error in (
        403,  # If user doesn't have storage.buckets.get access to dest bucket.
        404,  # If the dest bucket exists, but the dest object does not.
        410):  # If the service tells us to restart the upload from scratch.
      self.start_over_error_test_helper(start_over_error)

  def start_over_error_test_helper(self, http_error_num):
    bucket_uri = self.CreateBucket()
    # The object contents need to be fairly large to avoid the race condition
    # where the contents finish uploading before we artifically halt the copy.
    rand_chars = get_random_ascii_chars(size=(ONE_MIB * 4))
    fpath = self.CreateTempFile(contents=rand_chars)
    boto_config_for_test = ('GSUtil', 'resumable_threshold', str(ONE_KIB))
    if self.test_api == ApiSelector.JSON:
      test_callback_file = self.CreateTempFile(
          contents=pickle.dumps(_JSONForceHTTPErrorCopyCallbackHandler(5, 404)))
    elif self.test_api == ApiSelector.XML:
      test_callback_file = self.CreateTempFile(contents=pickle.dumps(
          _XMLResumableUploadStartOverCopyCallbackHandler(5)))

    with SetBotoConfigForTest([boto_config_for_test]):
      stderr = self.RunGsUtil([
          'cp', '--testcallbackfile', test_callback_file, fpath,
          suri(bucket_uri)
      ],
                              return_stderr=True)
      self.assertIn('Restarting upload of', stderr)

  def test_cp_minus_c(self):
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'foo')

    cp_command = [
        'cp',
        '-c',
        suri(bucket_uri) + '/foo2',
        suri(object_uri),
        suri(bucket_uri) + '/dir/',
    ]
    self.RunGsUtil(cp_command, expected_status=1)
    self.RunGsUtil(['stat', '%s/dir/foo' % suri(bucket_uri)])

  def test_rewrite_cp(self):
    """Tests the JSON Rewrite API."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip('Rewrite API is only supported in JSON.')
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'bar')
    gsutil_api = GcsJsonApi(BucketStorageUri, logging.getLogger(),
                            DiscardMessagesQueue(), self.default_provider)
    key = object_uri.get_key()
    src_obj_metadata = apitools_messages.Object(name=key.name,
                                                bucket=key.bucket.name,
                                                contentType=key.content_type)
    dst_obj_metadata = apitools_messages.Object(
        bucket=src_obj_metadata.bucket,
        name=self.MakeTempName('object'),
        contentType=src_obj_metadata.contentType)
    gsutil_api.CopyObject(src_obj_metadata, dst_obj_metadata)
    self.assertEqual(
        gsutil_api.GetObjectMetadata(src_obj_metadata.bucket,
                                     src_obj_metadata.name,
                                     fields=['customerEncryption',
                                             'md5Hash']).md5Hash,
        gsutil_api.GetObjectMetadata(dst_obj_metadata.bucket,
                                     dst_obj_metadata.name,
                                     fields=['customerEncryption',
                                             'md5Hash']).md5Hash,
        'Error: Rewritten object\'s hash doesn\'t match source object.')

  def test_rewrite_cp_resume(self):
    """Tests the JSON Rewrite API, breaking and resuming via a tracker file."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip('Rewrite API is only supported in JSON.')
    bucket_uri = self.CreateBucket()
    # Second bucket needs to be a different storage class so the service
    # actually rewrites the bytes.
    bucket_uri2 = self.CreateBucket(
        storage_class='durable_reduced_availability')
    # maxBytesPerCall must be >= 1 MiB, so create an object > 2 MiB because we
    # need 2 response from the service: 1 success, 1 failure prior to
    # completion.
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=(b'12' * ONE_MIB) + b'bar',
                                   prefer_json_api=True)
    gsutil_api = GcsJsonApi(BucketStorageUri, logging.getLogger(),
                            DiscardMessagesQueue(), self.default_provider)
    key = object_uri.get_key()
    src_obj_metadata = apitools_messages.Object(name=key.name,
                                                bucket=key.bucket.name,
                                                contentType=key.content_type,
                                                etag=key.etag.strip('"\''))
    dst_obj_name = self.MakeTempName('object')
    dst_obj_metadata = apitools_messages.Object(
        bucket=bucket_uri2.bucket_name,
        name=dst_obj_name,
        contentType=src_obj_metadata.contentType)
    tracker_file_name = GetRewriteTrackerFilePath(src_obj_metadata.bucket,
                                                  src_obj_metadata.name,
                                                  dst_obj_metadata.bucket,
                                                  dst_obj_metadata.name,
                                                  self.test_api)
    try:
      try:
        gsutil_api.CopyObject(src_obj_metadata,
                              dst_obj_metadata,
                              progress_callback=HaltingRewriteCallbackHandler(
                                  ONE_MIB * 2).call,
                              max_bytes_per_call=ONE_MIB)
        self.fail('Expected RewriteHaltException.')
      except RewriteHaltException:
        pass

      # Tracker file should be left over.
      self.assertTrue(os.path.exists(tracker_file_name))

      # Now resume. Callback ensures we didn't start over.
      gsutil_api.CopyObject(
          src_obj_metadata,
          dst_obj_metadata,
          progress_callback=EnsureRewriteResumeCallbackHandler(ONE_MIB *
                                                               2).call,
          max_bytes_per_call=ONE_MIB)

      # Copy completed; tracker file should be deleted.
      self.assertFalse(os.path.exists(tracker_file_name))

      self.assertEqual(
          gsutil_api.GetObjectMetadata(src_obj_metadata.bucket,
                                       src_obj_metadata.name,
                                       fields=['customerEncryption',
                                               'md5Hash']).md5Hash,
          gsutil_api.GetObjectMetadata(dst_obj_metadata.bucket,
                                       dst_obj_metadata.name,
                                       fields=['customerEncryption',
                                               'md5Hash']).md5Hash,
          'Error: Rewritten object\'s hash doesn\'t match source object.')
    finally:
      # Clean up if something went wrong.
      DeleteTrackerFile(tracker_file_name)

  def test_rewrite_cp_resume_source_changed(self):
    """Tests that Rewrite starts over when the source object has changed."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip('Rewrite API is only supported in JSON.')
    bucket_uri = self.CreateBucket()
    # Second bucket needs to be a different storage class so the service
    # actually rewrites the bytes.
    bucket_uri2 = self.CreateBucket(
        storage_class='durable_reduced_availability')
    # maxBytesPerCall must be >= 1 MiB, so create an object > 2 MiB because we
    # need 2 response from the service: 1 success, 1 failure prior to
    # completion.
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=(b'12' * ONE_MIB) + b'bar',
                                   prefer_json_api=True)
    gsutil_api = GcsJsonApi(BucketStorageUri, logging.getLogger(),
                            DiscardMessagesQueue(), self.default_provider)
    key = object_uri.get_key()
    src_obj_metadata = apitools_messages.Object(name=key.name,
                                                bucket=key.bucket.name,
                                                contentType=key.content_type,
                                                etag=key.etag.strip('"\''))
    dst_obj_name = self.MakeTempName('object')
    dst_obj_metadata = apitools_messages.Object(
        bucket=bucket_uri2.bucket_name,
        name=dst_obj_name,
        contentType=src_obj_metadata.contentType)
    tracker_file_name = GetRewriteTrackerFilePath(src_obj_metadata.bucket,
                                                  src_obj_metadata.name,
                                                  dst_obj_metadata.bucket,
                                                  dst_obj_metadata.name,
                                                  self.test_api)
    try:
      try:
        gsutil_api.CopyObject(src_obj_metadata,
                              dst_obj_metadata,
                              progress_callback=HaltingRewriteCallbackHandler(
                                  ONE_MIB * 2).call,
                              max_bytes_per_call=ONE_MIB)
        self.fail('Expected RewriteHaltException.')
      except RewriteHaltException:
        pass
      # Overwrite the original object.
      object_uri2 = self.CreateObject(bucket_uri=bucket_uri,
                                      object_name='foo',
                                      contents=b'bar',
                                      prefer_json_api=True)
      key2 = object_uri2.get_key()
      src_obj_metadata2 = apitools_messages.Object(
          name=key2.name,
          bucket=key2.bucket.name,
          contentType=key2.content_type,
          etag=key2.etag.strip('"\''))

      # Tracker file for original object should still exist.
      self.assertTrue(os.path.exists(tracker_file_name))

      # Copy the new object.
      gsutil_api.CopyObject(src_obj_metadata2,
                            dst_obj_metadata,
                            max_bytes_per_call=ONE_MIB)

      # Copy completed; original tracker file should be deleted.
      self.assertFalse(os.path.exists(tracker_file_name))

      self.assertEqual(
          gsutil_api.GetObjectMetadata(src_obj_metadata2.bucket,
                                       src_obj_metadata2.name,
                                       fields=['customerEncryption',
                                               'md5Hash']).md5Hash,
          gsutil_api.GetObjectMetadata(dst_obj_metadata.bucket,
                                       dst_obj_metadata.name,
                                       fields=['customerEncryption',
                                               'md5Hash']).md5Hash,
          'Error: Rewritten object\'s hash doesn\'t match source object.')
    finally:
      # Clean up if something went wrong.
      DeleteTrackerFile(tracker_file_name)

  def test_rewrite_cp_resume_command_changed(self):
    """Tests that Rewrite starts over when the arguments changed."""
    if self.test_api == ApiSelector.XML:
      return unittest.skip('Rewrite API is only supported in JSON.')
    bucket_uri = self.CreateBucket()
    # Second bucket needs to be a different storage class so the service
    # actually rewrites the bytes.
    bucket_uri2 = self.CreateBucket(
        storage_class='durable_reduced_availability')
    # maxBytesPerCall must be >= 1 MiB, so create an object > 2 MiB because we
    # need 2 response from the service: 1 success, 1 failure prior to
    # completion.
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=(b'12' * ONE_MIB) + b'bar',
                                   prefer_json_api=True)
    gsutil_api = GcsJsonApi(BucketStorageUri, logging.getLogger(),
                            DiscardMessagesQueue(), self.default_provider)
    key = object_uri.get_key()
    src_obj_metadata = apitools_messages.Object(name=key.name,
                                                bucket=key.bucket.name,
                                                contentType=key.content_type,
                                                etag=key.etag.strip('"\''))
    dst_obj_name = self.MakeTempName('object')
    dst_obj_metadata = apitools_messages.Object(
        bucket=bucket_uri2.bucket_name,
        name=dst_obj_name,
        contentType=src_obj_metadata.contentType)
    tracker_file_name = GetRewriteTrackerFilePath(src_obj_metadata.bucket,
                                                  src_obj_metadata.name,
                                                  dst_obj_metadata.bucket,
                                                  dst_obj_metadata.name,
                                                  self.test_api)
    try:
      try:
        gsutil_api.CopyObject(src_obj_metadata,
                              dst_obj_metadata,
                              canned_acl='private',
                              progress_callback=HaltingRewriteCallbackHandler(
                                  ONE_MIB * 2).call,
                              max_bytes_per_call=ONE_MIB)
        self.fail('Expected RewriteHaltException.')
      except RewriteHaltException:
        pass

      # Tracker file for original object should still exist.
      self.assertTrue(os.path.exists(tracker_file_name))

      # Copy the same object but with different call parameters.
      gsutil_api.CopyObject(src_obj_metadata,
                            dst_obj_metadata,
                            canned_acl='public-read',
                            max_bytes_per_call=ONE_MIB)

      # Copy completed; original tracker file should be deleted.
      self.assertFalse(os.path.exists(tracker_file_name))

      new_obj_metadata = gsutil_api.GetObjectMetadata(
          dst_obj_metadata.bucket,
          dst_obj_metadata.name,
          fields=['acl', 'customerEncryption', 'md5Hash'])
      self.assertEqual(
          gsutil_api.GetObjectMetadata(src_obj_metadata.bucket,
                                       src_obj_metadata.name,
                                       fields=['customerEncryption',
                                               'md5Hash']).md5Hash,
          new_obj_metadata.md5Hash,
          'Error: Rewritten object\'s hash doesn\'t match source object.')
      # New object should have a public-read ACL from the second command.
      found_public_acl = False
      for acl_entry in new_obj_metadata.acl:
        if acl_entry.entity == 'allUsers':
          found_public_acl = True
      self.assertTrue(found_public_acl,
                      'New object was not written with a public ACL.')
    finally:
      # Clean up if something went wrong.
      DeleteTrackerFile(tracker_file_name)

  @unittest.skipIf(IS_WINDOWS, 'POSIX attributes not available on Windows.')
  @unittest.skipUnless(UsingCrcmodExtension(), 'Test requires fast crcmod.')
  def test_cp_preserve_posix_bucket_to_dir_no_errors(self):
    """Tests use of the -P flag with cp from a bucket to a local dir.

    Specifically tests combinations of POSIX attributes in metadata that will
    pass validation.
    """
    bucket_uri = self.CreateBucket()
    tmpdir = self.CreateTempDir()
    TestCpMvPOSIXBucketToLocalNoErrors(self, bucket_uri, tmpdir, is_cp=True)

  @unittest.skipIf(IS_WINDOWS, 'POSIX attributes not available on Windows.')
  def test_cp_preserve_posix_bucket_to_dir_errors(self):
    """Tests use of the -P flag with cp from a bucket to a local dir.

    Specifically, combinations of POSIX attributes in metadata that will fail
    validation.
    """
    bucket_uri = self.CreateBucket()
    tmpdir = self.CreateTempDir()

    obj = self.CreateObject(bucket_uri=bucket_uri,
                            object_name='obj',
                            contents=b'obj')
    TestCpMvPOSIXBucketToLocalErrors(self, bucket_uri, obj, tmpdir, is_cp=True)

  @unittest.skipIf(IS_WINDOWS, 'POSIX attributes not available on Windows.')
  def test_cp_preseve_posix_dir_to_bucket_no_errors(self):
    """Tests use of the -P flag with cp from a local dir to a bucket."""
    bucket_uri = self.CreateBucket()
    TestCpMvPOSIXLocalToBucketNoErrors(self, bucket_uri, is_cp=True)

  def test_cp_minus_s_to_non_cloud_dest_fails(self):
    """Test that cp -s operations to a non-cloud destination are prevented."""
    local_file = self.CreateTempFile(contents=b'foo')
    dest_dir = self.CreateTempDir()
    stderr = self.RunGsUtil(['cp', '-s', 'standard', local_file, dest_dir],
                            expected_status=1,
                            return_stderr=True)
    self.assertIn('Cannot specify storage class for a non-cloud destination:',
                  stderr)

  # TODO: Remove @skip annotation from this test once we upgrade to the Boto
  # version that parses the storage class header for HEAD Object responses.
  @SkipForXML('Need Boto version > 2.46.1')
  def test_cp_specify_nondefault_storage_class(self):
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'foo')
    object2_suri = suri(object_uri) + 'bar'
    # Specify storage class name as mixed case here to ensure that it
    # gets normalized to uppercase (S3 would return an error otherwise), and
    # that using the normalized case is accepted by each API.
    nondefault_storage_class = {
        's3': 'Standard_iA',
        'gs': 'durable_REDUCED_availability'
    }
    storage_class = nondefault_storage_class[self.default_provider]
    self.RunGsUtil(['cp', '-s', storage_class, suri(object_uri), object2_suri])
    stdout = self.RunGsUtil(['stat', object2_suri], return_stdout=True)
    self.assertRegexpMatchesWithFlags(stdout,
                                      r'Storage class:\s+%s' % storage_class,
                                      flags=re.IGNORECASE)

  @SkipForS3('Test uses gs-specific storage classes.')
  def test_cp_sets_correct_dest_storage_class(self):
    """Tests that object storage class is set correctly with and without -s."""
    # Use a non-default storage class as the default for the bucket.
    bucket_uri = self.CreateBucket(storage_class='nearline')
    # Ensure storage class is set correctly for a local-to-cloud copy.
    local_fname = 'foo-orig'
    local_fpath = self.CreateTempFile(contents=b'foo', file_name=local_fname)
    foo_cloud_suri = suri(bucket_uri) + '/' + local_fname
    self.RunGsUtil(['cp', '-s', 'standard', local_fpath, foo_cloud_suri])
    with SetBotoConfigForTest([('GSUtil', 'prefer_api', 'json')]):
      stdout = self.RunGsUtil(['stat', foo_cloud_suri], return_stdout=True)
    self.assertRegexpMatchesWithFlags(stdout,
                                      r'Storage class:\s+STANDARD',
                                      flags=re.IGNORECASE)

    # Ensure storage class is set correctly for a cloud-to-cloud copy when no
    # destination storage class is specified.
    foo_nl_suri = suri(bucket_uri) + '/foo-nl'
    self.RunGsUtil(['cp', foo_cloud_suri, foo_nl_suri])
    # TODO: Remove with-clause after adding storage class parsing in Boto.
    with SetBotoConfigForTest([('GSUtil', 'prefer_api', 'json')]):
      stdout = self.RunGsUtil(['stat', foo_nl_suri], return_stdout=True)
    self.assertRegexpMatchesWithFlags(stdout,
                                      r'Storage class:\s+NEARLINE',
                                      flags=re.IGNORECASE)

    # Ensure storage class is set correctly for a cloud-to-cloud copy when a
    # non-bucket-default storage class is specified.
    foo_std_suri = suri(bucket_uri) + '/foo-std'
    self.RunGsUtil(['cp', '-s', 'standard', foo_nl_suri, foo_std_suri])
    # TODO: Remove with-clause after adding storage class parsing in Boto.
    with SetBotoConfigForTest([('GSUtil', 'prefer_api', 'json')]):
      stdout = self.RunGsUtil(['stat', foo_std_suri], return_stdout=True)
    self.assertRegexpMatchesWithFlags(stdout,
                                      r'Storage class:\s+STANDARD',
                                      flags=re.IGNORECASE)

  @SkipForS3('Test uses gs-specific KMS encryption')
  def test_kms_key_correctly_applied_to_dst_obj_from_src_with_no_key(self):
    bucket_uri = self.CreateBucket()
    obj1_name = 'foo'
    obj2_name = 'bar'
    key_fqn = AuthorizeProjectToUseTestingKmsKey()

    # Create the unencrypted object, then copy it, specifying a KMS key for the
    # new object.
    obj_uri = self.CreateObject(bucket_uri=bucket_uri,
                                object_name=obj1_name,
                                contents=b'foo')
    with SetBotoConfigForTest([('GSUtil', 'encryption_key', key_fqn)]):
      self.RunGsUtil(
          ['cp', suri(obj_uri),
           '%s/%s' % (suri(bucket_uri), obj2_name)])

    # Make sure the new object is encrypted with the specified KMS key.
    with SetBotoConfigForTest([('GSUtil', 'prefer_api', 'json')]):
      self.AssertObjectUsesCMEK('%s/%s' % (suri(bucket_uri), obj2_name),
                                key_fqn)

  @SkipForS3('Test uses gs-specific KMS encryption')
  def test_kms_key_correctly_applied_to_dst_obj_from_local_file(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=b'abcd')
    obj_name = 'foo'
    obj_suri = suri(bucket_uri) + '/' + obj_name
    key_fqn = AuthorizeProjectToUseTestingKmsKey()

    with SetBotoConfigForTest([('GSUtil', 'encryption_key', key_fqn)]):
      self.RunGsUtil(['cp', fpath, obj_suri])

    with SetBotoConfigForTest([('GSUtil', 'prefer_api', 'json')]):
      self.AssertObjectUsesCMEK(obj_suri, key_fqn)

  @SkipForS3('Test uses gs-specific KMS encryption')
  def test_kms_key_works_with_resumable_upload(self):
    resumable_threshold = 1024 * 1024  # 1M
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=b'a' * resumable_threshold)
    obj_name = 'foo'
    obj_suri = suri(bucket_uri) + '/' + obj_name
    key_fqn = AuthorizeProjectToUseTestingKmsKey()

    with SetBotoConfigForTest([('GSUtil', 'encryption_key', key_fqn),
                               ('GSUtil', 'resumable_threshold',
                                str(resumable_threshold))]):
      self.RunGsUtil(['cp', fpath, obj_suri])

    with SetBotoConfigForTest([('GSUtil', 'prefer_api', 'json')]):
      self.AssertObjectUsesCMEK(obj_suri, key_fqn)

  @SkipForS3('Test uses gs-specific KMS encryption')
  def test_kms_key_correctly_applied_to_dst_obj_from_src_with_diff_key(self):
    bucket_uri = self.CreateBucket()
    obj1_name = 'foo'
    obj2_name = 'bar'
    key1_fqn = AuthorizeProjectToUseTestingKmsKey()
    key2_fqn = AuthorizeProjectToUseTestingKmsKey(
        key_name=KmsTestingResources.CONSTANT_KEY_NAME2)
    obj1_suri = suri(
        self.CreateObject(bucket_uri=bucket_uri,
                          object_name=obj1_name,
                          contents=b'foo',
                          kms_key_name=key1_fqn))

    # Copy the object to the same bucket, specifying a different key to be used.
    obj2_suri = '%s/%s' % (suri(bucket_uri), obj2_name)
    with SetBotoConfigForTest([('GSUtil', 'encryption_key', key2_fqn)]):
      self.RunGsUtil(['cp', obj1_suri, obj2_suri])

    # Ensure the new object has the different key.
    with SetBotoConfigForTest([('GSUtil', 'prefer_api', 'json')]):
      self.AssertObjectUsesCMEK(obj2_suri, key2_fqn)

  @SkipForS3('Test uses gs-specific KMS encryption')
  @SkipForXML('Copying KMS-encrypted objects prohibited with XML API')
  def test_kms_key_not_applied_to_nonkms_dst_obj_from_src_with_kms_key(self):
    bucket_uri = self.CreateBucket()
    obj1_name = 'foo'
    obj2_name = 'bar'
    key1_fqn = AuthorizeProjectToUseTestingKmsKey()
    obj1_suri = suri(
        self.CreateObject(bucket_uri=bucket_uri,
                          object_name=obj1_name,
                          contents=b'foo',
                          kms_key_name=key1_fqn))

    # Copy the object to the same bucket, not specifying any KMS key.
    obj2_suri = '%s/%s' % (suri(bucket_uri), obj2_name)
    self.RunGsUtil(['cp', obj1_suri, obj2_suri])

    # Ensure the new object has no KMS key.
    with SetBotoConfigForTest([('GSUtil', 'prefer_api', 'json')]):
      self.AssertObjectUnencrypted(obj2_suri)

  @unittest.skipUnless(
      IS_WINDOWS,
      'Only Windows paths need to be normalized to use backslashes instead of '
      'forward slashes.')
  def test_windows_path_with_back_and_forward_slash_is_normalized(self):
    # Prior to this test and its corresponding fix, running
    # `gsutil cp dir/./file gs://bucket` would result in an object whose name
    # was "dir/./file", rather than just "file", as Windows tried to split on
    # the path component separator "\" intead of "/".
    tmp_dir = self.CreateTempDir()
    self.CreateTempFile(tmpdir=tmp_dir, file_name='obj1', contents=b'foo')
    bucket_uri = self.CreateBucket()
    self.RunGsUtil(['cp', '%s\\./obj1' % tmp_dir, suri(bucket_uri)])
    # If the destination path was not created correctly, this stat call should
    # fail with a non-zero exit code because the specified object won't exist.
    self.RunGsUtil(['stat', '%s/obj1' % suri(bucket_uri)])

  def test_cp_minus_m_streaming_upload(self):
    """Tests that cp -m - anything is disallowed."""
    stderr = self.RunGsUtil(['-m', 'cp', '-', 'file'],
                            return_stderr=True,
                            expected_status=1)
    if self._use_gcloud_storage:
      self.assertIn(
          'WARNING: Using sequential instead of parallel task execution to'
          ' transfer from stdin', stderr)
    else:
      self.assertIn(
          'CommandException: Cannot upload from a stream when using gsutil -m',
          stderr)

  @SequentialAndParallelTransfer
  def test_cp_overwrites_existing_destination(self):
    key_uri = self.CreateObject(contents=b'foo')
    fpath = self.CreateTempFile(contents=b'bar')
    stderr = self.RunGsUtil(['cp', suri(key_uri), fpath], return_stderr=True)
    with open(fpath, 'rb') as f:
      self.assertEqual(f.read(), b'foo')

  @SequentialAndParallelTransfer
  def test_downloads_are_reliable_with_more_than_one_gsutil_instance(self):
    test_file_count = 10
    temporary_directory = self.CreateTempDir()
    bucket_uri = self.CreateBucket(test_objects=test_file_count)

    cp_args = ['cp', suri(bucket_uri, '*'), temporary_directory]
    threads = []
    for _ in range(2):
      thread = threading.Thread(target=self.RunGsUtil, args=[cp_args])
      thread.start()
      threads.append(thread)
    [t.join() for t in threads]

    self.assertEqual(len(os.listdir(temporary_directory)), test_file_count)


class TestCpUnitTests(testcase.GsUtilUnitTestCase):
  """Unit tests for gsutil cp."""

  def testDownloadWithNoHashAvailable(self):
    """Tests a download with no valid server-supplied hash."""
    # S3 should have a special message for non-MD5 etags.
    bucket_uri = self.CreateBucket(provider='s3')
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
    object_uri.get_key().etag = '12345'  # Not an MD5
    dst_dir = self.CreateTempDir()

    log_handler = self.RunCommand('cp', [suri(object_uri), dst_dir],
                                  return_log_handler=True)
    warning_messages = log_handler.messages['warning']
    self.assertEqual(2, len(warning_messages))
    self.assertRegex(
        warning_messages[0], r'Non-MD5 etag \(12345\) present for key .*, '
        r'data integrity checks are not possible')
    self.assertIn('Integrity cannot be assured', warning_messages[1])

  def testDownloadWithDestinationEndingWithDelimiterRaisesError(self):
    """Tests a download with no valid server-supplied hash."""
    # S3 should have a special message for non-MD5 etags.
    bucket_uri = self.CreateBucket(provider='s3')
    object_uri = self.CreateObject(bucket_uri=bucket_uri, contents=b'foo')
    destination_path = 'random_dir' + os.path.sep

    with self.assertRaises(InvalidUrlError) as error:
      self.RunCommand('cp', [suri(object_uri), destination_path])
      self.assertEqual(str(error), 'Invalid destination path: random_dir/')

  def test_object_and_prefix_same_name(self):
    bucket_uri = self.CreateBucket()
    object_uri = self.CreateObject(bucket_uri=bucket_uri,
                                   object_name='foo',
                                   contents=b'foo')
    self.CreateObject(bucket_uri=bucket_uri,
                      object_name='foo/bar',
                      contents=b'bar')
    fpath = self.CreateTempFile()
    # MockKey doesn't support hash_algs, so the MD5 will not match.
    with SetBotoConfigForTest([('GSUtil', 'check_hashes', 'never')]):
      self.RunCommand('cp', [suri(object_uri), fpath])
    with open(fpath, 'rb') as f:
      self.assertEqual(f.read(), b'foo')

  def test_cp_upload_respects_no_hashes(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=b'abcd')
    with SetBotoConfigForTest([('GSUtil', 'check_hashes', 'never')]):
      log_handler = self.RunCommand('cp', [fpath, suri(bucket_uri)],
                                    return_log_handler=True)
    warning_messages = log_handler.messages['warning']
    self.assertEqual(1, len(warning_messages))
    self.assertIn('Found no hashes to validate object upload',
                  warning_messages[0])

  @unittest.skipIf(IS_WINDOWS, 'POSIX attributes not available on Windows.')
  @mock.patch('os.geteuid', new=mock.Mock(return_value=0))
  @mock.patch.object(os, 'chown', autospec=True)
  def test_posix_runs_chown_as_super_user(self, mock_chown):
    fpath = self.CreateTempFile(contents=b'abcd')
    obj = apitools_messages.Object()
    obj.metadata = CreateCustomMetadata(entries={UID_ATTR: USER_ID})
    ParseAndSetPOSIXAttributes(fpath, obj, False, True)
    mock_chown.assert_called_once_with(fpath, USER_ID, -1)

  @unittest.skipIf(IS_WINDOWS, 'POSIX attributes not available on Windows.')
  @mock.patch('os.geteuid', new=mock.Mock(return_value=1))
  @mock.patch.object(os, 'chown', autospec=True)
  def test_posix_skips_chown_when_not_super_user(self, mock_chown):
    fpath = self.CreateTempFile(contents=b'abcd')
    obj = apitools_messages.Object()
    obj.metadata = CreateCustomMetadata(entries={UID_ATTR: USER_ID})
    ParseAndSetPOSIXAttributes(fpath, obj, False, True)
    mock_chown.assert_not_called()

  @mock.patch(
      'gslib.utils.copy_helper.TriggerReauthForDestinationProviderIfNecessary')
  @mock.patch('gslib.command.Command._GetProcessAndThreadCount')
  @mock.patch('gslib.command.Command.Apply',
              new=mock.Mock(spec=command.Command.Apply))
  def test_cp_triggers_reauth(self, mock_get_process_and_thread_count,
                              mock_trigger_reauth):
    path = self.CreateTempFile(file_name=('foo'))
    bucket_uri = self.CreateBucket()
    mock_get_process_and_thread_count.return_value = 2, 3

    self.RunCommand('cp', [path, suri(bucket_uri)])

    mock_trigger_reauth.assert_called_once_with(
        StorageUrlFromString(suri(bucket_uri)),
        mock.ANY,  # Gsutil API.
        6,  # Worker count.
    )

    mock_get_process_and_thread_count.assert_called_once_with(
        process_count=None,
        thread_count=None,
        parallel_operations_override=None,
        print_macos_warning=False,
    )

  def test_translates_predefined_acl_sub_opts(self):
    sub_opts = [('--flag-key', 'flag-value'), ('-a', 'public-read'),
                ('-a', 'does-not-exist')]
    ShimTranslatePredefinedAclSubOptForCopy(sub_opts)
    self.assertEqual(sub_opts, [('--flag-key', 'flag-value'),
                                ('-a', 'publicRead'), ('-a', 'does-not-exist')])

  def test_shim_translates_flags(self):
    bucket_uri = self.CreateBucket()
    fpath = self.CreateTempFile(contents=b'abcd')
    with SetBotoConfigForTest([('GSUtil', 'use_gcloud_storage', 'True'),
                               ('GSUtil', 'hidden_shim_mode', 'dry_run')]):
      with SetEnvironmentForTest({
          'CLOUDSDK_CORE_PASS_CREDENTIALS_TO_GSUTIL': 'True',
          'CLOUDSDK_ROOT_DIR': 'fake_dir',
      }):
        mock_log_handler = self.RunCommand('cp', [
            '-e', '-n', '-r', '-R', '-s', 'some-class', '-v', '-a',
            'public-read', fpath,
            suri(bucket_uri)
        ],
                                           return_log_handler=True)
        info_lines = '\n'.join(mock_log_handler.messages['info'])
        self.assertIn(
            'Gcloud Storage Command: {} storage cp'
            ' --ignore-symlinks --no-clobber -r -r --storage-class some-class'
            ' --print-created-message --predefined-acl publicRead {} {}'.format(
                shim_util._get_gcloud_binary_path('fake_dir'), fpath,
                suri(bucket_uri)), info_lines)
        warn_lines = '\n'.join(mock_log_handler.messages['warning'])
        self.assertIn('Use the -m flag to enable parallelism', warn_lines)

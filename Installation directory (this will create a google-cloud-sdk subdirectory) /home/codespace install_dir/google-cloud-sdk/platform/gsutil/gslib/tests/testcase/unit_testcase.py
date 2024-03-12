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
"""Contains gsutil base unit test case class."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import logging
import os
import sys
import tempfile

import six

import boto
from boto.utils import get_utf8able_str
from gslib import project_id
from gslib import wildcard_iterator
from gslib.boto_translation import BotoTranslation
from gslib.cloud_api_delegator import CloudApiDelegator
from gslib.command_runner import CommandRunner
from gslib.cs_api_map import ApiMapConstants
from gslib.cs_api_map import ApiSelector
from gslib.discard_messages_queue import DiscardMessagesQueue
from gslib.gcs_json_api import GcsJsonApi
from gslib.tests.mock_logging_handler import MockLoggingHandler
from gslib.tests.testcase import base
import gslib.tests.util as util
from gslib.tests.util import unittest
from gslib.tests.util import WorkingDirectory
from gslib.utils.constants import UTF8
from gslib.utils.text_util import print_to_fd


def _AttemptToCloseSysFd(fd):
  """Suppress IOError when closing sys.stdout or sys.stderr in tearDown."""
  # In PY2, if another sibling thread/process tried closing it at the same
  # time we did, it succeeded either way, so we just continue. This approach
  # was taken from https://github.com/pytest-dev/pytest/pull/3305.
  if not six.PY2:  # This doesn't happen in PY3, AFAICT.
    fd.close()
    return

  try:
    fd.close()
  except IOError:
    pass


class GsutilApiUnitTestClassMapFactory(object):
  """Class map factory for use in unit tests.

  BotoTranslation is used for all cases so that GSMockBucketStorageUri can
  be used to communicate with the mock XML service.
  """

  @classmethod
  def GetClassMap(cls):
    """Returns a class map for use in unit tests."""
    gs_class_map = {
        ApiSelector.XML:
            BotoTranslation,
        # TODO: This should be replaced with 'ApiSelector.JSON: GcsJsonApi'.
        # Refer Issue https://github.com/GoogleCloudPlatform/gsutil/issues/970
        ApiSelector.JSON:
            BotoTranslation
    }
    s3_class_map = {ApiSelector.XML: BotoTranslation}
    class_map = {'gs': gs_class_map, 's3': s3_class_map}
    return class_map


@unittest.skipUnless(util.RUN_UNIT_TESTS, 'Not running integration tests.')
class GsUtilUnitTestCase(base.GsUtilTestCase):
  """Base class for gsutil unit tests."""

  @classmethod
  def setUpClass(cls):
    base.GsUtilTestCase.setUpClass()
    cls.mock_bucket_storage_uri = util.GSMockBucketStorageUri
    cls.mock_gsutil_api_class_map_factory = GsutilApiUnitTestClassMapFactory
    cls.logger = logging.getLogger()
    cls.command_runner = CommandRunner(
        bucket_storage_uri_class=cls.mock_bucket_storage_uri,
        gsutil_api_class_map_factory=cls.mock_gsutil_api_class_map_factory)
    # Ensure unit tests don't fail if no default_project_id is defined in the
    # boto config file.
    project_id.UNIT_TEST_PROJECT_ID = 'mock-project-id-for-unit-tests'

  def setUp(self):
    super(GsUtilUnitTestCase, self).setUp()
    self.bucket_uris = []
    self.stdout_save = sys.stdout
    self.stderr_save = sys.stderr
    fd, self.stdout_file = tempfile.mkstemp()
    # Specify the encoding explicitly to ensure Windows uses 'utf-8' instead of
    # the default of 'cp1252'.
    if six.PY2:
      sys.stdout = os.fdopen(fd, 'w+')
    else:
      sys.stdout = os.fdopen(fd, 'w+', encoding='utf-8')
    fd, self.stderr_file = tempfile.mkstemp()
    # do not set sys.stderr to be 'wb+' - it will blow up the logger
    if six.PY2:
      sys.stderr = os.fdopen(fd, 'w+')
    else:
      sys.stderr = os.fdopen(fd, 'w+', encoding='utf-8')
    self.accumulated_stdout = []
    self.accumulated_stderr = []

    self.root_logger = logging.getLogger()
    self.is_debugging = self.root_logger.isEnabledFor(logging.DEBUG)
    self.log_handlers_save = self.root_logger.handlers
    fd, self.log_handler_file = tempfile.mkstemp()
    self.log_handler_stream = os.fdopen(fd, 'w+')
    self.temp_log_handler = logging.StreamHandler(self.log_handler_stream)
    self.root_logger.handlers = [self.temp_log_handler]

  def tearDown(self):
    super(GsUtilUnitTestCase, self).tearDown()

    self.root_logger.handlers = self.log_handlers_save
    self.temp_log_handler.flush()
    self.temp_log_handler.close()
    self.log_handler_stream.seek(0)
    log_output = self.log_handler_stream.read()
    self.log_handler_stream.close()
    os.unlink(self.log_handler_file)

    sys.stdout.seek(0)
    sys.stderr.seek(0)
    if six.PY2:
      stdout = sys.stdout.read()
      stderr = sys.stderr.read()
    else:
      try:
        stdout = sys.stdout.read()
        stderr = sys.stderr.read()
      except UnicodeDecodeError:
        sys.stdout.seek(0)
        sys.stderr.seek(0)
        stdout = sys.stdout.buffer.read()
        stderr = sys.stderr.buffer.read()
    [six.ensure_text(string) for string in self.accumulated_stderr]
    [six.ensure_text(string) for string in self.accumulated_stdout]
    stdout = six.ensure_text(get_utf8able_str(stdout))
    stderr = six.ensure_text(get_utf8able_str(stderr))
    stdout += ''.join(self.accumulated_stdout)
    stderr += ''.join(self.accumulated_stderr)
    _AttemptToCloseSysFd(sys.stdout)
    _AttemptToCloseSysFd(sys.stderr)
    sys.stdout = self.stdout_save
    sys.stderr = self.stderr_save
    os.unlink(self.stdout_file)
    os.unlink(self.stderr_file)

    _id = six.ensure_text(self.id())
    if self.is_debugging and stdout:
      print_to_fd('==== stdout {} ====\n'.format(_id), file=sys.stderr)
      print_to_fd(stdout, file=sys.stderr)
      print_to_fd('==== end stdout ====\n', file=sys.stderr)
    if self.is_debugging and stderr:
      print_to_fd('==== stderr {} ====\n'.format(_id), file=sys.stderr)
      print_to_fd(stderr, file=sys.stderr)
      print_to_fd('==== end stderr ====\n', file=sys.stderr)
    if self.is_debugging and log_output:
      print_to_fd('==== log output {} ====\n'.format(_id), file=sys.stderr)
      print_to_fd(log_output, file=sys.stderr)
      print_to_fd('==== end log output ====\n', file=sys.stderr)

  def RunCommand(self,
                 command_name,
                 args=None,
                 headers=None,
                 debug=0,
                 return_stdout=False,
                 return_stderr=False,
                 return_log_handler=False,
                 cwd=None):
    """Method for calling gslib.command_runner.CommandRunner.

    Passes parallel_operations=False for all tests, optionally saving/returning
    stdout output. We run all tests multi-threaded, to exercise those more
    complicated code paths.
    TODO: Change to run with parallel_operations=True for all tests. At
    present when you do this it causes many test failures.

    Args:
      command_name: The name of the command being run.
      args: Command-line args (arg0 = actual arg, not command name ala bash).
      headers: Dictionary containing optional HTTP headers to pass to boto.
      debug: Debug level to pass in to boto connection (range 0..3).
      return_stdout: If True, will save and return stdout produced by command.
      return_stderr: If True, will save and return stderr produced by command.
      return_log_handler: If True, will return a MockLoggingHandler instance
           that was attached to the command's logger while running.
      cwd: The working directory that should be switched to before running the
           command. The working directory will be reset back to its original
           value after running the command. If not specified, the working
           directory is left unchanged.

    Returns:
      One or a tuple of requested return values, depending on whether
      return_stdout, return_stderr, and/or return_log_handler were specified.
      Return Types:
        stdout - str (binary in Py2, text in Py3)
        stderr - str (binary in Py2, text in Py3)
        log_handler - MockLoggingHandler
    """
    args = args or []

    command_line = six.ensure_text(' '.join([command_name] + args))
    if self.is_debugging:
      print_to_fd('\nRunCommand of {}\n'.format(command_line),
                  file=self.stderr_save)

    # Save and truncate stdout and stderr for the lifetime of RunCommand. This
    # way, we can return just the stdout and stderr that was output during the
    # RunNamedCommand call below.
    sys.stdout.seek(0)
    sys.stderr.seek(0)
    stdout = sys.stdout.read()
    stderr = sys.stderr.read()
    if stdout:
      self.accumulated_stdout.append(stdout)
    if stderr:
      self.accumulated_stderr.append(stderr)
    sys.stdout.seek(0)
    sys.stderr.seek(0)
    sys.stdout.truncate()
    sys.stderr.truncate()

    mock_log_handler = MockLoggingHandler()
    logging.getLogger(command_name).addHandler(mock_log_handler)
    if debug:
      logging.getLogger(command_name).setLevel(logging.DEBUG)

    try:
      with WorkingDirectory(cwd):
        self.command_runner.RunNamedCommand(command_name,
                                            args=args,
                                            headers=headers,
                                            debug=debug,
                                            parallel_operations=False,
                                            do_shutdown=False)
    finally:
      sys.stdout.seek(0)
      sys.stderr.seek(0)
      if six.PY2:
        stdout = sys.stdout.read()
        stderr = sys.stderr.read()
      else:
        try:
          stdout = sys.stdout.read()
          stderr = sys.stderr.read()
        except UnicodeDecodeError:
          sys.stdout.seek(0)
          sys.stderr.seek(0)
          stdout = sys.stdout.buffer.read()
          stderr = sys.stderr.buffer.read()
      logging.getLogger(command_name).removeHandler(mock_log_handler)
      mock_log_handler.close()

      log_output = '\n'.join(
          '%s:\n  ' % level + '\n  '.join(records)
          for level, records in six.iteritems(mock_log_handler.messages)
          if records)

      _id = six.ensure_text(self.id())
      if self.is_debugging and log_output:
        print_to_fd('==== logging RunCommand {} {} ====\n'.format(
            _id, command_line),
                    file=self.stderr_save)
        print_to_fd(log_output, file=self.stderr_save)
        print_to_fd('\n==== end logging ====\n', file=self.stderr_save)
      if self.is_debugging and stdout:
        print_to_fd('==== stdout RunCommand {} {} ====\n'.format(
            _id, command_line),
                    file=self.stderr_save)
        print_to_fd(stdout, file=self.stderr_save)
        print_to_fd('==== end stdout ====\n', file=self.stderr_save)
      if self.is_debugging and stderr:
        print_to_fd('==== stderr RunCommand {} {} ====\n'.format(
            _id, command_line),
                    file=self.stderr_save)
        print_to_fd(stderr, file=self.stderr_save)
        print_to_fd('==== end stderr ====\n', file=self.stderr_save)

      # Reset stdout and stderr files, so that we won't print them out again
      # in tearDown if debugging is enabled.
      sys.stdout.seek(0)
      sys.stderr.seek(0)
      sys.stdout.truncate()
      sys.stderr.truncate()

    to_return = []
    if return_stdout:
      to_return.append(stdout)
    if return_stderr:
      to_return.append(stderr)
    if return_log_handler:
      to_return.append(mock_log_handler)
    if len(to_return) == 1:
      return to_return[0]
    return tuple(to_return)

  @classmethod
  def MakeGsUtilApi(cls, debug=0):
    gsutil_api_map = {
        ApiMapConstants.API_MAP:
            (cls.mock_gsutil_api_class_map_factory.GetClassMap()),
        ApiMapConstants.SUPPORT_MAP: {
            'gs': [ApiSelector.XML, ApiSelector.JSON],
            's3': [ApiSelector.XML]
        },
        ApiMapConstants.DEFAULT_MAP: {
            'gs': ApiSelector.JSON,
            's3': ApiSelector.XML
        }
    }

    return CloudApiDelegator(cls.mock_bucket_storage_uri,
                             gsutil_api_map,
                             cls.logger,
                             DiscardMessagesQueue(),
                             debug=debug)

  @classmethod
  def _test_wildcard_iterator(cls, uri_or_str, exclude_tuple=None, debug=0):
    """Convenience method for instantiating a test instance of WildcardIterator.

    This makes it unnecessary to specify all the params of that class
    (like bucket_storage_uri_class=mock_storage_service.MockBucketStorageUri).
    Also, naming the factory method this way makes it clearer in the test code
    that WildcardIterator needs to be set up for testing.

    Args are same as for wildcard_iterator.wildcard_iterator(), except
    there are no class args for bucket_storage_uri_class or gsutil_api_class.

    Args:
      uri_or_str: StorageUri or string representing the wildcard string.
      exclude_tuple: (base_url, exclude_pattern), where base_url is
                     top-level URL to list; exclude_pattern is a regex
                     of paths to ignore during iteration.
      debug: debug level to pass to the underlying connection (0..3)

    Returns:
      WildcardIterator, over which caller can iterate.
    """
    # TODO: Remove when tests no longer pass StorageUri arguments.
    uri_string = uri_or_str
    if hasattr(uri_or_str, 'uri'):
      uri_string = uri_or_str.uri

    return wildcard_iterator.CreateWildcardIterator(uri_string,
                                                    cls.MakeGsUtilApi(debug),
                                                    exclude_tuple=exclude_tuple)

  @staticmethod
  def _test_storage_uri(uri_str, default_scheme='file', debug=0, validate=True):
    """Convenience method for instantiating a testing instance of StorageUri.

    This makes it unnecessary to specify
    bucket_storage_uri_class=mock_storage_service.MockBucketStorageUri.
    Also naming the factory method this way makes it clearer in the test
    code that StorageUri needs to be set up for testing.

    Args, Returns, and Raises are same as for boto.storage_uri(), except there's
    no bucket_storage_uri_class arg.

    Args:
      uri_str: Uri string to create StorageUri for.
      default_scheme: Default scheme for the StorageUri
      debug: debug level to pass to the underlying connection (0..3)
      validate: If True, validate the resource that the StorageUri refers to.

    Returns:
      StorageUri based on the arguments.
    """
    return boto.storage_uri(uri_str, default_scheme, debug, validate,
                            util.GSMockBucketStorageUri)

  def CreateBucket(self,
                   bucket_name=None,
                   test_objects=0,
                   storage_class=None,
                   provider='gs'):
    """Creates a test bucket.

    The bucket and all of its contents will be deleted after the test.

    Args:
      bucket_name: Create the bucket with this name. If not provided, a
                   temporary test bucket name is constructed.
      test_objects: The number of objects that should be placed in the bucket or
                    a list of object names to place in the bucket. Defaults to
                    0.
      storage_class: storage class to use. If not provided we us standard.
      provider: string provider to use, default gs.

    Returns:
      StorageUri for the created bucket.
    """
    bucket_name = bucket_name or self.MakeTempName('bucket')
    bucket_uri = boto.storage_uri(
        '%s://%s' % (provider, bucket_name.lower()),
        suppress_consec_slashes=False,
        bucket_storage_uri_class=util.GSMockBucketStorageUri)
    bucket_uri.create_bucket(storage_class=storage_class)
    self.bucket_uris.append(bucket_uri)
    try:
      iter(test_objects)
    except TypeError:
      test_objects = [self.MakeTempName('obj') for _ in range(test_objects)]
    for i, name in enumerate(test_objects):
      self.CreateObject(bucket_uri=bucket_uri,
                        object_name=name,
                        contents='test {}'.format(i).encode(UTF8))
    return bucket_uri

  def CreateObject(self, bucket_uri=None, object_name=None, contents=None):
    """Creates a test object.

    Args:
      bucket_uri: The URI of the bucket to place the object in. If not
                  specified, a new temporary bucket is created.
      object_name: The name to use for the object. If not specified, a temporary
                   test object name is constructed.
      contents: The contents to write to the object. If not specified, the key
                is not written to, which means that it isn't actually created
                yet on the server.

    Returns:
      A StorageUri for the created object.
    """
    bucket_uri = bucket_uri or self.CreateBucket(provider=self.default_provider)
    object_name = object_name or self.MakeTempName('obj')
    key_uri = bucket_uri.clone_replace_name(object_name)
    if contents is not None:
      key_uri.set_contents_from_string(contents)
    return key_uri

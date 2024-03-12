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

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from contextlib import contextmanager
import functools
import locale
import logging
import os
import pkgutil
import posixpath
import re
import io
import signal
import subprocess
import sys
import tempfile
import threading
import unittest

import six
from six.moves import urllib
from six.moves import cStringIO

import boto
import crcmod
import gslib
from gslib.kms_api import KmsApi
from gslib.project_id import PopulateProjectId
import mock_storage_service  # From boto/tests/integration/s3

from gslib.cloud_api import ResumableDownloadException
from gslib.cloud_api import ResumableUploadException
from gslib.lazy_wrapper import LazyWrapper
import gslib.tests as gslib_tests
from gslib.utils import posix_util
from gslib.utils.boto_util import UsingCrcmodExtension, HasUserSpecifiedGsHost
from gslib.utils.constants import UTF8
from gslib.utils.encryption_helper import Base64Sha256FromBase64EncryptionKey
from gslib.utils.system_util import IS_WINDOWS
from gslib.utils.unit_util import MakeHumanReadable

# pylint: disable=g-import-not-at-top, g-long-lambda
if not IS_WINDOWS:
  import grp
  import pwd

  def GetInvalidGid():
    # Get a list of all GIDs on the system for quick reference.
    all_gid = sorted([group.gr_gid for group in grp.getgrall()])
    # gid - Current GID being tested, 2k is close to a large empty span on most
    # unix systems and a good starting point.
    gid = 2000
    # OverflowError should prevent loop from reaching 5b, but adding a number
    # to the loop ensures that infinite loop does not occur
    while gid < 5000000000:
      if gid in all_gid:
        # Shortcut check; if gid is in list then the group exists.
        gid += 1
        continue
      try:
        # Testing for expected behaviour while testing POSIX permissions.
        # For more on grp see:
        # https://docs.python.org/3.7/library/grp.html
        grp.getgrgid(gid)
        gid += 1
      except KeyError:
        # This is the target exception for invalid GID and the behaviour needed
        # for testing.
        return gid
      except OverflowError:
        # Limit reached without a usable GID found.
        break
    raise Exception("Unable to generate GID for ")

  def GetNonPrimaryGid():
    # Select a group for the current user that is not the user's primary group.
    # If the length of the user's groups is 1, then we must use the primary
    # group.  Otherwise put all of the user's groups (except the primary group)
    # in a list, and use the first element. This guarantees us a group that is
    # not the user's primary group (unless the user is only a member of one
    # group).
    primary_gid = GetPrimaryGid()
    user_groups = GetUserGroups()
    if len(user_groups) == 1:
      return primary_gid
    return [g for g in list(user_groups) if g != primary_gid][0]

  def GetPrimaryGid():
    return os.getgid()

  def GetUserGroups():
    return set([GetPrimaryGid()] +
               [g.gr_gid for g in grp.getgrall() if USER_NAME() in g.gr_mem])

  posix_util.InitializeDefaultMode()
  DEFAULT_MODE = int(posix_util.SYSTEM_POSIX_MODE, 8)
  USER_ID = os.getuid()
  USER_NAME = LazyWrapper(lambda: pwd.getpwuid(USER_ID).pw_name)
  # Take the current user's UID and increment it by one, this counts as an
  # invalid UID, as the metric used is if the UID matches the current user's,
  # exactly.
  INVALID_UID = LazyWrapper(
      lambda: sorted([user.pw_uid for user in pwd.getpwall()])[-1] + 1)

  # Note that because the system's GID mapping can change mid-test, tests that
  # check for specific errors should always re-fetch these GID-related values,
  # rather than reusing these LazyWrapper values.
  INVALID_GID = LazyWrapper(lambda: GetInvalidGid())
  # Get a list of all groups on the system where the current username is listed
  # as a member of the group in the gr_mem group attribute. Make this a list of
  # all group IDs and cast as a set for more efficient lookup times.
  USER_GROUPS = LazyWrapper(lambda: GetUserGroups())


def GetGsutilCommand(raw_command, force_gsutil=False):
  """Adds config options to a list of strings defining a gsutil subcommand."""
  # TODO(b/203250512) Remove this once all the commands are supported
  # via gcloud storage.
  if force_gsutil:
    use_gcloud_storage = False
  else:
    use_gcloud_storage = boto.config.getbool('GSUtil', 'use_gcloud_storage',
                                             False)
  gcloud_storage_setting = [
      '-o',
      'GSUtil:use_gcloud_storage={}'.format(use_gcloud_storage),
      '-o',
      'GSUtil:hidden_shim_mode=no_fallback',
  ]
  gsutil_command = [
      gslib.GSUTIL_PATH, '--testexceptiontraces', '-o',
      'GSUtil:default_project_id=' + PopulateProjectId()
  ] + gcloud_storage_setting + raw_command

  # Checks to see if the test was invoked from a par file (bundled archive).
  # If not, adds the Python executable path to ensure that the correct version
  # of Python is used for testing.
  if not InvokedFromParFile():
    gsutil_command_with_executable_path = [str(sys.executable)] + gsutil_command
  else:
    gsutil_command_with_executable_path = gsutil_command

  return [six.ensure_str(part) for part in gsutil_command_with_executable_path]


def GetGsutilSubprocess(cmd, env_vars=None):
  """Returns a subprocess.Popen object for for running a gsutil command."""
  env = os.environ.copy()
  if env_vars:
    env.update(env_vars)
  envstr = dict()
  for k, v in six.iteritems(env):
    envstr[six.ensure_str(k)] = six.ensure_str(v)

  # The os.setsid call allows us to kill the process group below
  # if execution times out. With Python 2.7, there's no other way to
  # stop execution (p.kill() doesn't work). Since os.setsid is not available
  # on Windows, we just deal with the occasional timeouts on Windows.
  preexec_fn = os.setsid if hasattr(os, 'setsid') else None
  return subprocess.Popen(cmd,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          stdin=subprocess.PIPE,
                          env=envstr,
                          preexec_fn=preexec_fn)


def CommunicateWithTimeout(process, stdin=None):
  if stdin is not None:
    if six.PY3:
      if not isinstance(stdin, bytes):
        stdin = stdin.encode(UTF8)
    else:
      stdin = stdin.encode(UTF8)
  comm_kwargs = {'input': stdin}

  def Kill():
    os.killpg(os.getpgid(process.pid), signal.SIGKILL)

  if six.PY3:
    # TODO(b/135936279): Make this number configurable in .boto
    comm_kwargs['timeout'] = 180
  else:
    timer = threading.Timer(180, Kill)
    timer.start()

  c_out = process.communicate(**comm_kwargs)

  if not six.PY3:
    timer.cancel()

  try:
    c_out = [six.ensure_text(output) for output in c_out]
  except UnicodeDecodeError:
    c_out = [
        six.ensure_text(output, locale.getpreferredencoding(False))
        for output in c_out
    ]

  return c_out


# 256-bit base64 encryption keys used for testing AES256 customer-supplied
# encryption. These are public and open-source, so don't ever use them for
# real data.
TEST_ENCRYPTION_KEY1 = b'iMSM9eeXliDZHSBJZO71R98tfeW/+87VXTpk5chGd6Y='
TEST_ENCRYPTION_KEY1_SHA256_B64 = Base64Sha256FromBase64EncryptionKey(
    TEST_ENCRYPTION_KEY1)

TEST_ENCRYPTION_KEY2 = b'4TSaQ3S4U+5oxAbByA7HgIigD51zfzGed/c03Ts2TXc='
TEST_ENCRYPTION_KEY2_SHA256_B64 = Base64Sha256FromBase64EncryptionKey(
    TEST_ENCRYPTION_KEY2)

TEST_ENCRYPTION_KEY3 = b'HO4Q2X28N/6SmuAJ1v1CTuJjf5emQcXf7YriKzT1gj0='
TEST_ENCRYPTION_KEY3_SHA256_B64 = Base64Sha256FromBase64EncryptionKey(
    TEST_ENCRYPTION_KEY3)

TEST_ENCRYPTION_KEY4 = b'U6zIErjZCK/IpIeDS0pJrDayqlZurY8M9dvPJU0SXI8='
TEST_ENCRYPTION_KEY4_SHA256_B64 = Base64Sha256FromBase64EncryptionKey(
    TEST_ENCRYPTION_KEY4)

TEST_ENCRYPTION_KEY_S3 = b'MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI='
TEST_ENCRYPTION_KEY_S3_MD5 = b'dnF5x6K/8ZZRzpfSlMMM+w=='

TEST_ENCRYPTION_CONTENT1 = b'bar'
TEST_ENCRYPTION_CONTENT1_MD5 = 'N7UdGUp1E+RbVvZSTy1R8g=='
TEST_ENCRYPTION_CONTENT1_CRC32C = 'CrcTMQ=='
TEST_ENCRYPTION_CONTENT2 = b'bar2'
TEST_ENCRYPTION_CONTENT2_MD5 = 'Ik4lOfUiA+szcorNIotEMg=='
TEST_ENCRYPTION_CONTENT2_CRC32C = 'QScXtg=='
TEST_ENCRYPTION_CONTENT3 = b'bar3'
TEST_ENCRYPTION_CONTENT3_MD5 = '9iW6smjfu9hm0A//VQTQfw=='
TEST_ENCRYPTION_CONTENT3_CRC32C = 's0yUtQ=='
TEST_ENCRYPTION_CONTENT4 = b'bar4'
TEST_ENCRYPTION_CONTENT4_MD5 = 'kPCx6uZiUOU7W6E+cDCZFg=='
TEST_ENCRYPTION_CONTENT4_CRC32C = 'Z4bwXg=='
TEST_ENCRYPTION_CONTENT5 = b'bar5'
TEST_ENCRYPTION_CONTENT5_MD5 = '758XbXQOVkp8fTKMm83NXA=='
TEST_ENCRYPTION_CONTENT5_CRC32C = 'le1zXQ=='

# Flags for running different types of tests.
RUN_INTEGRATION_TESTS = True
RUN_UNIT_TESTS = True
RUN_S3_TESTS = False
USE_MULTIREGIONAL_BUCKETS = False

PARALLEL_COMPOSITE_UPLOAD_TEST_CONFIG = '/tmp/.boto.parallel_upload_test_config'

ORPHANED_FILE = ('This sync will orphan file(s), please fix their permissions '
                 'before trying again.')

POSIX_MODE_ERROR = 'Mode for %s won\'t allow read access.'
POSIX_GID_ERROR = 'GID for %s doesn\'t exist on current system.'
POSIX_UID_ERROR = 'UID for %s doesn\'t exist on current system.'
POSIX_INSUFFICIENT_ACCESS_ERROR = 'Insufficient access with uid/gid/mode for %s'


class KmsTestingResources(object):
  """Constants for KMS resource names to be used in integration testing."""
  KEYRING_LOCATION = 'us-central1'
  # Since KeyRings and their child resources cannot be deleted, we minimize the
  # number of resources created by using a hard-coded keyRing name.
  KEYRING_NAME = 'keyring-for-gsutil-integration-tests'

  # Used by tests where we don't need to alter the state of a cryptoKey and/or
  # its IAM policy bindings once it's initialized the first time.
  CONSTANT_KEY_NAME = 'key-for-gsutil-integration-tests'
  CONSTANT_KEY_NAME2 = 'key-for-gsutil-integration-tests2'

  # This key should not be authorized so it can be used for failure cases.
  CONSTANT_KEY_NAME_DO_NOT_AUTHORIZE = 'key-for-gsutil-no-auth'
  # Pattern used for keys that should only be operated on by one tester at a
  # time. Because multiple integration test invocations can run at the same
  # time, we want to minimize the risk of them operating on each other's key,
  # while also not creating too many one-time-use keys (as they cannot be
  # deleted). Tests should fill in the %d entries with a digit between 0 and 9.
  MUTABLE_KEY_NAME_TEMPLATE = 'cryptokey-for-gsutil-integration-tests-%d%d%d'


def AuthorizeProjectToUseTestingKmsKey(
    key_name=KmsTestingResources.CONSTANT_KEY_NAME):
  """Ensures test keys exist and that the service agent is authorized."""
  kms_api = KmsApi(logging.getLogger())

  keyring_fully_qualified_name = kms_api.CreateKeyRing(
      PopulateProjectId(None),
      KmsTestingResources.KEYRING_NAME,
      location=KmsTestingResources.KEYRING_LOCATION)

  key_fully_qualified_name = kms_api.CreateCryptoKey(
      keyring_fully_qualified_name, key_name)
  cmd = GetGsutilCommand(['kms', 'authorize', '-k', key_fully_qualified_name],
                         force_gsutil=True)
  process = GetGsutilSubprocess(cmd)
  CommunicateWithTimeout(process)
  return key_fully_qualified_name


def BuildErrorRegex(obj, err_str):
  """Builds a regex to match a file name for a file that would be orphaned.

  Args:
    obj: Object uri.
    err_str: The error string to search for.

  Returns:
    A regex that will match the file name and with the error text for a file
    that would be orphaned.
  """
  return re.compile(err_str % ObjectToURI(obj))


def TailSet(start_point, listing):
  """Returns set of object name tails.

  Tails can be compared between source and dest, past the point at which the
  command was done. For example if test ran {cp,mv,rsync}
  gs://bucket1/dir gs://bucket2/dir2, the tails for listings from bucket1
  would start after "dir", while the tails for listings from bucket2 would
  start after "dir2".

  Args:
    start_point: The target of the cp command, e.g., for the above command it
                 would be gs://bucket1/dir for the bucket1 listing results and
                 gs://bucket2/dir2 for the bucket2 listing results.
    listing: The listing over which to compute tail.

  Returns:
    Object name tails.
  """
  return set(l[len(start_point):] for l in listing.strip().split('\n'))


HAS_S3_CREDS = (boto.config.get('Credentials', 'aws_access_key_id', None) and
                boto.config.get('Credentials', 'aws_secret_access_key', None))

HAS_NON_DEFAULT_GS_HOST = HasUserSpecifiedGsHost()

HAS_GS_HOST = boto.config.get('Credentials', 'gs_host', None) is not None

HAS_GS_PORT = boto.config.get('Credentials', 'gs_port', None) is not None

USING_JSON_API = boto.config.get('GSUtil', 'prefer_api',
                                 'json').upper() != 'XML'


def _ArgcompleteAvailable():
  argcomplete = None
  if not IS_WINDOWS:
    try:
      # pylint: disable=g-import-not-at-top
      import argcomplete
    except ImportError:
      pass
  return argcomplete is not None


ARGCOMPLETE_AVAILABLE = _ArgcompleteAvailable()


def _NormalizeURI(uri):
  """Normalizes the path component of a URI.

  Args:
    uri: URI to normalize.

  Returns:
    Normalized URI.

  Examples:
    gs://foo//bar -> gs://foo/bar
    gs://foo/./bar -> gs://foo/bar
  """
  # Note: we have to do this dance of changing gs:// to file:// because on
  # Windows, the urlparse function won't work with URL schemes that are not
  # known. urlparse('gs://foo/bar') on Windows turns into:
  #     scheme='gs', netloc='', path='//foo/bar'
  # while on non-Windows platforms, it turns into:
  #     scheme='gs', netloc='foo', path='/bar'
  uri = uri.replace('gs://', 'file://')
  parsed = list(urllib.parse.urlparse(uri))
  parsed[2] = posixpath.normpath(parsed[2])
  if parsed[2].startswith('//'):
    # The normpath function doesn't change '//foo' -> '/foo' by design.
    parsed[2] = parsed[2][1:]
  unparsed = urllib.parse.urlunparse(parsed)
  unparsed = unparsed.replace('file://', 'gs://')
  return unparsed


def GenerationFromURI(uri):
  """Returns a the generation for a StorageUri.

  Args:
    uri: boto.storage_uri.StorageURI object to get the URI from.

  Returns:
    Generation string for the URI.
  """
  if not (uri.generation or uri.version_id):
    if uri.scheme == 's3':
      return 'null'
  return uri.generation or uri.version_id


def ObjectToURI(obj, *suffixes):
  """Returns the storage URI string for a given StorageUri or file object.

  Args:
    obj: The object to get the URI from. Can be a file object, a subclass of
         boto.storage_uri.StorageURI, or a string. If a string, it is assumed to
         be a local on-disk path.
    *suffixes: Suffixes to append. For example, ObjectToUri(bucketuri, 'foo')
               would return the URI for a key name 'foo' inside the given
               bucket.

  Returns:
    Storage URI string.
  """
  if is_file(obj):
    return 'file://{}'.format(os.path.abspath(os.path.join(obj.name,
                                                           *suffixes)))
  if isinstance(obj, six.string_types):
    return 'file://{}'.format(os.path.join(obj, *suffixes))
  uri = six.ensure_text(obj.uri)
  if suffixes:
    suffixes_list = [six.ensure_text(suffix) for suffix in suffixes]
    uri = _NormalizeURI('/'.join([uri] + suffixes_list))

  # Storage URIs shouldn't contain a trailing slash.
  if uri.endswith('/'):
    uri = uri[:-1]
  return uri


class GSMockConnection(mock_storage_service.MockConnection):

  def __init__(self, *args, **kwargs):
    kwargs['provider'] = 'gs'
    self.debug = 0
    super(GSMockConnection, self).__init__(*args, **kwargs)


mock_connection = GSMockConnection()


class GSMockBucketStorageUri(mock_storage_service.MockBucketStorageUri):

  def connect(self, access_key_id=None, secret_access_key=None):
    return mock_connection

  def compose(self, components, headers=None):
    """Dummy implementation to allow parallel uploads with tests."""
    return self.new_key()

  def get_location(self, headers=None):
    return 'US'

  def get_cors(self, headers=None):
    return boto.gs.cors.Cors()

  def get_encryption_config(self, headers=None):
    return boto.gs.encryptionconfig.EncryptionConfig()

  def get_lifecycle_config(self, headers=None):
    return None

  def get_website_config(self, headers=None):
    return None

  def get_versioning_config(self, headers=None):
    return None


TEST_BOTO_REMOVE_SECTION = 'TestRemoveSection'


def _SetBotoConfig(section, name, value, revert_list):
  """Sets boto configuration temporarily for testing.

  SetBotoConfigForTest should be called by tests instead of this function.
  This will ensure that the configuration is reverted to its original setting
  using _RevertBotoConfig.

  Args:
    section: Boto config section to set
    name: Boto config name to set
    value: Value to set
    revert_list: List for tracking configs to revert.
  """
  prev_value = boto.config.get(section, name, None)
  if not boto.config.has_section(section):
    revert_list.append((section, TEST_BOTO_REMOVE_SECTION, None))
    boto.config.add_section(section)
  revert_list.append((section, name, prev_value))
  if value is None:
    boto.config.remove_option(section, name)
  else:
    boto.config.set(section, name, value)


def _RevertBotoConfig(revert_list):
  """Reverts boto config modifications made by _SetBotoConfig.

  Args:
    revert_list: List of boto config modifications created by calls to
                 _SetBotoConfig.
  """
  sections_to_remove = []
  for section, name, value in revert_list:
    if value is None:
      if name == TEST_BOTO_REMOVE_SECTION:
        sections_to_remove.append(section)
      else:
        boto.config.remove_option(section, name)
    else:
      boto.config.set(section, name, value)
  for section in sections_to_remove:
    boto.config.remove_section(section)


def SequentialAndParallelTransfer(func):
  """Decorator for tests that perform file to object transfers, or vice versa.

  This forces the test to run once normally, and again with special boto
  config settings that will ensure that the test follows the parallel composite
  upload and/or sliced object download code paths.

  Args:
    func: Function to wrap.

  Returns:
    Wrapped function.
  """

  @functools.wraps(func)
  def Wrapper(*args, **kwargs):
    # Run the test normally once.
    func(*args, **kwargs)

    if not RUN_S3_TESTS and UsingCrcmodExtension():
      # Try again, forcing parallel upload and sliced download.
      with SetBotoConfigForTest([
          ('GSUtil', 'parallel_composite_upload_threshold', '1'),
          ('GSUtil', 'sliced_object_download_threshold', '1'),
          ('GSUtil', 'sliced_object_download_max_components', '3'),
          ('GSUtil', 'check_hashes', 'always')
      ]):
        func(*args, **kwargs)

  return Wrapper


def _SectionDictFromConfigList(boto_config_list):
  """Converts the input config list to a dict that is easy to write to a file.

  This is used to reset the boto config contents for a test instead of
  preserving the existing values.

  Args:
    boto_config_list: list of tuples of:
        (boto config section to set, boto config name to set, value to set)
        If value to set is None, no entry is created.

  Returns:
    Dictionary of {section: {keys: values}} for writing to the file.
  """
  sections = {}
  for config_entry in boto_config_list:
    section, key, value = (config_entry[0], config_entry[1], config_entry[2])
    if section not in sections:
      sections[section] = {}
    if value is not None:
      sections[section][key] = value

  return sections


def _WriteSectionDictToFile(section_dict, tmp_filename):
  """Writes a section dict from _SectionDictFromConfigList to tmp_filename."""
  with open(tmp_filename, 'w') as tmp_file:
    for section, key_value_pairs in six.iteritems(section_dict):
      tmp_file.write('[%s]\n' % section)
      for key, value in six.iteritems(key_value_pairs):
        tmp_file.write('%s = %s\n' % (key, value))


@contextmanager
def SetDummyProjectForUnitTest():
  """Sets a dummy project in boto config for the duration of a 'with' clause."""
  # Listing buckets requires a project ID, but unit tests should run
  # regardless of whether one is specified in config.
  with SetBotoConfigForTest([('GSUtil', 'default_project_id', 'dummy_proj')]):
    yield


@contextmanager
def SetBotoConfigForTest(boto_config_list, use_existing_config=True):
  """Sets the input list of boto configs for the duration of a 'with' clause.

  This preserves any existing boto configuration unless it is overwritten in
  the provided boto_config_list.

  Args:
    boto_config_list: list of tuples of:
        (boto config section to set, boto config name to set, value to set)
    use_existing_config: If True, apply boto_config_list to the existing
        configuration, preserving any original values unless they are
        overwritten. Otherwise, apply boto_config_list to a blank configuration.

  Yields:
    Once after config is set.
  """
  revert_configs = []
  tmp_filename = None
  try:
    tmp_fd, tmp_filename = tempfile.mkstemp(prefix='gsutil-temp-cfg')
    os.close(tmp_fd)
    if use_existing_config:
      for boto_config in boto_config_list:
        boto_value = boto_config[2]
        if six.PY3:
          if isinstance(boto_value, bytes):
            boto_value = boto_value.decode(UTF8)
        _SetBotoConfig(boto_config[0], boto_config[1], boto_value,
                       revert_configs)
      with open(tmp_filename, 'w') as tmp_file:
        boto.config.write(tmp_file)
    else:
      _WriteSectionDictToFile(_SectionDictFromConfigList(boto_config_list),
                              tmp_filename)

    with _SetBotoConfigFileForTest(tmp_filename):
      yield
  finally:
    _RevertBotoConfig(revert_configs)
    if tmp_filename:
      try:
        os.remove(tmp_filename)
      except OSError:
        pass


@contextmanager
def SetEnvironmentForTest(env_variable_dict):
  """Sets OS environment variables for a single test."""

  def _ApplyDictToEnvironment(dict_to_apply):
    for k, v in six.iteritems(dict_to_apply):
      old_values[k] = os.environ.get(k)
      if v is not None:
        os.environ[k] = v
      elif k in os.environ:
        del os.environ[k]

  old_values = {}
  for k in env_variable_dict:
    old_values[k] = os.environ.get(k)

  try:
    _ApplyDictToEnvironment(env_variable_dict)
    yield
  finally:
    _ApplyDictToEnvironment(old_values)


@contextmanager
def _SetBotoConfigFileForTest(boto_config_path):
  """Sets a given file as the boto config file for a single test.

  This function applies only the configuration in boto_config_path and will
  ignore existing configuration. It should not be called directly by tests;
  instead, use SetBotoConfigForTest.

  Args:
    boto_config_path: Path to config file to use.

  Yields:
    When configuration has been applied, and again when reverted.
  """
  # Setup for entering "with" block.
  try:
    old_boto_config_env_variable = os.environ['BOTO_CONFIG']
    boto_config_was_set = True
  except KeyError:
    boto_config_was_set = False
  os.environ['BOTO_CONFIG'] = boto_config_path

  try:
    yield
  finally:
    # Teardown for exiting "with" block.
    if boto_config_was_set:
      os.environ['BOTO_CONFIG'] = old_boto_config_env_variable
    else:
      os.environ.pop('BOTO_CONFIG', None)


def GetTestNames():
  """Returns a list of the names of the test modules in gslib.tests."""
  matcher = re.compile(r'^test_(?P<name>.*)$')
  names = []
  for _, modname, _ in pkgutil.iter_modules(gslib_tests.__path__):
    m = matcher.match(modname)
    if m:
      names.append(m.group('name'))
  return names


def is_file(obj):
  if six.PY2:
    return isinstance(obj, file)  # pylint: disable=undefined-variable
  return isinstance(obj, io.IOBase)


def MakeBucketNameValid(name):
  """Returns a copy of the given name with any invalid characters replaced.

  Args:
    name Union[str, unicode, bytes]: The bucket name to transform into a valid name.

  Returns:
    Union[str, unicode, bytes] The version of the bucket name containing only
      valid characters.
  """
  # Neither underscores nor uppercase letters are valid characters for a
  # bucket name. Replace those with hyphens and lowercase characters.
  if isinstance(name, (six.text_type, six.binary_type)):
    return name.replace('_', '-').lower()
  else:
    raise TypeError('Unable to format name. Incorrect Type: {0}'.format(
        type(name)))


@contextmanager
def WorkingDirectory(new_working_directory):
  """Changes the working directory for the duration of a 'with' call.

  Args:
    new_working_directory: The directory to switch to before executing wrapped
      code. A None value indicates that no switching is necessary.

  Yields:
    Once after working directory has been changed.
  """
  prev_working_directory = None
  try:
    prev_working_directory = os.getcwd()
  except OSError:
    # This can happen if the current working directory no longer exists.
    pass

  if new_working_directory:
    os.chdir(new_working_directory)

  try:
    yield
  finally:
    if new_working_directory and prev_working_directory:
      os.chdir(prev_working_directory)


def InvokedFromParFile():
  loader = globals().get('__loader__', None)
  if not loader:
    return False
  return 'zipimport' in loader.__class__.__module__


def SkipForParFile(reason):
  if InvokedFromParFile():
    return unittest.skip(reason)
  else:
    return lambda func: func


# Custom test callbacks must be pickleable, and therefore at global scope.
class HaltingCopyCallbackHandler(object):
  """Test callback handler for intentionally stopping a resumable transfer."""

  def __init__(self, is_upload, halt_at_byte):
    self._is_upload = is_upload
    self._halt_at_byte = halt_at_byte

  # pylint: disable=invalid-name
  def call(self, total_bytes_transferred, total_size):
    """Forcibly exits if the transfer has passed the halting point.

    Note that this function is only called when the conditions in
    gslib.progress_callback.ProgressCallbackWithTimeout.Progress are met, so
    self._halt_at_byte is only precise if it's divisible by
    gslib.progress_callback._START_BYTES_PER_CALLBACK.
    """
    if total_bytes_transferred >= self._halt_at_byte:
      sys.stderr.write(
          'Halting transfer after byte %s. %s/%s transferred.\r\n' %
          (self._halt_at_byte, MakeHumanReadable(total_bytes_transferred),
           MakeHumanReadable(total_size)))
      if self._is_upload:
        raise ResumableUploadException('Artifically halting upload.')
      else:
        raise ResumableDownloadException('Artifically halting download.')


class HaltOneComponentCopyCallbackHandler(object):
  """Test callback handler for stopping part of a sliced download."""

  def __init__(self, halt_at_byte):
    self._last_progress_byte = None
    self._halt_at_byte = halt_at_byte

  # pylint: disable=invalid-name
  # pylint: disable=unused-argument
  def call(self, current_progress_byte, total_size_unused):
    """Forcibly exits if the passed the halting point since the last call."""
    if (self._last_progress_byte is not None and
        self._last_progress_byte < self._halt_at_byte < current_progress_byte):
      sys.stderr.write('Halting transfer.\r\n')
      raise ResumableDownloadException('Artifically halting download.')
    self._last_progress_byte = current_progress_byte


class TestParams(object):
  """Allows easier organization of test parameters.

  This class allows grouping of test parameters, which include args and kwargs
  to be used, as well as the expected result based on those arguments.

  For example, to test an Add function, one might do:

  params = TestParams(args=(1, 2, 3), expected=6)
  self.assertEqual(Add(*(params.args)), params.expected)
  """

  def __init__(self, args=None, kwargs=None, expected=None):
    self.args = tuple() if args is None else args
    self.kwargs = dict() if kwargs is None else kwargs
    self.expected = expected

    if not isinstance(args, (tuple, list)):
      raise TypeError('TestParam args must be a tuple or list.')
    if not isinstance(self.kwargs, dict):
      raise TypeError('TestParam kwargs must be a dict.')


class CaptureStdout(list):
  """Context manager.

  For example, this function has the lines printed by the function call
  stored as a list in output:

  with CaptureStdout() as output:
    function(input_to_function)
  """

  def __enter__(self):
    self._stdout = sys.stdout
    sys.stdout = self._stringio = cStringIO()
    return self

  def __exit__(self, *args):
    self.extend(self._stringio.getvalue().splitlines())
    del self._stringio
    sys.stdout = self._stdout

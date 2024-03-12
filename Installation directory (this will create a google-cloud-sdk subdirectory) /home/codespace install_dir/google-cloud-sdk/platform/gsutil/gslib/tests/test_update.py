# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
"""Tests for the update command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os.path
import shutil
import subprocess
import sys
import tarfile

import boto
import gslib
from gslib.metrics import _UUID_FILE_PATH
import gslib.tests.testcase as testcase
from gslib.tests.util import ObjectToURI as suri
from gslib.tests.util import unittest
from gslib.utils import system_util
from gslib.utils.boto_util import CERTIFICATE_VALIDATION_ENABLED
from gslib.utils.constants import UTF8
from gslib.utils.update_util import DisallowUpdateIfDataInGsutilDir
from gslib.utils.update_util import GsutilPubTarball

from six import add_move, MovedModule

add_move(MovedModule('mock', 'mock', 'unittest.mock'))
from six.moves import mock

TESTS_DIR = os.path.abspath(os.path.dirname(__file__))
GSUTIL_DIR = os.path.join(TESTS_DIR, '..', '..')


class UpdateTest(testcase.GsUtilIntegrationTestCase):
  """Update command test suite."""

  @unittest.skipUnless(CERTIFICATE_VALIDATION_ENABLED,
                       'Test requires https certificate validation enabled.')
  def test_update(self):
    """Tests that the update command works or raises proper exceptions."""
    if system_util.InvokedViaCloudSdk():
      stderr = self.RunGsUtil(['update'],
                              stdin='n',
                              return_stderr=True,
                              expected_status=1)
      self.assertIn('update command is disabled for Cloud SDK', stderr)
      return

    if gslib.IS_PACKAGE_INSTALL:
      # The update command is not present when installed via package manager.
      stderr = self.RunGsUtil(['update'], return_stderr=True, expected_status=1)
      self.assertIn('Invalid command', stderr)
      return

    # Create two temp directories, one of which we will run 'gsutil update' in
    # to pull the changes from the other.
    tmpdir_src = self.CreateTempDir()
    tmpdir_dst = self.CreateTempDir()

    # Copy gsutil to both source and destination directories.
    gsutil_src = os.path.join(tmpdir_src, 'gsutil')
    gsutil_dst = os.path.join(tmpdir_dst, 'gsutil')
    # Path when executing from tmpdir (Windows doesn't support in-place rename)
    gsutil_relative_dst = os.path.join('gsutil', 'gsutil')

    ignore_callable = shutil.ignore_patterns(
        '.git*',
        '*.pyc',
        '*.pyo',
        '__pycache__',
    )
    shutil.copytree(GSUTIL_DIR, gsutil_src, ignore=ignore_callable)
    # Copy specific files rather than all of GSUTIL_DIR so we don't pick up temp
    # working files left in top-level directory by gsutil developers (like tags,
    # .git*, .pyc files, etc.)
    os.makedirs(gsutil_dst)
    for comp in os.listdir(GSUTIL_DIR):
      if ('.git' not in comp and
          '__pycache__' not in comp and
           not comp.endswith('.pyc') and
           not comp.endswith('.pyo')):  # yapf: disable
        cp_src_path = os.path.join(GSUTIL_DIR, comp)
        cp_dst_path = os.path.join(gsutil_dst, comp)
        if os.path.isdir(cp_src_path):
          shutil.copytree(cp_src_path, cp_dst_path, ignore=ignore_callable)
        else:
          shutil.copyfile(cp_src_path, cp_dst_path)

    # Create a fake version number in the source so we can verify it in the
    # destination.
    expected_version = '17.25'
    src_version_file = os.path.join(gsutil_src, 'VERSION')
    self.assertTrue(os.path.exists(src_version_file))
    with open(src_version_file, 'w') as f:
      f.write(expected_version)

    # Create a tarball out of the source directory and copy it to a bucket.
    src_tarball = os.path.join(tmpdir_src, 'gsutil.test.tar.gz')

    normpath = os.path.normpath
    try:
      # We monkey patch os.path.normpath here because the tarfile module
      # normalizes the ./gsutil path, but the update command expects the tar
      # file to be prefixed with . This preserves the ./gsutil path.
      os.path.normpath = lambda fname: fname
      tar = tarfile.open(src_tarball, 'w:gz')
      tar.add(gsutil_src, arcname='./gsutil')
      tar.close()
    finally:
      os.path.normpath = normpath

    prefix = [sys.executable] if sys.executable else []

    # Run with an invalid gs:// URI.
    p = subprocess.Popen(prefix + ['gsutil', 'update', 'gs://pub'],
                         cwd=gsutil_dst,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    (_, stderr) = p.communicate()
    p.stdout.close()
    p.stderr.close()
    self.assertEqual(p.returncode, 1)
    self.assertIn(b'update command only works with tar.gz', stderr)

    # Run with non-existent gs:// URI.
    p = subprocess.Popen(prefix +
                         ['gsutil', 'update', 'gs://pub/Jdjh38)(;.tar.gz'],
                         cwd=gsutil_dst,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    (_, stderr) = p.communicate()
    p.stdout.close()
    p.stderr.close()
    self.assertEqual(p.returncode, 1)
    self.assertIn(b'NotFoundException', stderr)

    # Run with file:// URI wihout -f option.
    p = subprocess.Popen(
        prefix + ['gsutil', 'update', suri(src_tarball)],
        cwd=gsutil_dst,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)
    (_, stderr) = p.communicate()
    p.stdout.close()
    p.stderr.close()
    self.assertEqual(p.returncode, 1)
    self.assertIn(b'command does not support', stderr)

    # Run with a file present that was not distributed with gsutil.
    with open(os.path.join(gsutil_dst, 'userdata.txt'), 'w') as fp:
      fp.write('important data\n')
    p = subprocess.Popen(
        prefix +
        ['gsutil', 'update', '-f', suri(src_tarball)],
        cwd=gsutil_dst,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE)
    (_, stderr) = p.communicate()
    p.stdout.close()
    p.stderr.close()
    # Clean up before next test, and before assertions so failure doesn't leave
    # this file around.
    os.unlink(os.path.join(gsutil_dst, 'userdata.txt'))
    self.assertEqual(p.returncode, 1)
    # Additional check for Windows since it has \r\n and string may have just \n
    os_ls = os.linesep.encode(UTF8)
    if os_ls in stderr:
      stderr = stderr.replace(os_ls, b' ')
    elif b'\n' in stderr:
      stderr = stderr.replace(b'\n', b' ')
    self.assertIn(
        b'The update command cannot run with user data in the gsutil directory',
        stderr)

    # Determine whether we'll need to decline the analytics prompt.
    analytics_prompt = not (os.path.exists(_UUID_FILE_PATH) or
                            boto.config.get_value('GSUtil',
                                                  'disable_analytics_prompt'))

    update_input = b'n\r\ny\r\n' if analytics_prompt else b'y\r\n'

    # Now do the real update, which should succeed.
    p = subprocess.Popen(
        prefix + [gsutil_relative_dst, 'update', '-f',
                  suri(src_tarball)],
        cwd=tmpdir_dst,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE)
    (_, stderr) = p.communicate(input=update_input)
    p.stdout.close()
    p.stderr.close()
    self.assertEqual(
        p.returncode,
        0,
        msg=('Non-zero return code (%d) from gsutil update. stderr = \n%s' %
             (p.returncode, stderr.decode(UTF8))))

    # Verify that version file was updated.
    dst_version_file = os.path.join(tmpdir_dst, 'gsutil', 'VERSION')
    with open(dst_version_file, 'r') as f:
      self.assertEqual(f.read(), expected_version)

    # If the analytics prompt was given, that means we disabled analytics. We
    # should reset to the default by deleting the UUID file.
    if analytics_prompt:
      os.unlink(_UUID_FILE_PATH)


class UpdateUnitTest(testcase.GsUtilUnitTestCase):
  """Tests the functionality of commands/update.py."""

  @unittest.skipUnless(
      not gslib.IS_PACKAGE_INSTALL,
      'Test is runnable only if gsutil dir is accessible, and update '
      'command is not valid for package installs.')
  def test_repo_matches_manifest(self):
    """Ensure that all files/folders match the manifest."""
    # Create a temp directory and copy specific files to it.
    tmpdir_src = self.CreateTempDir()
    gsutil_src = os.path.join(tmpdir_src, 'gsutil')
    os.makedirs(gsutil_src)
    copy_files = []
    for filename in os.listdir(GSUTIL_DIR):
      if (filename.endswith('.pyc') or filename.startswith('.git') or
          filename == '__pycache__' or filename == '.settings' or
          filename == '.project' or filename == '.pydevproject' or
          filename == '.style.yapf' or filename == '.yapfignore'):
        # Need to ignore any compiled code or Eclipse project folders.
        continue
      copy_files.append(filename)
    for comp in copy_files:
      if os.path.isdir(os.path.join(GSUTIL_DIR, comp)):
        func = shutil.copytree
      else:
        func = shutil.copyfile
      func(os.path.join(GSUTIL_DIR, comp), os.path.join(gsutil_src, comp))
    DisallowUpdateIfDataInGsutilDir(directory=gsutil_src)

  def test_pub_tarball(self):
    """Ensure that the correct URI is returned based on the Python version."""
    with mock.patch.object(sys, 'version_info') as version_info:
      version_info.major = 3
      self.assertIn('gsutil.tar.gz', GsutilPubTarball())
      version_info.major = 2
      self.assertIn('gsutil4.tar.gz', GsutilPubTarball())
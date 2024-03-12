# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
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
"""Implementation of gsutil version command."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import platform
import re
import sys

import six
import boto
import crcmod
import gslib
from gslib.command import Command
from gslib.utils import system_util
from gslib.utils.boto_util import GetFriendlyConfigFilePaths
from gslib.utils.boto_util import UsingCrcmodExtension
from gslib.utils.constants import UTF8
from gslib.utils.hashing_helper import GetMd5
from gslib.utils.parallelism_framework_util import CheckMultiprocessingAvailableAndInit

_SYNOPSIS = """
  gsutil version
"""

_DETAILED_HELP_TEXT = ("""
<B>SYNOPSIS</B>
""" + _SYNOPSIS + """


<B>DESCRIPTION</B>
  Prints information about the version of gsutil.

<B>OPTIONS</B>
  -l          Prints additional information, such as the version of Python
              being used, the version of the Boto library, a checksum of the
              code, the path to gsutil, and the path to gsutil's configuration
              file.
""")


class VersionCommand(Command):
  """Implementation of gsutil version command."""

  # Command specification. See base class for documentation.
  command_spec = Command.CreateCommandSpec(
      'version',
      command_name_aliases=['ver'],
      usage_synopsis=_SYNOPSIS,
      min_args=0,
      max_args=0,
      supported_sub_args='l',
      file_url_ok=False,
      provider_url_ok=False,
      urls_start_arg=0,
  )
  # Help specification. See help_provider.py for documentation.
  help_spec = Command.HelpSpec(
      help_name='version',
      help_name_aliases=['ver'],
      help_type='command_help',
      help_one_line_summary='Print version info about gsutil',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )

  def RunCommand(self):
    """Command entry point for the version command."""
    long_form = False
    if self.sub_opts:
      for o, _ in self.sub_opts:
        if o == '-l':
          long_form = True

    config_paths = ', '.join(GetFriendlyConfigFilePaths())

    shipped_checksum = gslib.CHECKSUM
    try:
      cur_checksum = self._ComputeCodeChecksum()
    except IOError:
      cur_checksum = 'MISSING FILES'
    if shipped_checksum == cur_checksum:
      checksum_ok_str = 'OK'
    else:
      checksum_ok_str = '!= %s' % shipped_checksum

    sys.stdout.write('gsutil version: %s\n' % gslib.VERSION)

    if long_form:

      long_form_output = (
          'checksum: {checksum} ({checksum_ok})\n'
          'boto version: {boto_version}\n'
          'python version: {python_version}\n'
          'OS: {os_version}\n'
          'multiprocessing available: {multiprocessing_available}\n'
          'using cloud sdk: {cloud_sdk}\n'
          'pass cloud sdk credentials to gsutil: {cloud_sdk_credentials}\n'
          'config path(s): {config_paths}\n'
          'gsutil path: {gsutil_path}\n'
          'compiled crcmod: {compiled_crcmod}\n'
          'installed via package manager: {is_package_install}\n'
          'editable install: {is_editable_install}\n'
          'shim enabled: {is_shim_enabled}\n')

      sys.stdout.write(
          long_form_output.format(
              checksum=cur_checksum,
              checksum_ok=checksum_ok_str,
              boto_version=boto.__version__,
              python_version=sys.version.replace('\n', ''),
              os_version='%s %s' % (platform.system(), platform.release()),
              multiprocessing_available=(
                  CheckMultiprocessingAvailableAndInit().is_available),
              cloud_sdk=system_util.InvokedViaCloudSdk(),
              cloud_sdk_credentials=system_util.CloudSdkCredPassingEnabled(),
              config_paths=config_paths,
              gsutil_path=(GetCloudSdkGsutilWrapperScriptPath() or
                           gslib.GSUTIL_PATH),
              compiled_crcmod=UsingCrcmodExtension(),
              is_package_install=gslib.IS_PACKAGE_INSTALL,
              is_editable_install=gslib.IS_EDITABLE_INSTALL,
              is_shim_enabled=boto.config.getbool('GSUtil',
                                                  'use_gcloud_storage', False)))

    return 0

  def _ComputeCodeChecksum(self):
    """Computes a checksum of gsutil code.

    This checksum can be used to determine if users locally modified
    gsutil when requesting support. (It's fine for users to make local mods,
    but when users ask for support we ask them to run a stock version of
    gsutil so we can reduce possible variables.)

    Returns:
      MD5 checksum of gsutil code.
    """
    if gslib.IS_PACKAGE_INSTALL:
      return 'PACKAGED_GSUTIL_INSTALLS_DO_NOT_HAVE_CHECKSUMS'
    m = GetMd5()
    # Checksum gsutil and all .py files under gslib directory.
    files_to_checksum = [gslib.GSUTIL_PATH]
    for root, _, files in os.walk(gslib.GSLIB_DIR):
      for filepath in files:
        if filepath.endswith('.py'):
          files_to_checksum.append(os.path.join(root, filepath))
    # Sort to ensure consistent checksum build, no matter how os.walk
    # orders the list.
    for filepath in sorted(files_to_checksum):
      if six.PY2:
        f = open(filepath, 'rb')
        content = f.read()
        content = re.sub(r'(\r\n|\r|\n)', b'\n', content)
        m.update(content)
        f.close()
      else:
        f = open(filepath, 'r', encoding=UTF8)
        content = f.read()
        content = re.sub(r'(\r\n|\r|\n)', '\n', content)
        m.update(content.encode(UTF8))
        f.close()
    return m.hexdigest()


def GetCloudSdkGsutilWrapperScriptPath():
  """If gsutil was invoked via the Cloud SDK, find its gsutil wrapper script.

  Returns:
    (str) The path to the Cloud SDK's gsutil wrapper script, or an empty string
    if gsutil was not invoked via the Cloud SDK or the wrapper script could not
    be found at its expected path.
  """
  # If running via the Cloud SDK, the "real" gsutil script was probably invoked
  # indirectly through gcloud's gsutil wrapper script (the former is at
  # <sdk-root>/platform/gsutil/gsutil, while the latter is located at
  # <sdk-root>/bin/gsutil). We should print the wrapper script's path if it
  # exists and we were invoked via the Cloud SDK.
  gsutil_path = gslib.GSUTIL_PATH
  if system_util.InvokedViaCloudSdk():
    platform_path_suffix = os.path.join('platform', 'gsutil', 'gsutil')
    if gsutil_path.endswith(platform_path_suffix):
      bin_path = os.path.join(
          gsutil_path[0:gsutil_path.rfind(platform_path_suffix)],
          'bin',
          'gsutil',
      )
      if os.path.exists(bin_path):
        return bin_path

  return ''

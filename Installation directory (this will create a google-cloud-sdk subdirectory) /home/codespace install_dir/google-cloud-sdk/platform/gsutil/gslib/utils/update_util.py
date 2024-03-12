# -*- coding: utf-8 -*-
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Shared utility methods for the update command and its tests."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import logging
import os
import re
import textwrap
import sys

import gslib
from gslib.utils.system_util import IS_OSX
from gslib.exception import CommandException
from gslib.storage_url import StorageUrlFromString
from gslib.utils.constants import GSUTIL_PUB_TARBALL
from gslib.utils.constants import GSUTIL_PUB_TARBALL_PY2


# This function used to belong inside of update.py. However, it needed to be
# moved here due to compatibility issues with Travis CI, because update.py is
# not included with PyPI installations.
def DisallowUpdateIfDataInGsutilDir(directory=gslib.GSUTIL_DIR):
  """Disallows the update command if files not in the gsutil distro are found.

  This prevents users from losing data if they are in the habit of running
  gsutil from the gsutil directory and leaving data in that directory.

  This will also detect someone attempting to run gsutil update from a git
  repo, since the top-level directory will contain git files and dirs (like
  .git) that are not distributed with gsutil.

  Args:
    directory: (str) The directory to use this functionality on.

  Raises:
    CommandException: if files other than those distributed with gsutil found.
  """
  # Manifest includes recursive-includes of gslib. Directly add
  # those to the list here so we will skip them in os.listdir() loop without
  # having to build deeper handling of the MANIFEST file here. Also include
  # 'third_party', which isn't present in manifest but gets added to the
  # gsutil distro by the gsutil submodule configuration; and the MANIFEST.in
  # and CHANGES.md files.
  manifest_lines = ['MANIFEST.in', 'third_party']

  try:
    with open(os.path.join(directory, 'MANIFEST.in'), 'r') as fp:
      for line in fp:
        if line.startswith('include '):
          manifest_lines.append(line.split()[-1])
        elif re.match(r'recursive-include \w+ \*', line):
          manifest_lines.append(line.split()[1])
  except IOError:
    logging.getLogger().warn(
        'MANIFEST.in not found in %s.\nSkipping user data '
        'check.\n', directory)
    return

  # Look just at top-level directory. We don't try to catch data dropped into
  # subdirs (like gslib) because that would require deeper parsing of
  # MANFFEST.in, and most users who drop data into gsutil dir do so at the top
  # level directory.
  addl_excludes = (
      '.coverage',
      '.DS_Store',
      '.github',
      '.style.yapf',
      '.yapfignore',
      '__pycache__',
      '.github',
  )
  for filename in os.listdir(directory):
    if filename.endswith('.pyc') or filename in addl_excludes:
      continue
    if filename not in manifest_lines:
      raise CommandException('\n'.join(
          textwrap.wrap(
              'A file (%s) that is not distributed with gsutil was found in '
              'the gsutil directory. The update command cannot run with user '
              'data in the gsutil directory.' %
              os.path.join(gslib.GSUTIL_DIR, filename))))


def LookUpGsutilVersion(gsutil_api, url_str):
  """Looks up the gsutil version of the specified gsutil tarball URL.

  Version is specified in the metadata field set on that object.

  Args:
    gsutil_api: gsutil Cloud API to use when retrieving gsutil tarball.
    url_str: tarball URL to retrieve (such as 'gs://pub/gsutil.tar.gz').

  Returns:
    Version string if URL is a cloud URL containing x-goog-meta-gsutil-version
    metadata, else None.
  """
  url = StorageUrlFromString(url_str)
  if url.IsCloudUrl():
    obj = gsutil_api.GetObjectMetadata(url.bucket_name,
                                       url.object_name,
                                       provider=url.scheme,
                                       fields=['metadata'])
    if obj.metadata and obj.metadata.additionalProperties:
      for prop in obj.metadata.additionalProperties:
        if prop.key == 'gsutil_version':
          return prop.value


def GsutilPubTarball():
  """Returns the appropriate gsutil pub tarball based on the Python version.

  Returns:
    The storage_uri of the appropriate pub tarball.
  """
  if sys.version_info.major == 2:
    return GSUTIL_PUB_TARBALL_PY2
  return GSUTIL_PUB_TARBALL

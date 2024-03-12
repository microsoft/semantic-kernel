# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Contains utilities for comparing RELEASE_NOTES between Cloud SDK versions.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core.document_renderers import render_document
from googlecloudsdk.core.updater import installers

import requests
from six.moves import StringIO


class ReleaseNotes(object):
  """Represents a parsed RELEASE_NOTES file.

  The file should have the general structure of:

  # Google Cloud SDK - Release Notes

  Copyright 2014-2015 Google LLC. All rights reserved.

  ## 0.9.78 (2015/09/16)

  *   Note
  *   Note 2

  ## 0.9.77 (2015/09/09)

  *   Note 3
  """

  # This regex matches each version section in the release notes file.
  # It uses lookaheads and lookbehinds to be able to ensure double newlines
  # without consuming them (because they are needed as part of the match of the
  # next version section.  This translates to a line starting with '##' preceded
  # by a blank line that has a version string and description.  It then consumes
  # all lines until it hits a newline that is not followed by a blank line and
  # another line starting with '##"
  _VERSION_SPLIT_REGEX = (
      r'(?<=\n)\n## +(?P<version>\S+).*\n(?:\n.*(?!\n\n## ))+.')

  MAX_DIFF = 15

  @classmethod
  def FromURL(cls, url, command_path=None):
    """Parses release notes from the given URL using the requests library.

    Any error in downloading or parsing release notes is logged and swallowed
    and None is returned.

    Args:
      url: str, The URL to download and parse.
      command_path: str, The command that is calling this for instrumenting the
        user agent for the download.

    Returns:
      ReleaseNotes, the parsed release notes or None if an error occurred.
    """
    try:
      response = installers.MakeRequest(url, command_path)
      if response is None:
        return None
      code = response.status_code
      if code != requests.codes.ok:
        return None
      return cls(response.text)
    # pylint: disable=broad-except, We don't want any failure to download or
    # parse the release notes to block an update.  Returning None here will
    # print a generic message of where the user can go to view the release
    # notes online.
    except Exception:
      log.debug('Failed to download [{url}]'.format(url=url), exc_info=True)
    return None

  def __init__(self, text):
    """Parse the release notes from the given text.

    Args:
      text: str, The text of the release notes to parse.

    Returns:
      ReleaseNotes, the parsed release notes.
    """
    self._text = text.replace('\r\n', '\n')

    versions = []

    for m in re.finditer(ReleaseNotes._VERSION_SPLIT_REGEX, self._text):
      versions.append((m.group('version'), m.group().strip()))

    # [(version string, full version text including header), ...]
    self._versions = versions

  def GetVersionText(self, version):
    """Gets the release notes text for the given version.

    Args:
      version: str, The version to get the release notes for.

    Returns:
      str, The release notes or None if the version does not exist.
    """
    index = self._GetVersionIndex(version)
    if index is None:
      return None
    return self._versions[index][1]

  def _GetVersionIndex(self, version):
    """Gets the index of the given version in the list of parsed versions.

    Args:
      version: str, The version to get the index for.

    Returns:
      int, The index of the given version or None if not found.
    """
    for i, (v, _) in enumerate(self._versions):
      if v == version:
        return i
    return None

  def Diff(self, start_version, end_version):
    """Creates a diff of the release notes between the two versions.

    The release notes are returned in reversed order (most recent first).

    Args:
      start_version: str, The version at which to start the diff.  This should
        be the later of the two versions.  The diff will start with this version
        and go backwards in time until end_version is hit.  If None, the diff
        will start at the most recent entry.
      end_version: str, The version at which to stop the diff.  This should be
        the version you are currently on.  The diff is accumulated until this
        version it hit.  This version is not included in the diff.  If None,
        the diff will include through the end of all release notes.

    Returns:
      [(version, text)], The list of release notes in the diff from most recent
      to least recent.  Each item is a tuple of the version string and the
      release notes text for that version.  Returns None if either of the
      versions are not present in the release notes.
    """
    if start_version:
      start_index = self._GetVersionIndex(start_version)
      if start_index is None:
        return None
    else:
      start_index = 0

    if end_version:
      end_index = self._GetVersionIndex(end_version)
      if end_index is None:
        return None
    else:
      end_index = len(self._versions)

    return self._versions[start_index:end_index]


def PrintReleaseNotesDiff(release_notes_url, current_version, latest_version):
  """Prints the release notes diff based on your current version.

  If any of the arguments are None, a generic message will be printed telling
  the user to go to the web to view the release notes.  If the release_notes_url
  is also None, it will print the developers site page for the SDK.

  Args:
    release_notes_url: str, The URL to download the latest release notes from.
    current_version: str, The current version of the SDK you have installed.
    latest_version: str, The version you are about to update to.
  """
  if release_notes_url and current_version and latest_version:
    notes = ReleaseNotes.FromURL(release_notes_url)
    if notes:
      release_notes_diff = notes.Diff(latest_version, current_version)
    else:
      release_notes_diff = None
  else:
    release_notes_diff = None

  if not release_notes_diff:
    # We failed to print the release notes.  Send people to a nice web page with
    # the release notes.
    log.status.write(
        'For the latest full release notes, please visit:\n  {0}\n\n'.format(
            config.INSTALLATION_CONFIG.release_notes_url))
    return

  if len(release_notes_diff) > ReleaseNotes.MAX_DIFF:
    log.status.Print("""\
A lot has changed since your last upgrade.  For the latest full release notes,
please visit:
  {0}
""".format(config.INSTALLATION_CONFIG.release_notes_url))
    return

  log.status.Print("""\
The following release notes are new in this upgrade.
Please read carefully for information about new features, breaking changes,
and bugs fixed.  The latest full release notes can be viewed at:
  {0}
""".format(config.INSTALLATION_CONFIG.release_notes_url))

  full_text = StringIO()
  for _, text in release_notes_diff:
    full_text.write(text)
    full_text.write('\n')

  full_text.seek(0)
  render_document.RenderDocument('text', full_text, log.status)
  log.status.Print()

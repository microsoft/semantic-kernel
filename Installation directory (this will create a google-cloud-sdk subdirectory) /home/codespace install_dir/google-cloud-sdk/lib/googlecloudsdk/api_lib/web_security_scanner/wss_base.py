# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Base classes for abstracting away common logic for web security scanner."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis


class WebSecurityScannerApiVersion(object):
  """An enum representing the API version of Web Security Scanner.

  The WebSecurityScanner API version controls which version of WSS API to use
  for a certain command under certain release track.
  """

  class _VERSION(object):
    """An enum representing the API version of Web Security Manager."""

    # pylint: disable=redefined-builtin
    def __init__(self, id, help_tag, help_note):
      self.id = id
      self.help_tag = help_tag
      self.help_note = help_note

    def __str__(self):
      return self.id

    def __eq__(self, other):
      return self.id == other.id

  V1BETA = _VERSION('v1beta', None, None)

  _ALL = (V1BETA)


class WebSecurityScannerCommand(object):
  """WebSecurityScannerCommand is a base class for web security scanner commands."""

  _version = WebSecurityScannerApiVersion.V1BETA
  _client = None
  _messages = None

  def __init__(self):
    pass

  @property
  def client(self):
    """Specifies the WebSecurityScanner client."""
    if self._client is None:
      self._client = apis.GetClientInstance('websecurityscanner',
                                            self._version.id)
    return self._client

  @property
  def messages(self):
    """Specifies the WebSecurityScanner messages."""
    if self._messages is None:
      self._messages = apis.GetMessagesModule('websecurityscanner',
                                              self._version.id)
    return self._messages


def UseWebSecurityScannerApi(api_version):
  """Mark this command class to use given Web Security Scanner API version.

  Args:
    api_version: Web Security Scanner API version to use for the command

  Returns:
    The decorator function
  """

  def InitApiHolder(cmd_class):
    """Wrapper function for the decorator."""
    # pylint: disable=protected-access
    cmd_class._wss_version = api_version
    return cmd_class

  return InitApiHolder

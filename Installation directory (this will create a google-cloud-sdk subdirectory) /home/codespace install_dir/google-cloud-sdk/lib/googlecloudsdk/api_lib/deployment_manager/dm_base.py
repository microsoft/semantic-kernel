# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Base classes for abstracting away common logic for Deployment Manager."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class DmApiVersion(object):
  """An enum representing the API version of Deployment Manager.

  The DM API version controls which version of DM API to use for a certain
  command under certain release track.
  """

  class _VERSION(object):
    """An enum representing the API version of Deployment Manager."""

    # pylint: disable=redefined-builtin
    def __init__(self, id, help_tag, help_note):
      self.id = id
      self.help_tag = help_tag
      self.help_note = help_note

    def __str__(self):
      return self.id

    def __eq__(self, other):
      return self.id == other.id

  V2 = _VERSION('v2', None, None)

  ALPHA = _VERSION(
      'alpha',
      '{0}(ALPHA){0} '.format('*'),
      'The DM API currently used is ALPHA and may change without notice.')

  V2BETA = _VERSION(
      'v2beta',
      '{0}(V2BETA){0} '.format('*'),
      'The DM API currently used is V2BETA and may change without notice.')

  _ALL = (V2, ALPHA, V2BETA)


class DmCommand(object):
  """DmCommand is a base class for Deployment Manager commands."""

  _dm_version = DmApiVersion.V2
  _dm_client = None
  _dm_messages = None
  _dm_resources = None

  def __init__(self):
    pass

  @property
  def version(self):
    return self._dm_version

  @property
  def client(self):
    """Specifies the DM client."""
    if self._dm_client is None:
      self._dm_client = apis.GetClientInstance('deploymentmanager',
                                               self._dm_version.id)
    return self._dm_client

  @property
  def messages(self):
    """Specifies the DM messages."""
    if self._dm_messages is None:
      self._dm_messages = apis.GetMessagesModule('deploymentmanager',
                                                 self._dm_version.id)
    return self._dm_messages

  @property
  def resources(self):
    """Specifies the resources parser for DM resources."""
    if self._dm_resources is None:
      self._dm_resources = resources.REGISTRY.Clone()
      self._dm_resources.RegisterApiByName('deploymentmanager',
                                           self._dm_version.id)
    return self._dm_resources


def UseDmApi(api_version):
  """Mark this command class to use given Deployment Manager API version.

  Args:
    api_version: DM API version to use for the command

  Returns:
    The decorator function
  """
  def InitApiHolder(cmd_class):
    """Wrapper function for the decorator."""
    # pylint: disable=protected-access
    cmd_class._dm_version = api_version
    return cmd_class
  return InitApiHolder


def GetProject():
  return properties.VALUES.core.project.Get(required=True)

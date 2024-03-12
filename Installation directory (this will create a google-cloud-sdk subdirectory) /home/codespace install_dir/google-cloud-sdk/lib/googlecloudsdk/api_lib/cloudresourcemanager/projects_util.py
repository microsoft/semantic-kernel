# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Util for projects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis

_API_NAME = 'cloudresourcemanager'
DEFAULT_API_VERSION = 'v1'


class DeletedResource(object):
  """A deleted/undeleted resource returned by Run()."""

  def __init__(self, project_id):
    self.projectId = project_id  # pylint: disable=invalid-name, This is a resource attribute name.


def GetMessages(version=DEFAULT_API_VERSION):
  """Import and return the appropriate projects messages module.

  Args:
    version: the API version

  Returns:
    Cloud Resource Manager message.
  """
  return apis.GetMessagesModule(_API_NAME, version)


def GetClient(version=DEFAULT_API_VERSION):
  """Import and return the appropriate projects client.

  Args:
    version: the API version

  Returns:
    Cloud Resource Manager client for the appropriate release track.
  """
  return apis.GetClientInstance(_API_NAME, version)


def IsActive(project):
  """Returns true if the project's lifecycle state is 'active'.

  Args:
    project: A Project
  Returns:
    True if the Project's lifecycle state is 'active,' else False.
  """
  lifecycle_enum = GetMessages().Project.LifecycleStateValueValuesEnum
  return project.lifecycleState == lifecycle_enum.ACTIVE

# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""SourceRepo APIs layer.

Parse methods accepts strings from command-line arguments, and it can accept
more formats like "https://...". Get methods are strict about the arguments.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis

_API_NAME = 'sourcerepo'
_API_VERSION = 'v1'


class ProjectConfig(object):
  """Base class for source project config api wrappers."""

  def __init__(self):
    self._client = apis.GetClientInstance(_API_NAME, _API_VERSION)
    self.messages = apis.GetMessagesModule(_API_NAME, _API_VERSION)

  def Get(self, project_ref):
    """Get a project configuration."""
    req = self.messages.SourcerepoProjectsGetConfigRequest(
        name=project_ref.RelativeName())
    return self._client.projects.GetConfig(req)

  def Update(self, project_config, update_mask):
    """Update a project configuration."""
    req = self.messages.SourcerepoProjectsUpdateConfigRequest(
        name=project_config.name,
        updateProjectConfigRequest=self.messages.UpdateProjectConfigRequest(
            projectConfig=project_config, updateMask=update_mask))
    return self._client.projects.UpdateConfig(req)

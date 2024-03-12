# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Functions that directly interact with Cloud Run."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.console import console_io


class ServiceAlreadyExistsError(exceptions.Error):
  """Error thrown if the service already exists and overwrite denied.
  """


class _ServiceResource:

  def __init__(self, project, service_name):
    self.project = project
    self.service_name = service_name

  def RelativeName(self):
    return 'namespaces/{}/services/{}'.format(self.project, self.service_name)


def ServiceExists(args, project, service_name, region, release_track):
  """Check to see if the service with the given name already exists."""
  context = connection_context.GetConnectionContext(
      args,
      release_track=release_track,
      platform=platforms.PLATFORM_MANAGED,
      region_label=region,
  )
  with serverless_operations.Connect(context) as client:
    return client.GetService(_ServiceResource(project, service_name))


def PromptToOverwriteCloud(args, settings, release_track):
  """If the service already exists, prompt the user before overwriting."""
  if ServiceExists(
      args,
      settings.project,
      settings.service_name,
      settings.region,
      release_track,
  ):
    if console_io.CanPrompt() and console_io.PromptContinue(
        message='Serivce {} already exists in project {}'.format(
            settings.service_name, settings.project
        ),
        prompt_string='Do you want to overwrite it?',
    ):
      return
    raise ServiceAlreadyExistsError('Service already exists.')

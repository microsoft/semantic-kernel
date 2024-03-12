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
"""A library that is used to support trace commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def GetClient():
  """Returns the client for the trace API."""
  return core_apis.GetClientInstance('cloudtrace', 'v2beta1')


def GetMessages():
  """Returns the messages for the trace API."""
  return core_apis.GetMessagesModule('cloudtrace', 'v2beta1')


def GetProjectNumber(project):
  project_id = project or properties.VALUES.core.project.Get(required=True)
  return projects_api.Get(projects_util.ParseProject(project_id)).projectNumber


def GetTraceSinkResource(sink_name, project):
  """Returns the appropriate sink resource based on args."""
  return resources.REGISTRY.Parse(
      sink_name,
      params={'projectsId': GetProjectNumber(project)},
      collection='cloudtrace.projects.traceSinks')


def GetProjectResource(project):
  """Returns the resource for the current project."""
  return resources.REGISTRY.Parse(
      project or properties.VALUES.core.project.Get(required=True),
      collection='cloudresourcemanager.projects')


def FormatTraceSink(sink):
  sink_name_tokens = sink.name.split('/')
  sink_name = ''
  if len(sink_name_tokens) > 3:
    sink_name = sink_name_tokens[3]

  return {
      'name': sink_name,
      'destination': sink.outputConfig.destination,
      'writer_identity': sink.writerIdentity
  }

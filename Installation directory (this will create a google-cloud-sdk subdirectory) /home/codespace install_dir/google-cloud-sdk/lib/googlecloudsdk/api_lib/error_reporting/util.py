# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Crash Reporting for Cloud SDK."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


API_VERSION = 'v1beta1'
API_NAME = 'clouderrorreporting'


class ErrorReporting(object):
  """Report errors to errorreporting."""

  def __init__(self, api_client=None):
    self.api_client = api_client
    if self.api_client is None:
      self.api_client = core_apis.GetClientInstance(API_NAME, API_VERSION)
    self.api_messages = self.api_client.MESSAGES_MODULE

  def ReportEvent(self, error_message, service, version=None,
                  project=None, request_url=None, user=None):
    """Creates a new error event and sends to StackDriver Reporting API.

    Args:
      error_message: str, Crash details including stacktrace
      service: str, Name of service
      version: str, Service version, defaults to None
      project: str, Project to report errors to, defaults to current
      request_url: str, The request url that led to the error
      user: str, The user affected by the error
    """
    self.api_client.projects_events.Report(self.GenerateReportRequest(
        error_message, service, version=version, project=project,
        request_url=request_url, user=user))

  def GenerateReportRequest(self, error_message, service, version=None,
                            project=None, request_url=None, user=None):
    """Creates a new error event request.

    Args:
      error_message: str, Crash details including stacktrace
      service: str, Name of service
      version: str, Service version, defaults to None
      project: str, Project to report errors to, defaults to current
      request_url: str, The request url that led to the error
      user: str, The user affected by the error

    Returns:
      The request to send.
    """
    service_context = self.api_messages.ServiceContext(
        service=service, version=version)

    error_event = self.api_messages.ReportedErrorEvent(
        serviceContext=service_context, message=error_message)

    if request_url or user:
      error_context = self.api_messages.ErrorContext()
      if request_url:
        error_context.httpRequest = self.api_messages.HttpRequestContext(
            url=request_url)
      if user:
        error_context.user = user
      error_event.context = error_context

    if project is None:
      project = self._GetGcloudProject()
    project_name = self._MakeProjectName(project)

    return self.api_messages.ClouderrorreportingProjectsEventsReportRequest(
        projectName=project_name, reportedErrorEvent=error_event)

  def _GetGcloudProject(self):
    """Gets the current project if project is not specified."""
    return properties.VALUES.core.project.Get(required=True)

  def _MakeProjectName(self, project):
    project_ref = resources.REGISTRY.Create(API_NAME + '.projects',
                                            projectId=project)
    return project_ref.RelativeName()

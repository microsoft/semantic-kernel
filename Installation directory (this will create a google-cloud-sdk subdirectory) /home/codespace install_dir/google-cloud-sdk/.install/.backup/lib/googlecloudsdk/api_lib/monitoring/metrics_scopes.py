# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utilities for Cloud Monitoring Metrics Scopes API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis


def GetClientInstance(no_http=False):
  return apis.GetClientInstance('monitoring', 'v1', no_http=no_http)


def GetMessagesModule(client=None):
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


class MetricsScopeClient(object):
  """Client for the Metrics Scope service in the Cloud Monitoring API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._ms_service = self.client.locations_global_metricsScopes
    self._mp_service = self.client.locations_global_metricsScopes_projects

  def MetricsScopeName(self, metrics_scope_ref):
    return 'locations/global/metricsScopes/' + metrics_scope_ref.Name()

  def MonitoredProjectName(self, metrics_scope_ref, monitored_project_ref):
    return self.MetricsScopeName(
        metrics_scope_ref) + '/projects/' + monitored_project_ref.Name()

  def List(self, project_ref):
    """List the Metrics Scopes monitoring the specified project."""
    request = (
        self.messages.
        MonitoringLocationsGlobalMetricsScopesListMetricsScopesByMonitoredProjectRequest(
            monitoredResourceContainer=project_ref.RelativeName()))
    return self._ms_service.ListMetricsScopesByMonitoredProject(request)

  def Create(self, metrics_scope_ref, monitored_project_ref):
    """Create a Monitored Project in a Monitoring Metrics Scope."""
    mp = self.messages.MonitoredProject()
    mp.name = self.MonitoredProjectName(metrics_scope_ref,
                                        monitored_project_ref)
    request = (
        self.messages
        .MonitoringLocationsGlobalMetricsScopesProjectsCreateRequest(
            monitoredProject=mp,
            parent=self.MetricsScopeName(metrics_scope_ref)))
    return self._mp_service.Create(request)

  def Delete(self, metrics_scope_ref, monitored_project_ref):
    """Delete a Monitored Project from a Monitoring Metrics Scope."""
    request = (
        self.messages
        .MonitoringLocationsGlobalMetricsScopesProjectsDeleteRequest(
            name=self.MonitoredProjectName(metrics_scope_ref,
                                           monitored_project_ref)))
    return self._mp_service.Delete(request)

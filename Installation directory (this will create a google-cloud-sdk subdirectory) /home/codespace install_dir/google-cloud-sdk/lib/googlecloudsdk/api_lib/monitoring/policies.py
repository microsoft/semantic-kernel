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
"""Utilities for Cloud Monitoring Policies API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis


def GetClientInstance(no_http=False):
  return apis.GetClientInstance('monitoring', 'v3', no_http=no_http)


def GetMessagesModule(client=None):
  client = client or GetClientInstance()
  return client.MESSAGES_MODULE


class AlertPolicyClient(object):
  """Client for the Alert Policy service in the Stackdriver Monitoring API."""

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or GetMessagesModule(client)
    self._service = self.client.projects_alertPolicies

  def Create(self, project_ref, policy):
    """Creates a Stackdriver alerting policy."""
    req = self.messages.MonitoringProjectsAlertPoliciesCreateRequest(
        name=project_ref.RelativeName(),
        alertPolicy=policy)
    return self._service.Create(req)

  def Get(self, policy_ref):
    """Gets an Monitoring Alert Policy."""
    request = self.messages.MonitoringProjectsAlertPoliciesGetRequest(
        name=policy_ref.RelativeName())
    return self._service.Get(request)

  def List(self, project_ref, list_filter=None):
    """List Monitoring Alert Policies.

    "list_filter" must be a valid filter expression or an empty value. For more
    information, see
    https://cloud.google.com/monitoring/api/v3/sorting-and-filtering

    Args:
      project_ref: resources.Resource, Resource reference to the policy to be
        updated.
      list_filter: str, filter to be included in the ListAlertPOliciesRequest.

    Returns:
      Alert policies that match the given filter. If no filter is given, fetches
      all policies from the target project.
    """
    request = self.messages.MonitoringProjectsAlertPoliciesListRequest(
        name=project_ref.RelativeName(), filter=list_filter or ''
    )
    return self._service.List(request)

  def Update(self, policy_ref, policy, fields=None):
    """Updates a Monitoring Alert Policy.

    If fields is not specified, then the policy is replaced entirely. If
    fields are specified, then only the fields are replaced.

    Args:
      policy_ref: resources.Resource, Resource reference to the policy to be
          updated.
      policy: AlertPolicy, The policy message to be sent with the request.
      fields: str, Comma separated list of field masks.
    Returns:
      AlertPolicy, The updated AlertPolicy.
    """
    request = self.messages.MonitoringProjectsAlertPoliciesPatchRequest(
        name=policy_ref.RelativeName(),
        alertPolicy=policy,
        updateMask=fields)
    return self._service.Patch(request)

# -*- coding: utf-8 -*- #
# Copyright 2022 Google Inc. All Rights Reserved.
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
"""Anthos Policy Controller status API utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import api_util as fleet_api_util
from googlecloudsdk.command_lib.container.fleet.policycontroller import constants
from googlecloudsdk.core import exceptions
import six


def _GetApiVersionFromReleaseTrack(release_track):
  if release_track == base.ReleaseTrack.ALPHA:
    return 'v1alpha'
  raise ValueError('Invalid release track: ' + release_track)


def GetMessagesModule(release_track):
  """Returns the Policy Controller status API messages module."""
  return apis.GetMessagesModule(
      'anthospolicycontrollerstatus_pa',
      _GetApiVersionFromReleaseTrack(release_track))


def GetClientInstance(release_track):
  """Returns the Policy Controller status API client instance."""
  return apis.GetClientInstance(
      'anthospolicycontrollerstatus_pa',
      _GetApiVersionFromReleaseTrack(release_track))


def GetMembershipConstraint(client, messages, constraint_name, project_id,
                            membership, release_track):
  """Returns a formatted membership constraint."""
  try:
    membership_obj = fleet_api_util.GetMembership(membership,
                                                  release_track)
  except apitools_exceptions.HttpNotFoundError:
    raise exceptions.Error(
        'Membership [{}] was not found in the Fleet.'
        .format(membership))

  try:
    request = messages.AnthospolicycontrollerstatusPaProjectsMembershipConstraintsGetRequest(
        name='projects/{}/membershipConstraints/{}/{}'.format(
            project_id, constraint_name, membership_obj.uniqueId))
    response = client.projects_membershipConstraints.Get(request)
  except apitools_exceptions.HttpNotFoundError:
    raise exceptions.Error(
        'Constraint [{}] was not found in Fleet membership [{}].'
        .format(constraint_name, membership))

  return {
      'name':
          response.constraintRef.name,
      'template':
          response.constraintRef.constraintTemplateName,
      'enforcementAction':
          constants.get_enforcement_action_label(
              six.text_type(response.spec.enforcementAction)),
      'membership': membership,
      'violationCount':
          response.status.numViolations or 0,
      'violations': [],
      'match':
          response.spec.kubernetesMatch or {},
      'parameters':
          response.spec.parameters or {}
  }


def GetFleetConstraint(client, messages, constraint_name, project_id):
  """Returns a formatted Fleet constraint."""
  try:
    request = messages.AnthospolicycontrollerstatusPaProjectsFleetConstraintsGetRequest(
        name='projects/{}/fleetConstraints/{}'.format(
            project_id, constraint_name))
    response = client.projects_fleetConstraints.Get(request)
  except apitools_exceptions.HttpNotFoundError:
    raise exceptions.Error(
        'Constraint [{}] was not found in the fleet.'
        .format(constraint_name))
  constraint = {
      'name': response.ref.name,
      'template': response.ref.constraintTemplateName,
      'violations': [],
      'violationCount': response.numViolations or 0,
      'memberships': [],
      'membershipCount': response.numMemberships or 0
  }

  membership_constraints_request = messages.AnthospolicycontrollerstatusPaProjectsMembershipConstraintsListRequest(
      parent='projects/{}'.format(project_id))
  membership_constraints_response = client.projects_membershipConstraints.List(
      membership_constraints_request)

  for membership_constraint in membership_constraints_response.membershipConstraints:
    if constraint_name == '{}/{}'.format(
        membership_constraint.constraintRef.constraintTemplateName,
        membership_constraint.constraintRef.name):
      constraint['memberships'].append(
          membership_constraint.membershipRef.name)

  return constraint


def ListFleetConstraints(client, msg, project_id):
  client_fn = client.projects_fleetConstraints
  req = msg.AnthospolicycontrollerstatusPaProjectsFleetConstraintsListRequest()
  return _Autopage(client_fn, req, project_id,
                   lambda response: response.fleetConstraints)


def ListMembershipConstraints(client, msg, project_id):
  client_fn = client.projects_membershipConstraints
  req = msg.AnthospolicycontrollerstatusPaProjectsMembershipConstraintsListRequest()  # pylint: disable=line-too-long
  return _Autopage(client_fn, req, project_id,
                   lambda response: response.membershipConstraints)


def ListFleetConstraintTemplates(client, msg, project_id):
  client_fn = client.projects_fleetConstraintTemplates
  req = msg.AnthospolicycontrollerstatusPaProjectsFleetConstraintTemplatesListRequest()  # pylint: disable=line-too-long
  return _Autopage(client_fn, req, project_id,
                   lambda response: response.fleetConstraintTemplates)


def ListMembershipConstraintTemplates(client, msg, project_id):
  client_fn = client.projects_membershipConstraintTemplates
  req = msg.AnthospolicycontrollerstatusPaProjectsMembershipConstraintTemplatesListRequest()  # pylint: disable=line-too-long
  return _Autopage(client_fn, req, project_id,
                   lambda response: response.membershipConstraintTemplates)


def ListViolations(client, msg, project_id):
  client_fn = client.projects_membershipConstraintAuditViolations
  req = msg.AnthospolicycontrollerstatusPaProjectsMembershipConstraintAuditViolationsListRequest()  # pylint: disable=line-too-long
  return _Autopage(
      client_fn, req, project_id,
      lambda response: response.membershipConstraintAuditViolations)


def ListMemberships(client, msg, project_id):
  client_fn = client.projects_memberships
  req = msg.AnthospolicycontrollerstatusPaProjectsMembershipsListRequest()
  return _Autopage(client_fn, req, project_id,
                   lambda response: response.memberships)


def _Autopage(client_fn, request, project_id, resource_collector):
  """Auto-page through the responses if the next page token is not empty and returns a list of all resources.

  Args:
    client_fn: Function specific to the endpoint
    request: Request object specific to the endpoint
    project_id: Project id that will be used in populating the request object
    resource_collector: Function to be used for retrieving the relevant field
      from the response

  Returns:
    List of all resources specific to the endpoint
  """
  resources = []
  next_page_token = ''
  while True:
    request.parent = 'projects/' + project_id
    request.pageToken = next_page_token
    response = client_fn.List(request)
    resources += resource_collector(response)
    if not response.nextPageToken:
      break
    next_page_token = response.nextPageToken
  return resources

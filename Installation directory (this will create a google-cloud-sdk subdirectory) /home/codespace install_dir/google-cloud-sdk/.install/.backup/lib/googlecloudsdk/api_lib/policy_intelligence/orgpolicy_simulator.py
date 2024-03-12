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
"""Utilities for Org Policy Simulator API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


_API_NAME = 'policysimulator'
_MAX_WAIT_TIME_MS = 60 * 60 * 1000  # 60 minutes.

VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1alpha',
    base.ReleaseTrack.BETA: 'v1beta',
    base.ReleaseTrack.GA: 'v1'
}


def GetApiVersion(release_track):
  """Return the api version of the Org Policy Simulator service."""
  return VERSION_MAP.get(release_track)


class OrgPolicySimulatorApi(object):
  """Base Class for OrgPolicy Simulator API."""

  def __new__(cls, release_track):
    if release_track == base.ReleaseTrack.ALPHA:
      return super(OrgPolicySimulatorApi,
                   cls).__new__(OrgPolicySimulatorApiAlpha)
    if release_track == base.ReleaseTrack.BETA:
      return super(OrgPolicySimulatorApi,
                   cls).__new__(OrgPolicySimulatorApiBeta)
    if release_track == base.ReleaseTrack.GA:
      return super(OrgPolicySimulatorApi,
                   cls).__new__(OrgPolicySimulatorApiGA)

  def __init__(self, release_track):
    self.api_version = GetApiVersion(release_track)
    self.client = apis.GetClientInstance(_API_NAME, self.api_version)
    self.messages = apis.GetMessagesModule(_API_NAME, self.api_version)

  # New operation name has format: organizations/<orgID>/locations/<locationID>/
  # orgPolicyViolationsPreviews/<orgPolicyPreviewID>/operations/<operationID>
  def GetViolationsPreviewId(self, operation_name):
    return operation_name.split('/')[-3]

  def WaitForOperation(self, operation, message):
    """Wait for the operation to complete."""
    # Use "GetOperation" from policysimulator (version: `self.api_version`)
    v1_client = apis.GetClientInstance(_API_NAME, self.api_version)
    registry = resources.REGISTRY.Clone()
    registry.RegisterApiByName('policysimulator', self.api_version)

    operation_ref = registry.Parse(
        operation.name,
        params={
            'organizationsId':
                properties.VALUES.access_context_manager.organization.GetOrFail,
            'locationsId': 'global',
            'orgPolicyViolationsPreviewsId':
                self.GetViolationsPreviewId(operation.name),
        },
        collection='policysimulator.organizations.locations.orgPolicyViolationsPreviews.operations')
    poller = waiter.CloudOperationPollerNoResources(v1_client.operations)
    return waiter.WaitFor(
        poller, operation_ref, message, wait_ceiling_ms=_MAX_WAIT_TIME_MS)

  @abc.abstractmethod
  def CreateOrgPolicyViolationsPreviewRequest(self,
                                              violations_preview=None,
                                              parent=None):
    pass

  @abc.abstractmethod
  def GetPolicysimulatorOrgPolicyViolationsPreview(self,
                                                   name=None,
                                                   overlay=None,
                                                   resource_counts=None,
                                                   state=None,
                                                   violations_count=None):
    pass

  @abc.abstractmethod
  def GetOrgPolicyOverlay(self,
                          custom_constraints=None,
                          policies=None):
    pass

  @abc.abstractmethod
  def GetOrgPolicyPolicyOverlay(
      self,
      policy=None,
      policy_parent=None):
    pass

  @abc.abstractmethod
  def GetOrgPolicyCustomConstraintOverlay(self,
                                          custom_constraint=None,
                                          custom_constraint_parent=None):
    pass

  @abc.abstractmethod
  def GetOrgPolicyViolationsPreviewMessage(self):
    pass


class OrgPolicySimulatorApiAlpha(OrgPolicySimulatorApi):
  """Base Class for OrgPolicy Simulator API Alpha."""

  def CreateOrgPolicyViolationsPreviewRequest(self,
                                              violations_preview=None,
                                              parent=None):
    return self.messages.PolicysimulatorOrganizationsLocationsOrgPolicyViolationsPreviewsCreateRequest(
        googleCloudPolicysimulatorV1alphaOrgPolicyViolationsPreview=violations_preview,
        parent=parent)

  def GetPolicysimulatorOrgPolicyViolationsPreview(self,
                                                   name=None,
                                                   overlay=None,
                                                   resource_counts=None,
                                                   state=None,
                                                   violations_count=None):
    return self.messages.GoogleCloudPolicysimulatorV1alphaOrgPolicyViolationsPreview(
        name=name,
        overlay=overlay,
        resourceCounts=resource_counts,
        state=state,
        violationsCount=violations_count)

  def GetOrgPolicyOverlay(self,
                          custom_constraints=None,
                          policies=None):
    return self.messages.GoogleCloudPolicysimulatorV1alphaOrgPolicyOverlay(
        customConstraints=custom_constraints,
        policies=policies)

  def GetOrgPolicyPolicyOverlay(self,
                                policy=None,
                                policy_parent=None):
    return self.messages.GoogleCloudPolicysimulatorV1alphaOrgPolicyOverlayPolicyOverlay(
        policy=policy,
        policyParent=policy_parent)

  def GetOrgPolicyCustomConstraintOverlay(self,
                                          custom_constraint=None,
                                          custom_constraint_parent=None):
    return self.messages.GoogleCloudPolicysimulatorV1alphaOrgPolicyOverlayCustomConstraintOverlay(
        customConstraint=custom_constraint,
        customConstraintParent=custom_constraint_parent)

  def GetOrgPolicyViolationsPreviewMessage(self):
    m = self.messages.GoogleCloudPolicysimulatorV1alphaOrgPolicyViolationsPreview
    return m


class OrgPolicySimulatorApiBeta(OrgPolicySimulatorApi):
  """Base Class for OrgPolicy Simulator API Beta."""

  def CreateOrgPolicyViolationsPreviewRequest(self,
                                              violations_preview=None,
                                              parent=None):
    return self.messages.PolicysimulatorOrganizationsLocationsOrgPolicyViolationsPreviewsCreateRequest(
        googleCloudPolicysimulatorV1betaOrgPolicyViolationsPreview=violations_preview,
        parent=parent)

  def GetPolicysimulatorOrgPolicyViolationsPreview(self,
                                                   name=None,
                                                   overlay=None,
                                                   resource_counts=None,
                                                   state=None,
                                                   violations_count=None):
    return self.messages.GoogleCloudPolicysimulatorV1betaOrgPolicyViolationsPreview(
        name=name,
        overlay=overlay,
        resourceCounts=resource_counts,
        state=state,
        violationsCount=violations_count)

  def GetOrgPolicyOverlay(self,
                          custom_constraints=None,
                          policies=None):
    return self.messages.GoogleCloudPolicysimulatorV1betaOrgPolicyOverlay(
        customConstraints=custom_constraints,
        policies=policies)

  def GetOrgPolicyPolicyOverlay(self,
                                policy=None,
                                policy_parent=None):
    return self.messages.GoogleCloudPolicysimulatorV1betaOrgPolicyOverlayPolicyOverlay(
        policy=policy,
        policyParent=policy_parent)

  def GetOrgPolicyCustomConstraintOverlay(self,
                                          custom_constraint=None,
                                          custom_constraint_parent=None):
    return self.messages.GoogleCloudPolicysimulatorV1betaOrgPolicyOverlayCustomConstraintOverlay(
        customConstraint=custom_constraint,
        customConstraintParent=custom_constraint_parent)

  def GetOrgPolicyViolationsPreviewMessage(self):
    m = self.messages.GoogleCloudPolicysimulatorV1betaOrgPolicyViolationsPreview
    return m

class OrgPolicySimulatorApiGA(OrgPolicySimulatorApi):
  """Base Class for OrgPolicy Simulator API GA."""

  def CreateOrgPolicyViolationsPreviewRequest(self,
                                              violations_preview=None,
                                              parent=None):
    return self.messages.PolicysimulatorOrganizationsLocationsOrgPolicyViolationsPreviewsCreateRequest(
        googleCloudPolicysimulatorV1OrgPolicyViolationsPreview=violations_preview,
        parent=parent)

  def GetPolicysimulatorOrgPolicyViolationsPreview(self,
                                                   name=None,
                                                   overlay=None,
                                                   resource_counts=None,
                                                   state=None,
                                                   violations_count=None):
    return self.messages.GoogleCloudPolicysimulatorV1OrgPolicyViolationsPreview(
        name=name,
        overlay=overlay,
        resourceCounts=resource_counts,
        state=state,
        violationsCount=violations_count)

  def GetOrgPolicyOverlay(self,
                          custom_constraints=None,
                          policies=None):
    return self.messages.GoogleCloudPolicysimulatorV1OrgPolicyOverlay(
        customConstraints=custom_constraints,
        policies=policies)

  def GetOrgPolicyPolicyOverlay(self,
                                policy=None,
                                policy_parent=None):
    return self.messages.GoogleCloudPolicysimulatorV1OrgPolicyOverlayPolicyOverlay(
        policy=policy,
        policyParent=policy_parent)

  def GetOrgPolicyCustomConstraintOverlay(self,
                                          custom_constraint=None,
                                          custom_constraint_parent=None):
    return self.messages.GoogleCloudPolicysimulatorV1OrgPolicyOverlayCustomConstraintOverlay(
        customConstraint=custom_constraint,
        customConstraintParent=custom_constraint_parent)

  def GetOrgPolicyViolationsPreviewMessage(self):
    return self.messages.GoogleCloudPolicysimulatorV1OrgPolicyViolationsPreview

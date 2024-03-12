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
"""Utilities for Policy Troubleshooter API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base

_API_NAME = 'policytroubleshooter'
VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v3alpha',
    base.ReleaseTrack.BETA: 'v3beta',
    base.ReleaseTrack.GA: 'v3',
    # Future versions to be added.
}


def GetApiVersion(release_track):
  """Return the api version of the Policy Troubleshooter service."""
  return VERSION_MAP.get(release_track)


class PolicyTroubleshooterApi(object):
  """Base Class for Policy Troubleshooter API."""

  def __new__(cls, release_track):
    if release_track == base.ReleaseTrack.ALPHA:
      return super(PolicyTroubleshooterApi, cls).__new__(
          PolicyTroubleshooterApiAlpha
      )
    if release_track == base.ReleaseTrack.BETA:
      return super(PolicyTroubleshooterApi, cls).__new__(
          PolicyTroubleshooterApiBeta
      )
    if release_track == base.ReleaseTrack.GA:
      return super(PolicyTroubleshooterApi, cls).__new__(
          PolicyTroubleshooterApiGA
      )

  def __init__(self, release_track):
    api_version = GetApiVersion(release_track)
    self.client = apis.GetClientInstance(_API_NAME, api_version)
    self.messages = apis.GetMessagesModule(_API_NAME, api_version)

  @abc.abstractmethod
  def TroubleshootIAMPolicies(self, access_tuple):
    pass

  @abc.abstractmethod
  def GetPolicyTroubleshooterAccessTuple(
      self,
      condition_context=None,
      full_resource_name=None,
      principal_email=None,
      permission=None,
  ):
    pass

  @abc.abstractmethod
  def GetPolicyTroubleshooterConditionContext(
      self, destination=None, request=None, resource=None
  ):
    pass

  @abc.abstractmethod
  def GetPolicyTroubleshooterPeer(
      self, destination_ip=None, destination_port=None
  ):
    pass

  @abc.abstractmethod
  def GetPolicyTroubleshooterRequest(self, request_time=None):
    pass

  @abc.abstractmethod
  def GetPolicyTroubleshooterResource(
      self, resource_name=None, resource_service=None, resource_type=None
  ):
    pass


class PolicyTroubleshooterApiAlpha(PolicyTroubleshooterApi):
  """Base Class for Policy Troubleshooter API Alpha."""

  def TroubleshootIAMPolicies(self, access_tuple):
    request = self.messages.GoogleCloudPolicytroubleshooterIamV3alphaTroubleshootIamPolicyRequest(
        accessTuple=access_tuple
    )
    return self.client.iam.Troubleshoot(request)

  def GetPolicyTroubleshooterAccessTuple(
      self,
      condition_context=None,
      full_resource_name=None,
      principal_email=None,
      permission=None,
  ):
    return self.messages.GoogleCloudPolicytroubleshooterIamV3alphaAccessTuple(
        fullResourceName=full_resource_name,
        principal=principal_email,
        permission=permission,
        conditionContext=condition_context,
    )

  def GetPolicyTroubleshooterRequest(self, request_time=None):
    return self.messages.GoogleCloudPolicytroubleshooterIamV3alphaConditionContextRequest(
        receiveTime=request_time
    )

  def GetPolicyTroubleshooterResource(
      self, resource_name=None, resource_service=None, resource_type=None
  ):
    return self.messages.GoogleCloudPolicytroubleshooterIamV3alphaConditionContextResource(
        name=resource_name, service=resource_service, type=resource_type
    )

  def GetPolicyTroubleshooterPeer(
      self, destination_ip=None, destination_port=None
  ):
    return self.messages.GoogleCloudPolicytroubleshooterIamV3alphaConditionContextPeer(
        ip=destination_ip, port=destination_port
    )

  def GetPolicyTroubleshooterConditionContext(
      self, destination=None, request=None, resource=None
  ):
    return (
        self.messages.GoogleCloudPolicytroubleshooterIamV3alphaConditionContext(
            destination=destination, request=request, resource=resource
        )
    )


class PolicyTroubleshooterApiBeta(PolicyTroubleshooterApi):
  """Base Class for Policy Troubleshooter API Beta."""

  def TroubleshootIAMPolicies(self, access_tuple):
    request = self.messages.GoogleCloudPolicytroubleshooterIamV3betaTroubleshootIamPolicyRequest(
        accessTuple=access_tuple
    )
    return self.client.iam.Troubleshoot(request)

  def GetPolicyTroubleshooterAccessTuple(
      self,
      condition_context=None,
      full_resource_name=None,
      principal_email=None,
      permission=None,
  ):
    return self.messages.GoogleCloudPolicytroubleshooterIamV3betaAccessTuple(
        fullResourceName=full_resource_name,
        principal=principal_email,
        permission=permission,
        conditionContext=condition_context,
    )

  def GetPolicyTroubleshooterRequest(self, request_time=None):
    return self.messages.GoogleCloudPolicytroubleshooterIamV3betaConditionContextRequest(
        receiveTime=request_time
    )

  def GetPolicyTroubleshooterResource(
      self, resource_name=None, resource_service=None, resource_type=None
  ):
    return self.messages.GoogleCloudPolicytroubleshooterIamV3betaConditionContextResource(
        name=resource_name, service=resource_service, type=resource_type
    )

  def GetPolicyTroubleshooterPeer(
      self, destination_ip=None, destination_port=None
  ):
    return self.messages.GoogleCloudPolicytroubleshooterIamV3betaConditionContextPeer(
        ip=destination_ip, port=destination_port
    )

  def GetPolicyTroubleshooterConditionContext(
      self, destination=None, request=None, resource=None
  ):
    return (
        self.messages.GoogleCloudPolicytroubleshooterIamV3betaConditionContext(
            destination=destination, request=request, resource=resource
        )
    )


class PolicyTroubleshooterApiGA(PolicyTroubleshooterApi):
  """Base Class for Policy Troubleshooter API GA."""

  def TroubleshootIAMPolicies(self, access_tuple):
    request = self.messages.GoogleCloudPolicytroubleshooterIamV3TroubleshootIamPolicyRequest(
        accessTuple=access_tuple
    )
    return self.client.iam.Troubleshoot(request)

  def GetPolicyTroubleshooterAccessTuple(
      self,
      condition_context=None,
      full_resource_name=None,
      principal_email=None,
      permission=None,
  ):
    return self.messages.GoogleCloudPolicytroubleshooterIamV3AccessTuple(
        fullResourceName=full_resource_name,
        principal=principal_email,
        permission=permission,
        conditionContext=condition_context,
    )

  def GetPolicyTroubleshooterRequest(self, request_time=None):
    return self.messages.GoogleCloudPolicytroubleshooterIamV3ConditionContextRequest(
        receiveTime=request_time
    )

  def GetPolicyTroubleshooterResource(
      self, resource_name=None, resource_service=None, resource_type=None
  ):
    return self.messages.GoogleCloudPolicytroubleshooterIamV3ConditionContextResource(
        name=resource_name, service=resource_service, type=resource_type
    )

  def GetPolicyTroubleshooterPeer(
      self, destination_ip=None, destination_port=None
  ):
    return (
        self.messages.GoogleCloudPolicytroubleshooterIamV3ConditionContextPeer(
            ip=destination_ip, port=destination_port
        )
    )

  def GetPolicyTroubleshooterConditionContext(
      self, destination=None, request=None, resource=None
  ):
    return self.messages.GoogleCloudPolicytroubleshooterIamV3ConditionContext(
        destination=destination, request=request, resource=resource
    )

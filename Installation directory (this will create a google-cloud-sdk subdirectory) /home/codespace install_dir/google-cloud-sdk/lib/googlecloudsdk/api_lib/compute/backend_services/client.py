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
"""Backend service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.iam import iam_util


class BackendService(object):
  """Abstracts BackendService resource."""

  def __init__(self, ref, compute_client=None):
    self.ref = ref
    self._compute_client = compute_client

  @property
  def _client(self):
    return self._compute_client.apitools_client

  @property
  def _messages(self):
    return self._compute_client.messages

  def _MakeGetRequestTuple(self):
    region = getattr(self.ref, 'region', None)
    if region is not None:
      return (self._client.regionBackendServices, 'Get',
              self._messages.ComputeRegionBackendServicesGetRequest(
                  project=self.ref.project,
                  region=region,
                  backendService=self.ref.Name()))
    else:
      return (self._client.backendServices, 'Get',
              self._messages.ComputeBackendServicesGetRequest(
                  project=self.ref.project, backendService=self.ref.Name()))

  def _MakeSetRequestTuple(self, replacement):
    """Makes a location aware backend service patch call."""
    region = getattr(self.ref, 'region', None)
    if region is not None:
      return (self._client.regionBackendServices, 'Patch',
              self._messages.ComputeRegionBackendServicesPatchRequest(
                  project=self.ref.project,
                  region=region,
                  backendService=self.ref.Name(),
                  backendServiceResource=replacement))
    else:
      return (self._client.backendServices, 'Patch',
              self._messages.ComputeBackendServicesPatchRequest(
                  project=self.ref.project,
                  backendService=self.ref.Name(),
                  backendServiceResource=replacement))

  def _MakeDeleteRequestTuple(self):
    region = getattr(self.ref, 'region', None)
    if region is not None:
      return (self._client.regionBackendServices, 'Delete',
              self._messages.ComputeRegionBackendServicesDeleteRequest(
                  project=self.ref.project,
                  region=region,
                  backendService=self.ref.Name()))
    else:
      return (self._client.backendServices, 'Delete',
              self._messages.ComputeBackendServicesDeleteRequest(
                  project=self.ref.project, backendService=self.ref.Name()))

  def _MakeGetHealthRequestTuple(self, group):
    region = getattr(self.ref, 'region', None)
    if region is not None:
      return (self._client.regionBackendServices, 'GetHealth',
              self._messages.ComputeRegionBackendServicesGetHealthRequest(
                  resourceGroupReference=self._messages.ResourceGroupReference(
                      group=group),
                  project=self.ref.project,
                  region=region,
                  backendService=self.ref.Name()))
    else:
      return (self._client.backendServices, 'GetHealth',
              self._messages.ComputeBackendServicesGetHealthRequest(
                  resourceGroupReference=self._messages.ResourceGroupReference(
                      group=group),
                  project=self.ref.project,
                  backendService=self.ref.Name()))

  def MakeSetSecurityPolicyRequestTuple(self,
                                        security_policy):
    """Makes a call to set the security policy on a backend service."""
    region = getattr(self.ref, 'region', None)
    if region:
      return (
          self._client.regionBackendServices,
          'SetSecurityPolicy',
          self._messages.ComputeRegionBackendServicesSetSecurityPolicyRequest(
              securityPolicyReference=self._messages.SecurityPolicyReference(
                  securityPolicy=security_policy),
              region=region,
              project=self.ref.project,
              backendService=self.ref.Name()),
      )

    return (
        self._client.backendServices,
        'SetSecurityPolicy',
        self._messages.ComputeBackendServicesSetSecurityPolicyRequest(
            securityPolicyReference=self._messages.SecurityPolicyReference(
                securityPolicy=security_policy),
            project=self.ref.project,
            backendService=self.ref.Name()),
    )

  def MakeSetEdgeSecurityPolicyRequestTuple(self, security_policy):
    region = getattr(self.ref, 'region', None)
    if region:
      raise calliope_exceptions.InvalidArgumentException(
          'region',
          'Can only set edge security policy for global backend services.')

    return (
        self._client.backendServices,
        'SetEdgeSecurityPolicy',
        self._messages.ComputeBackendServicesSetEdgeSecurityPolicyRequest(
            securityPolicyReference=self._messages.SecurityPolicyReference(
                securityPolicy=security_policy),
            project=self.ref.project,
            backendService=self.ref.Name()),
    )

  def Delete(self, only_generate_request=False):
    requests = [self._MakeDeleteRequestTuple()]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def Get(self, only_generate_request=False):
    """Fetches the backend service resource."""
    requests = [self._MakeGetRequestTuple()]
    if not only_generate_request:
      responses = self._compute_client.MakeRequests(requests)
      return responses[0]
    return requests

  def Set(self, replacement):
    """Patches the backend service resource."""
    requests = [self._MakeSetRequestTuple(replacement)]
    self._compute_client.MakeRequests(requests)

  def GetHealth(self):
    """Issues series of gethealth requests for each backend group.

    Yields:
      {'backend': backend.group, 'status': backend_service.GetHealthResponse}
    """
    backend_service = self.Get()
    # Call GetHealth for each group in the backend service
    # Instead of batching-up all requests and making a single
    # request_helper.MakeRequests call, go one backend at a time.
    # We do this because getHealth responses don't say what resource
    # they correspond to.  It's not obvious how to reliably match up
    # responses and backends when there are errors.  Additionally the contract
    # for batched requests doesn't guarantee response order will match
    # request order.
    #
    # TODO(b/25015230): Make a single batch request once the response
    # can be mapped back to resource.
    errors = []
    for backend in backend_service.backends:
      # The list() call below is itended to force the generator returned by
      # MakeRequests.  If there are exceptions the command will abort, which is
      # expected.  Having a list simplifies some of the checks that follow.
      resources = self._compute_client.MakeRequests(
          [self._MakeGetHealthRequestTuple(backend.group)], errors)

      #  For failed request error information will accumulate in errors
      if resources:
        yield {'backend': backend.group, 'status': resources[0]}

    if errors:
      utils.RaiseToolException(
          errors, error_message='Could not get health for some groups:')

  def SetSecurityPolicy(self, security_policy='', only_generate_request=False):
    """Sets the security policy for the backend service."""
    requests = [self.MakeSetSecurityPolicyRequestTuple(security_policy)]
    if not only_generate_request:
      return self._compute_client.MakeRequests(requests)
    return requests

  def GetIamPolicy(self):
    """Get the IAM policy for a Compute Engine backend service."""
    if self.ref.Collection() == 'compute.backendServices':
      service = self._compute_client.apitools_client.backendServices
      request = self._compute_client.messages.ComputeBackendServicesGetIamPolicyRequest(
          resource=self.ref.Name(), project=self.ref.project)
    elif self.ref.Collection() == 'compute.regionBackendServices':
      service = self._compute_client.apitools_client.regionBackendServices
      request = self._compute_client.messages.ComputeRegionBackendServicesGetIamPolicyRequest(
          resource=self.ref.Name(),
          region=self.ref.region,
          project=self.ref.project)
    return self._compute_client.MakeRequests([(service, 'GetIamPolicy', request)
                                             ])[0]

  def SetIamPolicy(self, policy):
    """Set the IAM policy binding for a Compute Engine backend service."""
    if self.ref.Collection() == 'compute.backendServices':
      service = self._compute_client.apitools_client.backendServices
      request = self._compute_client.messages.ComputeBackendServicesSetIamPolicyRequest(
          resource=self.ref.Name(),
          project=self.ref.project,
          globalSetPolicyRequest=self._compute_client.messages
          .GlobalSetPolicyRequest(policy=policy))
    elif self.ref.Collection() == 'compute.regionBackendServices':
      service = self._compute_client.apitools_client.regionBackendServices
      request = self._compute_client.messages.ComputeRegionBackendServicesSetIamPolicyRequest(
          resource=self.ref.Name(),
          region=self.ref.region,
          project=self.ref.project,
          regionSetPolicyRequest=self._compute_client.messages
          .RegionSetPolicyRequest(policy=policy))
    result = self._compute_client.MakeRequests([(service, 'SetIamPolicy',
                                                 request)])[0]
    iam_util.LogSetIamPolicy(self.ref.Name(), 'backend service')
    return result

  def AddIamPolicyBinding(self, member, role):
    """Compute Engine backend service add iam policy binding request."""
    policy = self.GetIamPolicy()
    iam_util.AddBindingToIamPolicy(self._messages.Binding, policy, member, role)
    return self.SetIamPolicy(policy)

  def RemoveIamPolicyBinding(self, member, role):
    """Compute Engine backend service remove iam policy binding request."""
    policy = self.GetIamPolicy()
    iam_util.RemoveBindingFromIamPolicy(policy, member, role)
    return self.SetIamPolicy(policy)

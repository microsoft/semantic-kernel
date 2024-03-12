# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""API utilities for gcloud compute ssl-policy commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.util import waiter


class SslPolicyHelper(object):
  """Helper for SSL policy service in the Compute API."""

  def __init__(self, holder):
    """Initializes the helper for SSL policy operations.

    Args:
      holder: Object representing the Compute API holder instance.
    """
    self._compute_client = holder.client
    self._resources = holder.resources

  @property
  def _client(self):
    return self._compute_client.apitools_client

  @property
  def _messages(self):
    return self._compute_client.messages

  def GetSslPolicyForInsert(self, name, description, profile, min_tls_version,
                            custom_features):
    """Returns the SslPolicy message for an insert request.

    Args:
      name: String representing the name of the SSL policy resource.
      description: String representing the description for the SSL policy
        resource.
      profile: String representing the SSL policy profile. Can be one of
        'COMPATIBLE', 'MODERN', 'RESTRICTED' or 'CUSTOM'.
      min_tls_version: String representing the minimum TLS version of the SSL
        policy. Can be one of 'TLS_1_0', 'TLS_1_1', 'TLS_1_2'.
      custom_features: The list of strings representing the custom features to
        use.

    Returns:
      The SslPolicy message object that can be used in an insert request.
    """
    return self._messages.SslPolicy(
        name=name,
        description=description,
        profile=self._messages.SslPolicy.ProfileValueValuesEnum(profile),
        minTlsVersion=self._messages.SslPolicy.MinTlsVersionValueValuesEnum(
            min_tls_version),
        customFeatures=custom_features)

  def GetSslPolicyForPatch(self,
                           fingerprint,
                           profile=None,
                           min_tls_version=None,
                           custom_features=None):
    """Returns the SslPolicy message for a patch request.

    Args:
      fingerprint: String representing the existing fingerprint of the SSL
        policy resource.
      profile: String representing the SSL policy profile. Can be one of
        'COMPATIBLE', 'MODERN', 'RESTRICTED' or 'CUSTOM'.
      min_tls_version: String representing the minimum TLS version of the SSL
        policy. Can be one of 'TLS_1_0', 'TLS_1_1', 'TLS_1_2'.
      custom_features: The list of strings representing the custom features to
        use.
    """
    messages = self._messages
    ssl_policy = messages.SslPolicy(fingerprint=fingerprint)
    if profile:
      ssl_policy.profile = messages.SslPolicy.ProfileValueValuesEnum(profile)
    if min_tls_version:
      ssl_policy.minTlsVersion = (
          messages.SslPolicy.MinTlsVersionValueValuesEnum(min_tls_version))
    if custom_features is not None:
      ssl_policy.customFeatures = custom_features
    return ssl_policy

  def WaitForOperation(self, ssl_policy_ref, operation_ref, wait_message):
    """Waits for the specified operation to complete and returns the target.

    Args:
      ssl_policy_ref: The SSL policy reference object.
      operation_ref: The operation reference object to wait for.
      wait_message: String representing the wait message to display while the
        operation is in progress.

    Returns:
      The resulting resource object after the operation completes.
    """
    if ssl_policy_ref.Collection() == 'compute.regionSslPolicies':
      operation_poller = poller.Poller(self._client.regionSslPolicies,
                                       ssl_policy_ref)
      return waiter.WaitFor(operation_poller, operation_ref, wait_message)

    operation_poller = poller.Poller(self._client.sslPolicies, ssl_policy_ref)
    return waiter.WaitFor(operation_poller, operation_ref, wait_message)

  def Create(self, ref, ssl_policy):
    """Sends an Insert request for an SSL policy and returns the operation.

    Args:
      ref: The SSL policy reference object.
      ssl_policy: The SSL policy message object to use in the insert request.

    Returns:
      The operation reference object for the insert request.
    """
    if ref.Collection() == 'compute.regionSslPolicies':
      request = self._messages.ComputeRegionSslPoliciesInsertRequest(
          project=ref.project, region=ref.region, sslPolicy=ssl_policy)
      operation = self._client.regionSslPolicies.Insert(request)
      return self._resources.Parse(
          operation.selfLink, collection='compute.regionOperations')

    request = self._messages.ComputeSslPoliciesInsertRequest(
        project=ref.project, sslPolicy=ssl_policy)
    operation = self._client.sslPolicies.Insert(request)
    return self._resources.Parse(
        operation.selfLink, collection='compute.globalOperations')

  def Describe(self, ref):
    """Sends a Get request for an SSL policy and returns the resource.

    Args:
      ref: The SSL policy reference object.

    Returns:
      The SSL policy resource object.
    """
    if ref.Collection() == 'compute.regionSslPolicies':
      request = self._messages.ComputeRegionSslPoliciesGetRequest(
          project=ref.project, region=ref.region, sslPolicy=ref.Name())
      return self._client.regionSslPolicies.Get(request)

    request = self._messages.ComputeSslPoliciesGetRequest(
        project=ref.project, sslPolicy=ref.Name())
    return self._client.sslPolicies.Get(request)

  def Patch(self, ref, ssl_policy, clear_custom_features):
    """Sends a Patch request for an SSL policy and returns the operation.

    Args:
      ref: The SSL policy reference object.
      ssl_policy: The SSL policy message object to use in the patch request.
      clear_custom_features: If True, customFeatures field is explicitly cleared
        by including it in the request even if empty. Otherwise it is included
        only if the SSL policy message has non-empty customFeatures field.

    Returns:
      The operation reference object for the patch request.
    """
    cleared_fields = []
    # Since custom_features is a repeated field, we need to explicitly indicate
    # that the field must be cleared when it is empty, for patch requests.
    # Otherwise the field is ignored and will not be part of the request.
    if clear_custom_features:
      cleared_fields.append('customFeatures')

    if ref.Collection() == 'compute.regionSslPolicies':
      request = self._messages.ComputeRegionSslPoliciesPatchRequest(
          project=ref.project,
          region=ref.region,
          sslPolicy=ref.Name(),
          sslPolicyResource=ssl_policy)
      with self._client.IncludeFields(cleared_fields):
        operation = self._client.regionSslPolicies.Patch(request)
      return self._resources.Parse(
          operation.selfLink, collection='compute.regionOperations')

    request = self._messages.ComputeSslPoliciesPatchRequest(
        project=ref.project, sslPolicy=ref.Name(), sslPolicyResource=ssl_policy)
    with self._client.IncludeFields(cleared_fields):
      operation = self._client.sslPolicies.Patch(request)
    return self._resources.Parse(
        operation.selfLink, collection='compute.globalOperations')

  def Delete(self, ref):
    """Sends a Delete request for an SSL policy and returns the operation.

    Args:
      ref: The SSL policy reference object.

    Returns:
      The operation reference object for the delete request.
    """
    if ref.Collection() == 'compute.regionSslPolicies':
      request = self._messages.ComputeRegionSslPoliciesDeleteRequest(
          project=ref.project, region=ref.region, sslPolicy=ref.Name())
      operation = self._client.regionSslPolicies.Delete(request)
      return self._resources.Parse(
          operation.selfLink, collection='compute.regionOperations')

    request = self._messages.ComputeSslPoliciesDeleteRequest(
        project=ref.project, sslPolicy=ref.Name())
    operation = self._client.sslPolicies.Delete(request)
    return self._resources.Parse(
        operation.selfLink, collection='compute.globalOperations')

  def ListAvailableFeatures(self, project, region):
    """Sends a ListAvailableFeatures request and returns the features.

    Args:
      project: String representing the project to use for the request.
      region: The region to use. If not set, the global scope is used.

    Returns:
      List of strings representing the list of available features.
    """
    if region:
      request = self._messages.ComputeRegionSslPoliciesListAvailableFeaturesRequest(
          project=project, region=region)
      return self._client.regionSslPolicies.ListAvailableFeatures(
          request).features

    request = self._messages.ComputeSslPoliciesListAvailableFeaturesRequest(
        project=project)
    return self._client.sslPolicies.ListAvailableFeatures(request).features

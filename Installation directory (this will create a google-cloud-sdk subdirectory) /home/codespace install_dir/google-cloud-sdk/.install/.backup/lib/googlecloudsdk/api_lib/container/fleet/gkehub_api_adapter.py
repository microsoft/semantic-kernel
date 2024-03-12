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

"""Adapter for interaction with gkehub One Platform APIs."""

# TODO(b/181243034): This file should be replaced with `util.py` once
# the Membership API is on version selector.

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from apitools.base.py import encoding
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core import resources as cloud_resources
import six

API_NAME = 'gkehub'


def NewAPIAdapter(api_version):
  return InitAPIAdapter(api_version, APIAdapter)


def InitAPIAdapter(api_version, adapter):
  """Initialize an api adapter.

  Args:
    api_version: the api version we want.
    adapter: the api adapter constructor.
  Returns:
    APIAdapter object.
  """

  api_client = core_apis.GetClientInstance(API_NAME, api_version)
  api_client.check_response_func = api_adapter.CheckResponse
  messages = api_client.MESSAGES_MODULE

  registry = cloud_resources.REGISTRY.Clone()
  registry.RegisterApiByName(API_NAME, api_version)

  return adapter(registry, api_client, messages, api_version)


class APIAdapter(object):
  """Handles making api requests in a version-agnostic way."""

  _HTTP_ERROR_FORMAT = ('HTTP request failed with status code {}. '
                        'Response content: {}')

  def __init__(self, registry, client, messages, api_version):
    self.registry = registry
    self.client = client
    self.messages = messages
    self.api_version = api_version

  def _ManifestResponse(self, client, messages, option):
    return getattr(
        client.projects_locations_memberships.GenerateConnectManifest(
            messages
            .GkehubProjectsLocationsMembershipsGenerateConnectManifestRequest(
                imagePullSecretContent=six.ensure_binary(
                    option.image_pull_secret_content),
                isUpgrade=option.is_upgrade,
                name=option.membership_ref,
                connectAgent_namespace=option.namespace,
                connectAgent_proxy=six.ensure_binary(option.proxy),
                registry=option.registry,
                version=option.version)), 'manifest')

  def GenerateConnectAgentManifest(self, option):
    """Generate the YAML manifest to deploy the Connect Agent.

    Args:
      option: an instance of ConnectAgentOption.

    Returns:
      A slice of connect agent manifest resources.
    Raises:
      Error: if the API call to generate connect agent manifest failed.
    """
    client = core_apis.GetClientInstance(API_NAME, self.api_version)
    messages = core_apis.GetMessagesModule(API_NAME, self.api_version)
    encoding.AddCustomJsonFieldMapping(
        messages
        .GkehubProjectsLocationsMembershipsGenerateConnectManifestRequest,
        'connectAgent_namespace', 'connectAgent.namespace')
    encoding.AddCustomJsonFieldMapping(
        messages
        .GkehubProjectsLocationsMembershipsGenerateConnectManifestRequest,
        'connectAgent_proxy', 'connectAgent.proxy')
    return self._ManifestResponse(client, messages, option)


class ConnectAgentOption(object):
  """Option for generating connect agent manifest."""

  def __init__(self,
               name,
               proxy,
               namespace,
               is_upgrade,
               version,
               registry,
               image_pull_secret_content,
               membership_ref):
    self.name = name
    self.proxy = proxy
    self.namespace = namespace
    self.is_upgrade = is_upgrade
    self.version = version
    self.registry = registry
    self.image_pull_secret_content = image_pull_secret_content
    self.membership_ref = membership_ref

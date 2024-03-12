# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Library for the Secret Manager integration in the local environment."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import re

from apitools.base.py import encoding_helper
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.code import kubernetes
from googlecloudsdk.command_lib.run import secrets_mapping

SECRETS_MESSAGE_MODULE = apis.GetMessagesModule('secretmanager', 'v1')
RUN_MESSAGE_MODULE = apis.GetMessagesModule('run', 'v1')


class SecretManagerSecret(object):
  """A secret to be fetched from Secret Manager."""

  def __init__(self, name, versions, mapped_secret=None):
    self.name = name
    self.versions = versions
    self.mapped_secret = mapped_secret

  def __eq__(self, other):
    return (self.name == other.name and self.versions == other.versions and
            self.mapped_secret == other.mapped_secret)

  def __repr__(self):
    return '<Secret: (name="{}", versions={}, mapped_secret="{}")>'.format(
        self.name, self.versions, self.mapped_secret)

  def __hash__(self):
    return hash((self.name, self.versions, self.mapped_secret))


def BuildSecrets(project_name, secret_list, namespace, client=None):
  """Fetch secrets from Secret Manager and create k8s secrets with the data."""
  if client is None:
    client = _SecretsClient()
  secrets = []
  for secret in secret_list:
    secrets.append(
        _BuildSecret(client, project_name, secret.name, secret.mapped_secret,
                     secret.versions, namespace))
  return secrets


def _BuildSecret(client, project, secret_name, mapped_secret, versions,
                 namespace):
  """Build the k8s secret resource for minikube from Secret Manager data."""
  if secrets_mapping.SpecialVersion.MOUNT_ALL in versions:
    # TODO(b/187972361): Do we need to load all secret versions for the secret?
    raise ValueError('local development requires you to specify all secret '
                     'versions that you need to use.')
  secrets = {}
  for version in versions:
    secrets[version] = client.GetSecretData(project, secret_name, mapped_secret,
                                            version)
  return _BuildK8sSecret(secret_name, secrets, namespace)


def _BuildK8sSecret(secret_name, secrets, namespace):
  """Turn a map of SecretManager responses into a k8s secret."""
  data_value = RUN_MESSAGE_MODULE.Secret.DataValue(additionalProperties=[])
  k8s_secret = RUN_MESSAGE_MODULE.Secret(
      metadata=RUN_MESSAGE_MODULE.ObjectMeta(
          name=secret_name, namespace=namespace),
      data=data_value)
  for version, secret in secrets.items():
    k8s_secret.data.additionalProperties.append(
        RUN_MESSAGE_MODULE.Secret.DataValue.AdditionalProperty(
            key=version, value=secret.payload.data))
  d = encoding_helper.MessageToDict(k8s_secret)
  # RUN_MESSAGE_MODULE.Secret doesn't have fields for apiVersion and Kind so we
  # need to add that here
  d['apiVersion'] = 'v1'
  d['kind'] = 'Secret'
  return d


def _DeleteSecrets(secret_map, namespace, context_name):
  kubernetes.DeleteResources('secret', list(secret_map.keys()), namespace,
                             context_name)


class _SecretsClient(object):
  """Client implementation for calling Secret Manager to fetch secrets."""

  def __init__(self):
    self.secrets_client = apis.GetClientInstance('secretmanager', 'v1')

  def GetSecretData(self, project, secret_name, mapped_secret, version):
    """Retrieve secret from secret manager."""
    if mapped_secret:
      if mapped_secret.startswith('projects/'):
        # mapping a cross-project secret.
        resource_name = '{}/versions/{}'.format(mapped_secret, version)
      else:
        # if we're mapping a local secret to a valid k8s name
        resource_name = 'projects/{}/secrets/{}/versions/{}'.format(
            project, mapped_secret, version)
    else:
      resource_name = 'projects/{}/secrets/{}/versions/{}'.format(
          project, secret_name, version)
    return self.secrets_client.projects_secrets_versions.Access(
        SECRETS_MESSAGE_MODULE
        .SecretmanagerProjectsSecretsVersionsAccessRequest(name=resource_name))


def IsValidK8sName(name):
  # k8s names must start and end with alphanumeric, only contain alphanumeric,
  # -, and ., and contain at most 253 characters
  return re.match(r'[a-z0-9]([a-z0-9\-\.]{0,251}[a-z0-9])?$', name)

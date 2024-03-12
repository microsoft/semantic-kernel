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
"""Utility for working with secret environment variables and volumes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import re

from googlecloudsdk.command_lib.functions import secrets_config
import six


_SECRET_VERSION_RESOURCE_PATTERN = re.compile(
    '^projects/(?P<project>[^/]+)/secrets/(?P<secret>[^/]+)'
    '/versions/(?P<version>[^/]+)$'
)


def _GetSecretVersionResource(project, secret, version):
  return 'projects/{project}/secrets/{secret}/versions/{version}'.format(
      project=project or '*', secret=secret, version=version
  )


def _CanonicalizedDict(secrets_dict):
  """Canonicalizes all keys in the dict and returns a new dict.

  Args:
    secrets_dict: Existing secrets configuration dict.

  Returns:
    Canonicalized secrets configuration dict.
  """
  return collections.OrderedDict(
      sorted(
          six.iteritems(
              {
                  secrets_config.CanonicalizeKey(key): value
                  for (key, value) in secrets_dict.items()
              }
          )
      )
  )


def GetSecretsAsDict(secret_env_vars, secret_volumes):
  """Converts secrets from message to flattened secrets configuration dict.

  Args:
    secret_env_vars: list of cloudfunctions_v1|v2alpha|v2beta.SecretEnvVars
    secret_volumes: list of cloudfunctions_v1|v2alpha|v2beta.SecretVolumes

  Returns:
    OrderedDict[str, str], Secrets configuration sorted ordered dict.
  """
  secrets_dict = {}

  if secret_env_vars:
    secrets_dict.update(
        {
            sev.key: _GetSecretVersionResource(
                sev.projectId, sev.secret, sev.version
            )
            for sev in secret_env_vars
        }
    )

  if secret_volumes:
    for secret_volume in secret_volumes:
      mount_path = secret_volume.mountPath
      project = secret_volume.projectId
      secret = secret_volume.secret
      if secret_volume.versions:
        for version in secret_volume.versions:
          secrets_config_key = mount_path + ':' + version.path
          secrets_config_value = _GetSecretVersionResource(
              project, secret, version.version
          )
          secrets_dict[secrets_config_key] = secrets_config_value
      else:
        secrets_config_key = mount_path + ':/' + secret
        secrets_config_value = _GetSecretVersionResource(
            project, secret, 'latest'
        )
        secrets_dict[secrets_config_key] = secrets_config_value

  return _CanonicalizedDict(secrets_dict)


def _ParseSecretRef(secret_ref):
  """Splits a secret version resource into its components.

  Args:
    secret_ref: Secret version resource reference.

  Returns:
    A dict with entries for project, secret and version.
  """
  return _SECRET_VERSION_RESOURCE_PATTERN.search(secret_ref).groupdict()


def SecretEnvVarsToMessages(secret_env_vars_dict, messages):
  """Converts secrets from dict to cloud function SecretEnvVar message list.

  Args:
    secret_env_vars_dict: Secret environment variables configuration dict.
      Prefers a sorted ordered dict for consistency.
    messages: The GCF messages module to use.

  Returns:
    A list of cloud function SecretEnvVar message.
  """
  secret_environment_variables = []
  for secret_env_var_key, secret_env_var_value in six.iteritems(
      secret_env_vars_dict
  ):
    secret_ref = _ParseSecretRef(secret_env_var_value)
    secret_environment_variables.append(
        messages.SecretEnvVar(
            key=secret_env_var_key,
            projectId=secret_ref['project'],
            secret=secret_ref['secret'],
            version=secret_ref['version'],
        )
    )
  return secret_environment_variables


def SecretVolumesToMessages(secret_volumes, messages, normalize_for_v2=False):
  # type: (dict[str, str], ) -> (list[messages.SecretVolume])
  """Converts secrets from dict to cloud function SecretVolume message list.

  Args:
    secret_volumes: Secrets volumes configuration dict. Prefers a sorted ordered
      dict for consistency.
    messages: The GCF messages module to use.
    normalize_for_v2: If set, normalizes the SecretVolumes to the format the
      GCFv2 API expects.

  Returns:
    A list of Cloud Function SecretVolume messages.
  """
  secret_volumes_messages = []
  mount_path_to_secrets = collections.defaultdict(list)
  for secret_volume_key, secret_volume_value in secret_volumes.items():
    mount_path, secret_file_path = secret_volume_key.split(':', 1)
    if normalize_for_v2:
      # GCFv2 API doesn't accept a leading / in the secret file path.
      secret_file_path = re.sub(r'^/', '', secret_file_path)

    secret_ref = _ParseSecretRef(secret_volume_value)
    mount_path_to_secrets[mount_path].append({
        'path': secret_file_path,
        'project': secret_ref['project'],
        'secret': secret_ref['secret'],
        'version': secret_ref['version'],
    })

  for mount_path, secrets in sorted(six.iteritems(mount_path_to_secrets)):
    project = secrets[0]['project']
    secret_value = secrets[0]['secret']
    versions = [
        messages.SecretVersion(path=secret['path'], version=secret['version'])
        for secret in secrets
    ]
    secret_volumes_messages.append(
        messages.SecretVolume(
            mountPath=mount_path,
            projectId=project,
            secret=secret_value,
            versions=versions,
        )
    )

  return secret_volumes_messages

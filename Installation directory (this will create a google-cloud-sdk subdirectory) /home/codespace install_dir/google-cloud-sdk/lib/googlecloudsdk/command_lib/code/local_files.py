# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Library for generating the files for local development environment."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import functools
import itertools

from googlecloudsdk.command_lib.code import builders
from googlecloudsdk.command_lib.code import local
from googlecloudsdk.command_lib.code import yaml_helper
from googlecloudsdk.core import yaml
import six

_SKAFFOLD_TEMPLATE = """
apiVersion: skaffold/v2beta5
kind: Config
build:
  artifacts: []
deploy:
  kubectl:
    manifests: []
"""


class LocalRuntimeFiles(object):
  """Generates the developement environment files for a project."""

  def __init__(self, settings):
    """Initialize LocalRuntimeFiles.

    Args:
      settings: Local development settings.
    """
    self._settings = settings

  def KubernetesConfig(self):
    """Create a kubernetes config file.

    Returns:
      Text of a kubernetes config file.
    """
    if self._settings.cpu:
      if isinstance(self._settings.cpu, six.text_type):
        if not self._settings.cpu.endswith('m'):
          raise ValueError('cpu limit must be defined as an integer or as '
                           'millicpus')
        user_cpu = int(self._settings.cpu[:-1]) / 1000.0
      else:
        user_cpu = self._settings.cpu
      cpu_request = min(0.1, user_cpu)
    else:
      cpu_request = None

    code_generators = [
        local.AppContainerGenerator(
            self._settings.service_name, self._settings.image,
            self._settings.env_vars, self._settings.env_vars_secrets,
            self._settings.memory, self._settings.cpu, cpu_request,
            self._settings.readiness_probe),
        local.SecretsGenerator(self._settings.service_name,
                               self._settings.env_vars_secrets,
                               self._settings.volumes_secrets,
                               self._settings.namespace,
                               self._settings.allow_secret_manager)
    ]

    credential_generator = None
    if isinstance(self._settings.credential, local.ServiceAccountSetting):
      credential_generator = local.CredentialGenerator(
          functools.partial(local.GetServiceAccountSecret,
                            self._settings.credential.name))
      code_generators.append(credential_generator)
    elif isinstance(self._settings.credential,
                    local.ApplicationDefaultCredentialSetting):
      credential_generator = local.CredentialGenerator(local.GetUserCredential)
      code_generators.append(credential_generator)

    if self._settings.cloudsql_instances:
      if not credential_generator:
        raise ValueError('A credential generator must be defined when cloudsql '
                         'instances are defined.')
      cloudsql_proxy = local.CloudSqlProxyGenerator(
          self._settings.cloudsql_instances, credential_generator.GetInfo())
      code_generators.append(cloudsql_proxy)

    return _GenerateKubeConfigs(code_generators)

  def SkaffoldConfig(self, kubernetes_file_path):
    """Create a skaffold yaml file.

    Args:
      kubernetes_file_path: Path to the kubernetes config file.

    Returns:
      Text of the skaffold yaml file.
    """
    skaffold_yaml = yaml.load(_SKAFFOLD_TEMPLATE)
    manifests = yaml_helper.GetOrCreate(
        skaffold_yaml, ('deploy', 'kubectl', 'manifests'), constructor=list)
    manifests.append(kubernetes_file_path)
    artifact = {'image': self._settings.image}
    # Need to escape file paths for the yaml encoder. The yaml encoder will
    # interpret \ as the beginning of an escape character. Windows paths may
    # have backslashes.
    artifact['context'] = six.ensure_text(
        self._settings.context.encode('unicode_escape'))

    if isinstance(self._settings.builder, builders.BuildpackBuilder):
      artifact['buildpacks'] = {
          'builder': self._settings.builder.builder,
      }
      if self._settings.builder.devmode:
        artifact['buildpacks']['env'] = ['GOOGLE_DEVMODE=1']
        artifact['sync'] = {'auto': {}}
      if self._settings.builder.trust:
        artifact['buildpacks']['trustBuilder'] = True
    else:
      # Macos needs a relative path or else
      # e2e.surface.code.dev_mac_test.MacE2ETest.testNamespace fails.
      dockerfile_rel_path = self._settings.builder.DockerfileRelPath(
          self._settings.context)
      artifact['docker'] = {
          'dockerfile':
              six.ensure_text(dockerfile_rel_path.encode('unicode_escape'))
      }

    artifacts = yaml_helper.GetOrCreate(
        skaffold_yaml, ('build', 'artifacts'), constructor=list)
    artifacts.append(artifact)

    if self._settings.local_port:
      port_forward_config = {
          'resourceType': 'service',
          'resourceName': self._settings.service_name,
          'port': 8080,
          'localPort': self._settings.local_port
      }
      if self._settings.namespace:
        port_forward_config['namespace'] = self._settings.namespace
      skaffold_yaml['portForward'] = [port_forward_config]

    return yaml.dump(skaffold_yaml)


def _GenerateKubeConfigs(code_generators):
  """Generate Kubernetes yaml configs.

  Args:
    code_generators: Iterable of KubeConfigGenerator.

  Returns:
    Iterable of dictionaries representing kubernetes yaml configs.
  """
  kube_configs = []
  for code_generator in code_generators:
    kube_configs.extend(code_generator.CreateConfigs())

  deployments = [
      config for config in kube_configs if config['kind'] == 'Deployment'
  ]
  for deployment, code_generator in itertools.product(deployments,
                                                      code_generators):
    code_generator.ModifyDeployment(deployment)

  for deployment in deployments:
    containers = yaml_helper.GetAll(deployment,
                                    ('spec', 'template', 'spec', 'containers'))

    for container, code_generator in itertools.product(containers,
                                                       code_generators):
      code_generator.ModifyContainer(container)

  return yaml.dump_all(kube_configs)

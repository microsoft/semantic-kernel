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
"""Utilities for generating cloud-based dev loop configs."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.command_lib.code import builders
from googlecloudsdk.command_lib.code import yaml_helper
from googlecloudsdk.command_lib.code.cloud import cloud
from googlecloudsdk.core import yaml

import six

_SKAFFOLD_TEMPLATE = """
apiVersion: skaffold/v3alpha1
kind: Config
build:
  artifacts: []
  local:
    push: true
manifests:
  rawYaml: []
deploy:
  cloudrun: {}
"""


class CloudRuntimeFiles(object):
  """Generates the development environment files for a project."""

  def __init__(self, settings):
    self._settings = settings

  def KubernetesConfig(self):
    return yaml.dump(
        encoding.MessageToDict(cloud.GenerateService(self._settings)))

  def SkaffoldConfig(self, service_file_path):
    """Generate the Skaffold yaml for the deploy."""
    skaffold_yaml = yaml.load(_SKAFFOLD_TEMPLATE)
    manifests = yaml_helper.GetOrCreate(
        skaffold_yaml, ('manifests', 'rawYaml'), constructor=list)
    manifests.append(service_file_path)
    artifact = {'image': self._settings.image}
    if isinstance(self._settings.builder, builders.BuildpackBuilder):
      artifact['buildpacks'] = {
          'builder': self._settings.builder.builder,
      }
      # sync is not currently supported for Cloud Run
      artifact['sync'] = {'auto': False}
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
    skaffold_yaml['deploy']['cloudrun']['projectid'] = self._settings.project
    skaffold_yaml['deploy']['cloudrun']['region'] = self._settings.region

    if self._settings.local_port:
      port_forward_config = {
          'resourceType': 'service',
          'resourceName': self._settings.service_name,
          'port': 8080,
          'localPort': self._settings.local_port,
      }
      skaffold_yaml['portForward'] = [port_forward_config]
    return yaml.dump(skaffold_yaml)

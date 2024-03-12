# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Helper functions for interacting with the binauthz API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

# See //third_party/py/googlecloudsdk/command_lib/container/resources.yaml
LOCATIONS_POLICY = 'binaryauthorization.systempolicy'
PROJECTS_COLLECTION = 'binaryauthorization.projects'
PROJECTS_POLICY_COLLECTION = 'binaryauthorization.projects.policy'
PROJECTS_ATTESTORS_COLLECTION = 'binaryauthorization.projects.attestors'
PROJECTS_CV_CONFIGS_COLLECTION = 'binaryauthorization.projects.continuousValidationConfig'


def GetProjectRef():
  return resources.REGISTRY.Parse(
      None,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection=PROJECTS_COLLECTION,
  )


def GetPolicyRef():
  return resources.REGISTRY.Parse(
      None,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection=PROJECTS_POLICY_COLLECTION,
  )


def GetSystemPolicyRef(location):
  return resources.REGISTRY.Parse(
      None,
      params={'locationsId': location},
      collection=LOCATIONS_POLICY)


def GetAttestorRef(attestor_name):
  return resources.REGISTRY.Parse(
      attestor_name,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection=PROJECTS_ATTESTORS_COLLECTION,
  )


def GetCvConfigRef():
  return resources.REGISTRY.Parse(
      None,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection=PROJECTS_CV_CONFIGS_COLLECTION,
  )

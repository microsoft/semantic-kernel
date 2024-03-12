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
"""Shared resource flags for Cloud Build commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.core import properties


def RegionAttributeConfig():
  fallthroughs = [
      deps.PropertyFallthrough(properties.VALUES.builds.region)
  ]
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      fallthroughs=fallthroughs,
      help_text='The Cloud location for the {resource}.')


def GetTriggerResourceSpec():
  return concepts.ResourceSpec(
      'cloudbuild.projects.locations.triggers',
      api_version='v1',
      resource_name='trigger',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      triggersId=TriggerAttributeConfig())


def TriggerAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='trigger',
      help_text='Build Trigger ID')


def GetWorkflowResourceSpec():
  return concepts.ResourceSpec(
      'cloudbuild.projects.locations.workflows',
      api_version='v2',
      resource_name='workflow',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      workflowsId=WorkflowAttributeConfig())


def WorkflowAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='workflow', help_text='Workflow ID')


def GetGitLabConfigResourceSpec():
  return concepts.ResourceSpec(
      'cloudbuild.projects.locations.gitLabConfigs',
      api_version='v1',
      resource_name='gitLabConfig',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=RegionAttributeConfig(),
      gitLabConfigsId=GitLabConfigAttributeConfig())


def GitLabConfigAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='config', help_text='Config Name')

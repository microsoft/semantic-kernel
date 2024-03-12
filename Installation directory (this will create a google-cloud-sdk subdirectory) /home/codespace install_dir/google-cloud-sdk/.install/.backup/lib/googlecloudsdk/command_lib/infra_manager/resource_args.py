# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Shared resource flags for Config Manager commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties


def DeploymentAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='deployment', help_text='The deployment for the {resource}.'
  )


def RevisionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='revision', help_text='The revision for the {resource}.'
  )


def LocationAttributeConfig():
  fallthroughs = [
      deps.PropertyFallthrough(properties.VALUES.inframanager.location)
  ]
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      fallthroughs=fallthroughs,
      help_text='The Cloud location for the {resource}.',
  )


def PreviewAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='preview', help_text='The preview for the {resource}.'
  )


def GetDeploymentResourceSpec():
  return concepts.ResourceSpec(
      'config.projects.locations.deployments',
      resource_name='deployment',
      deploymentsId=DeploymentAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def GetRevisionResourceSpec():
  return concepts.ResourceSpec(
      'config.projects.locations.deployments.revisions',
      resource_name='revision',
      revisionsId=RevisionAttributeConfig(),
      deploymentsId=DeploymentAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def GetPreviewResourceSpec():
  return concepts.ResourceSpec(
      'config.projects.locations.previews',
      resource_name='preview',
      previewsId=PreviewAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def GetLocationResourceSpec():
  return concepts.ResourceSpec(
      'config.projects.locations',
      resource_name='location',
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      disable_auto_completers=False,
  )


def GetDeploymentResourceArgSpec(group_help):
  """Gets a resource presentation spec for a config manager deployment.

  Args:
    group_help: string, the help text for the entire arg group.

  Returns:
    ResourcePresentationSpec for a config manager deployment resource argument.
  """
  name = 'DEPLOYMENT'
  return presentation_specs.ResourcePresentationSpec(
      name, GetDeploymentResourceSpec(), group_help, required=True
  )


def GetRevisionResourceArgSpec(group_help):
  """Gets a resource presentation spec for a config manager revision.

  Args:
    group_help: string, the help text for the entire arg group.

  Returns:
    ResourcePresentationSpec for a config manager revision resource argument.
  """
  name = 'REVISION'
  return presentation_specs.ResourcePresentationSpec(
      name, GetRevisionResourceSpec(), group_help, required=True
  )


def GetPreviewResourceArgSpec(
    group_help, required=True, flag_name_overrides=None
):
  """Gets a resource presentation spec for a config manager preview.

  Args:
    group_help: string, the help text for the entire arg group.
    required:
    flag_name_overrides:

  Returns:
    ResourcePresentationSpec for a config manager preview resource argument.
  """
  name = 'PREVIEW'
  return presentation_specs.ResourcePresentationSpec(
      name,
      GetPreviewResourceSpec(),
      group_help,
      required=required,
      flag_name_overrides=flag_name_overrides,
  )


def GetLocationResourceArgSpec(group_help):
  """Gets a resource presentation spec for a config manager preview.

  Args:
    group_help: string, the help text for the entire arg group.

  Returns:
    ResourcePresentationSpec for a config manager preview resource argument.
  """
  name = '--location'
  return presentation_specs.ResourcePresentationSpec(
      name,
      GetLocationResourceSpec(),
      group_help,
      required=True,
  )

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
"""Shared resource flags for OS Config commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def PatchJobAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='patch_job', help_text='An OS patch job.')


def GetPatchJobResourceSpec():
  return concepts.ResourceSpec(
      'osconfig.projects.patchJobs',
      resource_name='patch_job',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      patchJobsId=PatchJobAttributeConfig())


def CreatePatchJobResourceArg(verb, plural=False):
  """Creates a resource argument for a OS Config patch job.

  Args:
    verb: str, The verb to describe the resource, such as 'to describe'.
    plural: bool, If True, use a resource argument that returns a list.

  Returns:
    PresentationSpec for the resource argument.
  """
  noun = 'Patch job' + ('s' if plural else '')
  return presentation_specs.ResourcePresentationSpec(
      'patch_job',
      GetPatchJobResourceSpec(),
      '{} {}'.format(noun, verb),
      required=True,
      plural=plural,
      prefixes=False)


def AddPatchJobResourceArg(parser, verb, plural=False):
  """Creates a resource argument for a OS Config patch job.

  Args:
    parser: The parser for the command.
    verb: str, The verb to describe the resource, such as 'to describe'.
    plural: bool, If True, use a resource argument that returns a list.
  """
  concept_parsers.ConceptParser([CreatePatchJobResourceArg(
      verb, plural)]).AddToParser(parser)


def PatchDeploymentAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='patch_deployment', help_text='An OS patch deployment.')


def GetPatchDeploymentResourceSpec():
  return concepts.ResourceSpec(
      'osconfig.projects.patchDeployments',
      resource_name='patch_deployment',
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      patchDeploymentsId=PatchDeploymentAttributeConfig())


def CreatePatchDeploymentResourceArg(verb, plural=False):
  """Creates a resource argument for a OS Config patch deployment.

  Args:
    verb: str, The verb to describe the resource, such as 'to describe'.
    plural: bool, If True, use a resource argument that returns a list.

  Returns:
    PresentationSpec for the resource argument.
  """
  noun = 'Patch deployment' + ('s' if plural else '')
  return presentation_specs.ResourcePresentationSpec(
      'patch_deployment',
      GetPatchDeploymentResourceSpec(),
      '{} {}'.format(noun, verb),
      required=True,
      plural=plural,
      prefixes=False)


def AddPatchDeploymentResourceArg(parser, verb, plural=False):
  """Creates a resource argument for a OS Config patch deployment.

  Args:
    parser: The parser for the command.
    verb: str, The verb to describe the resource, such as 'to describe'.
    plural: bool, If True, use a resource argument that returns a list.
  """
  concept_parsers.ConceptParser(
      [CreatePatchDeploymentResourceArg(verb, plural)]).AddToParser(parser)

# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""A library containing resource args used by Transcoder commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


def LocationAttributeConfig():
  fallthroughs = [
      deps.PropertyFallthrough(properties.VALUES.transcoder.location)
  ]
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='Transcoder location for resources',
      fallthroughs=fallthroughs)


def TemplateAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='template_id', help_text='Transcoder template id for job')


def JobAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='job_name', help_text='Transcoder job name')


def GetLocationResourceSpec():
  return concepts.ResourceSpec(
      'transcoder.projects.locations',
      resource_name='location',
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetJobResourceSpec():
  """Constructs and returns the Resource specification for Job."""

  return concepts.ResourceSpec(
      'transcoder.projects.locations.jobs',
      resource_name='job',
      jobsId=JobAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      disable_auto_completers=False)


def GetTemplateResourceSpec():
  """Constructs and returns the Resource specification for Job Template."""

  return concepts.ResourceSpec(
      'transcoder.projects.locations.jobTemplates',
      resource_name='jobTemplate',
      jobTemplatesId=TemplateAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=LocationAttributeConfig(),
      disable_auto_completers=False)


def AddLocationResourceArg(parser):
  """Constructs and returns the Location Resource Argument."""
  return concept_parsers.ConceptParser.ForResource(
      '--location',
      GetLocationResourceSpec(),
      'Transcoder location',
      required=True).AddToParser(parser)


def AddJobResourceArg(parser):
  """Constructs and returns the Job Resource Argument."""

  return concept_parsers.ConceptParser.ForResource(
      'job_name',
      GetJobResourceSpec(),
      'Transcoder Job name',
      required=True).AddToParser(parser)


def AddTemplateResourceArg(parser):
  """Constructs and returns Job Template Resource Argument."""

  return concept_parsers.ConceptParser.ForResource(
      'template_id',
      GetTemplateResourceSpec(),
      'Transcoder job template id',
      required=True).AddToParser(parser)

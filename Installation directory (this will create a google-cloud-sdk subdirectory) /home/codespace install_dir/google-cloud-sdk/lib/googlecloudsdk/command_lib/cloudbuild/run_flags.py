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
"""Set up flags for creating a PipelineRun/TaskRun."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.cloudbuild import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers


def AddsCreateFlags(parser):
  parser.add_argument(
      '--file',
      required=True,
      help='The YAML file to use as the PipelineRun/TaskRun configuration file.'
  )
  AddsRegionResourceArg(parser)


def AddsRegionResourceArg(parser, is_required=True):
  """Add region resource argument to parser."""
  region_resource_spec = concepts.ResourceSpec(
      'cloudbuild.projects.locations',
      resource_name='region',
      locationsId=resource_args.RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)

  concept_parsers.ConceptParser.ForResource(
      '--region',
      region_resource_spec,
      'Region for Cloud Build.',
      required=is_required).AddToParser(parser)


def AddsRunFlags(parser):
  """Add flags related to a run to parser."""
  parser.add_argument('RUN_ID', help='The ID of the PipelineRun/TaskRun.')
  parser.add_argument(
      '--type',
      choices=[
          'pipelinerun',
          'taskrun',
      ],
      default='pipelinerun',
      help='Type of Run.',
  )
  AddsRegionResourceArg(parser)

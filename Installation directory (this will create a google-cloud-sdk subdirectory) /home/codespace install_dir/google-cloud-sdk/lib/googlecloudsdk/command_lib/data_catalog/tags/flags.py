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

"""Additional flags for data-catalog tags commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def AddCreateUpdateTagFlags():
  """Hook for adding flags to tags create and update."""
  resource_spec = concepts.ResourceSpec.FromYaml(
      yaml_data.ResourceYAMLData.FromPath('data_catalog.tag_template')
      .GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='--tag-template',
      concept_spec=resource_spec,
      prefixes=True,
      required=True,
      flag_name_overrides={
          'project': '--tag-template-project',
      },
      group_help="""\
Tag template. `--tag-template-location` defaults to the tag's location.
`--tag-template-project` defaults to the tag's project.
      """
  )
  tag_template_arg = concept_parsers.ConceptParser(
      [presentation_spec],
      command_level_fallthroughs={
          '--tag-template.location': ['--location'],
          '--tag-template.project': ['--project'],
      },
  )

  return [tag_template_arg]

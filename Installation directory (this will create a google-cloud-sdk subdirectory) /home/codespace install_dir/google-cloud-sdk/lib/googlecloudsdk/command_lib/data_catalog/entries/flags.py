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
"""Flags for data-catalog commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def GetEntryArg():
  entry_data = yaml_data.ResourceYAMLData.FromPath('data_catalog.entry')
  resource_spec = concepts.ResourceSpec.FromYaml(
      entry_data.GetData(), is_positional=True)
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='entry', concept_spec=resource_spec, group_help='Entry to update.')
  return concept_parsers.ConceptParser([presentation_spec])


def GetLookupEntryArg():
  """Returns the argument for looking up an entry."""
  help_text = """\
The name of the target resource whose entry to update. This can be either the
Google Cloud Platform resource name or the SQL name of a Google Cloud Platform
resource. This flag allows one to update the entry corresponding to the lookup
of the given resource, without needing to specify the entry directly."""
  return base.Argument(
      '--lookup-entry',
      metavar='RESOURCE',
      help=help_text)


def AddEntryUpdateArgs():
  # Normally these arguments would be added in a mutex group, but the help
  # text would look confusing in this case since --lookup-entry shows up
  # under positional arguments despite being a flag.
  return [GetEntryArg(), GetLookupEntryArg()]

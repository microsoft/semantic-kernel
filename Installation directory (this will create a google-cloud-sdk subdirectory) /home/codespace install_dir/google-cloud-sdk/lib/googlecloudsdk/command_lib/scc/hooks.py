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
"""Declarative Hooks for Cloud SCC surface arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import json
import re

from apitools.base.py import encoding
from googlecloudsdk.api_lib.scc import securitycenter_client as sc_client
from googlecloudsdk.command_lib.scc.errors import InvalidSCCInputError
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.args import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml


class InvalidCustomConfigFileError(core_exceptions.Error):
  """Error if a custom config file is improperly formatted."""


class InvalidTestDataFileError(core_exceptions.Error):
  """Error if a test data file is improperly formatted."""


class InvalidResourceFileError(core_exceptions.Error):
  """Error if a resource file is improperly formatted."""


def AppendOrgArg():
  """Add Organization as a positional resource."""
  org_spec_data = yaml_data.ResourceYAMLData.FromPath("scc.organization")
  arg_specs = [
      resource_args.GetResourcePresentationSpec(
          verb="to be used for the SCC (Security Command Center) command",
          name="organization",
          required=True,
          prefixes=False,
          positional=True,
          resource_data=org_spec_data.GetData()),
  ]
  return [concept_parsers.ConceptParser(arg_specs, [])]


def AppendParentArg():
  """Add Parent as a positional resource."""
  parent_spec_data = yaml_data.ResourceYAMLData.FromPath("scc.parent")
  arg_specs = [
      resource_args.GetResourcePresentationSpec(
          verb="to be used for the `gcloud scc` command",
          name="parent",
          help_text="{name} organization, folder, or project in the Google Cloud resource hierarchy {verb}. Specify the argument as either [RESOURCE_TYPE/RESOURCE_ID] or [RESOURCE_ID], as shown in the preceding examples.",
          required=True,
          prefixes=False,
          positional=True,
          resource_data=parent_spec_data.GetData()),
  ]
  return [concept_parsers.ConceptParser(arg_specs, [])]


def SourcePropertiesHook(source_properties_dict):
  """Hook to capture "key1=val1,key2=val2" as SourceProperties object."""
  messages = sc_client.GetMessages()
  return encoding.DictToMessage(source_properties_dict,
                                messages.Finding.SourcePropertiesValue)


def SecurityMarksHook(parsed_dict):
  """Hook to capture "key1=val1,key2=val2" as SecurityMarks object."""
  messages = sc_client.GetMessages()
  security_marks = messages.SecurityMarks()
  security_marks.marks = encoding.DictToMessage(
      parsed_dict, messages.SecurityMarks.MarksValue)
  return security_marks


def GetOrganization(args):
  """Prepend organizations/ to org if necessary."""
  resource_pattern = re.compile("organizations/[0-9]+")
  id_pattern = re.compile("[0-9]+")
  if not args.organization:
    organization = properties.VALUES.scc.organization.Get()
  else:
    organization = args.organization
  if organization is None:
    raise InvalidSCCInputError("Could not find Organization argument. Please "
                               "provide the organization argument.")
  if (not resource_pattern.match(organization) and
      not id_pattern.match(organization)):
    raise InvalidSCCInputError(
        "Organization must match either organizations/[0-9]+ or [0-9]+.")
  if resource_pattern.match(organization):
    return organization
  return "organizations/" + organization


def GetDefaultOrganization():
  """Prepend organizations/ to org if necessary."""
  resource_pattern = re.compile("organizations/[0-9]+")
  id_pattern = re.compile("[0-9]+")
  organization = properties.VALUES.scc.organization.Get()
  if (not resource_pattern.match(organization) and
      not id_pattern.match(organization)):
    raise InvalidSCCInputError(
        "Organization must match either organizations/[0-9]+ or [0-9]+.")
  if resource_pattern.match(organization):
    return organization
  return "organizations/" + organization


def GetDefaultParent():
  """Converts user input to one of: organization, project, or folder."""
  organization_resource_pattern = re.compile("organizations/[0-9]+$")
  id_pattern = re.compile("[0-9]+")
  parent = properties.VALUES.scc.parent.Get()
  if id_pattern.match(parent):
    # Prepend organizations/ if only number value is provided.
    parent = "organizations/" + parent
  if not (organization_resource_pattern.match(parent) or
          parent.startswith("projects/") or parent.startswith("folders/")):
    raise InvalidSCCInputError(
        """Parent must match either [0-9]+, organizations/[0-9]+, projects/.*
      or folders/.*.""")
  return parent


def CleanUpUserInput(mask):
  """Removes spaces from a field mask provided by user."""
  return mask.replace(" ", "")


def GetParentFromResourceName(resource_name):
  resource_pattern = re.compile("(organizations|projects|folders)/.*")
  if not resource_pattern.match(resource_name):
    raise InvalidSCCInputError(
        "When providing a full resource path, it must also include the pattern "
        "the organization, project, or folder prefix.")
  list_organization_components = resource_name.split("/")
  return list_organization_components[0] + "/" + list_organization_components[1]


def GetSourceParentFromResourceName(resource_name):
  resource_pattern = re.compile(
      "(organizations|projects|folders)/.*/sources/[0-9]+")
  if not resource_pattern.match(resource_name):
    raise InvalidSCCInputError(
        "When providing a full resource path, it must also include "
        "the organization, project, or folder prefix.")
  list_source_components = resource_name.split("/")
  return (GetParentFromResourceName(resource_name) + "/" +
          list_source_components[2] + "/" + list_source_components[3])


def ProcessCustomEtdConfigFile(file_contents):
  """Processes the configuration file for the ETD custom module."""
  messages = sc_client.GetMessages()
  try:
    config = json.loads(file_contents)
    return encoding.DictToMessage(
        config, messages.EventThreatDetectionCustomModule.ConfigValue
    )
  except json.JSONDecodeError as e:
    raise InvalidCustomConfigFileError(
        "Error parsing custom config file [{}]".format(e)
    )


def ProcessCustomConfigFile(file_contents):
  """Process the custom configuration file for the custom module."""
  messages = sc_client.GetMessages()
  try:
    config_dict = yaml.load(file_contents)
    return encoding.DictToMessage(
        config_dict, messages.GoogleCloudSecuritycenterV1CustomConfig
    )
  except yaml.YAMLParseError as ype:
    raise InvalidCustomConfigFileError(
        "Error parsing custom config file [{}]".format(ype))


def ExtractTestData(test_data_input):
  """Extract test data into list structure, accept both list and dict."""
  if isinstance(test_data_input, list):
    return test_data_input
  elif isinstance(test_data_input, dict):
    if "testData" in test_data_input:
      return test_data_input["testData"]
    else:
      return None
  else:
    if not test_data_input:
      raise InvalidTestDataFileError(
          "Error parsing test data file: no data records defined in file"
      )


def ProcessTestResourceDataFile(file_contents):
  """Process the test resource data file for the custom module to test against."""
  messages = sc_client.GetMessages()
  try:
    test_data = ExtractTestData(yaml.load(file_contents))
    test_data_messages = []
    for field in test_data:
      test_data_messages.append(
          encoding.DictToMessage(field, messages.TestData)
      )

    return test_data_messages
  except yaml.YAMLParseError as ype:
    raise InvalidTestDataFileError(
        "Error parsing test data file [{}]".format(ype)
    )


def ProcessSimulatedResourceFile(file_contents):
  """Process the simulate resource data file for the custom module to validate against."""
  messages = sc_client.GetMessages()
  try:
    resource_dict = yaml.load(file_contents)

    return encoding.DictToMessage(resource_dict, messages.SimulatedResource)
  except yaml.YAMLParseError as ype:
    raise InvalidResourceFileError(
        "Error parsing resource file [{}]".format(ype)
    )

def ProcessTFPlanFile(file_contents):
  """Process the custom configuration file for the custom module."""
  try:
    config = json.loads(file_contents)
    return json.dumps(config).encode("utf-8")
  except json.JSONDecodeError as e:
    raise InvalidCustomConfigFileError(
        "Error parsing terraform plan file [{}]".format(e)
    )

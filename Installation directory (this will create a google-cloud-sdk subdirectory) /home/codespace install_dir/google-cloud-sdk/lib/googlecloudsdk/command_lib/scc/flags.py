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

"""Shared flags definitions for multiple commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import re

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.scc import errors
from googlecloudsdk.command_lib.util.args import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties

PAGE_TOKEN_FLAG = base.Argument(
    "--page-token",
    help="""
      Response objects will return a non-null value for page-token to
      indicate that there is at least one additional page of data. User can
      either directly request that page by specifying the page-token
      explicitly or let gcloud fetch one-page-at-a-time.""",
)

READ_TIME_FLAG = base.Argument(
    "--read-time",
    help="""
      Time used as a reference point when filtering. Absence of this field
      will default to the API's version of NOW. See $ gcloud topic datetimes
      for information on supported time formats.""",
)

API_VERSION_FLAG = base.ChoiceArgument(
    "--api-version",
    choices=["v1", "v2enabled"],
    help_str="""
      This is a temporary flag to be used for testing the Security Command
      Center v2 api before its launch.""",
    default="v1",
    hidden=True,
)

LOCATION_FLAG = base.Argument(
    "--location",
    help="""
      When data residency controls are enabled, this attribute specifies the location in which
      the resource is located and applicable. The `location` attribute can be
      provided as part of the fully specified resource name or with the `--location`
      argument on the command line. The default location is `global`.

      The default location on this command is unrelated to the default location
      that is specified when data residency controls are enabled
      for Security Command Center.""",
    default="global",
)


def AppendParentArg():
  """Add Parent as a positional resource."""
  parent_spec_data = {
      "name": "parent",
      "collection": "securitycenter.organizations",
      "attributes": [{
          "parameter_name": "organizationsId",
          "attribute_name": "parent",
          "help": """(Optional) Provide the full resource name,
          [RESOURCE_TYPE/RESOURCE_ID], of the parent organization, folder, or
          project resource. For example, `organizations/123` or `parent/456`.
          If the parent is an organization, you can specify just the
          organization ID. For example, `123`.""",
          "fallthroughs": [{
              "hook": "googlecloudsdk.command_lib.scc.flags:GetDefaultParent",
              "hint": """Set the parent property in configuration using `gcloud
              config set scc/parent` if it is not specified in command line""",
          }],
      }],
      "disable_auto_completers": "false",
  }

  arg_specs = [
      resource_args.GetResourcePresentationSpec(
          verb="to be used for the `gcloud scc` command",
          name="parent",
          help_text=(
              "{name} organization, folder, or project in the Google Cloud"
              " resource hierarchy {verb}. Specify the argument as either"
              " [RESOURCE_TYPE/RESOURCE_ID] or [RESOURCE_ID], as shown in the"
              " preceding examples."
          ),
          required=True,
          prefixes=False,
          positional=True,
          resource_data=parent_spec_data,
      ),
  ]
  return [concept_parsers.ConceptParser(arg_specs, [])]


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
    raise errors.InvalidSCCInputError(
        """Parent must match either [0-9]+, organizations/[0-9]+, projects/.*
      or folders/.*.""")
  return parent

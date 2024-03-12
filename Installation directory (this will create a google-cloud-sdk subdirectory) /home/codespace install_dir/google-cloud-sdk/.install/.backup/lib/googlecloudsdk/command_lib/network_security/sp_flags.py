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
"""Flags for Security Profile Threat Prevention commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.security_profiles.threat_prevention import sp_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs

DEFAULT_ACTIONS = ["DEFAULT", "ALLOW", "ALERT", "DENY"]
DEFAULT_PROFILE_TYPES = ["THREAT_PREVENTION"]


def AddSeverityorThreatIDArg(parser, required=True):
  """Adds --severities or --threat-ids flag."""
  severity_threatid_args = parser.add_group(mutex=True, required=required)
  severity_threatid_args.add_argument(
      "--severities",
      type=arg_parsers.ArgList(),
      metavar="SEVERITY_LEVEL",
      help=(
          "List of comma-separated severities where each value in the list"
          " indicates the severity of the threat."
      ),
  )
  severity_threatid_args.add_argument(
      "--threat-ids",
      type=arg_parsers.ArgList(),
      metavar="THREAT-ID",
      help=(
          "List of comma-separated threat identifiers where each identifier in"
          " the list is a vendor-specified Signature ID representing a threat"
          " type. "
      ),
  )


def AddActionArg(parser, actions=None, required=True):
  choices = actions or DEFAULT_ACTIONS
  parser.add_argument(
      "--action",
      required=required,
      choices=choices,
      help="Action associated with severity or threat-id",
  )


def AddProfileDescription(parser, required=False):
  parser.add_argument(
      "--description",
      required=required,
      help="Brief description of the security profile",
  )


def AddSecurityProfileResource(parser, release_track):
  """Adds Security Profile Threat Prevention type."""
  name = "security_profile"
  resource_spec = concepts.ResourceSpec(
      resource_collection=(
          "networksecurity.organizations.locations.securityProfiles"
      ),
      resource_name="security_profile",
      api_version=sp_api.GetApiVersion(release_track),
      organizationsId=concepts.ResourceParameterAttributeConfig(
          "organization",
          "Organization ID to which the changes should apply.",
          parameter_name="organizationsId",
      ),
      locationsId=concepts.ResourceParameterAttributeConfig(
          "location",
          "location of the {resource} - Global.",
          parameter_name="locationsId",
      ),
      securityProfilesId=concepts.ResourceParameterAttributeConfig(
          "security_profile",
          "Name of the {resource}.",
          parameter_name="securityProfilesId",
      ),
  )
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help="Security Profile Name.",
  )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)

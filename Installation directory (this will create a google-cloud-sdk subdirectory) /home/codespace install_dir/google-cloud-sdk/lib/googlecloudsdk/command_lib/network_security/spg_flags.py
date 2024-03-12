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
"""Flags for Security Profile Group commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.security_profile_groups import spg_api
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import resources

_SECURITY_PROFILE_RESOURCE_COLLECTION = (
    "networksecurity.organizations.locations.securityProfiles"
)
_SECURITY_PROFILE_GROUP_RESOURCE_COLLECTION = (
    "networksecurity.organizations.locations.securityProfileGroups"
)
_THREAT_PREVENTION_PROFILE_RESOURCE_NAME = "--threat-prevention-profile"
_SECURITY_PROFILE_GROUP_RESOURCE_NAME = "SECURITY_PROFILE_GROUP"


def AddProfileGroupDescription(parser, required=False):
  parser.add_argument(
      "--description",
      required=required,
      help="Brief description of the security profile group",
  )


def AddThreatPreventionProfileResource(
    parser,
    release_track,
    help_text="Path to Security Profile resource.",
    required=False,
):
  """Adds Security Profile resource."""
  api_version = spg_api.GetApiVersion(release_track)
  collection_info = resources.REGISTRY.Clone().GetCollectionInfo(
      _SECURITY_PROFILE_GROUP_RESOURCE_COLLECTION, api_version
  )
  resource_spec = concepts.ResourceSpec(
      _SECURITY_PROFILE_RESOURCE_COLLECTION,
      "Security Profile",
      api_version=api_version,
      organizationsId=concepts.ResourceParameterAttributeConfig(
          "security-profile-organization",
          "Organization ID of the Security Profile.",
          parameter_name="organizationsId",
          fallthroughs=[
              deps.ArgFallthrough("--organization"),
              deps.FullySpecifiedAnchorFallthrough(
                  [deps.ArgFallthrough(
                      _SECURITY_PROFILE_GROUP_RESOURCE_COLLECTION
                  )],
                  collection_info,
                  "organizationsId",
              ),
          ],
      ),
      locationsId=concepts.ResourceParameterAttributeConfig(
          "security-profile-location",
          """
          Location of the {resource}.
          NOTE: Only `global` security profiles are supported.
          """,
          parameter_name="locationsId",
          fallthroughs=[
              deps.ArgFallthrough("--location"),
              deps.FullySpecifiedAnchorFallthrough(
                  [deps.ArgFallthrough(
                      _SECURITY_PROFILE_GROUP_RESOURCE_COLLECTION
                  )],
                  collection_info,
                  "locationsId",
              ),
          ],
      ),
      securityProfilesId=concepts.ResourceParameterAttributeConfig(
          "security_profile",
          "Name of security profile {resource}.",
          parameter_name="securityProfilesId",
      ),
  )
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=_THREAT_PREVENTION_PROFILE_RESOURCE_NAME,
      concept_spec=resource_spec,
      required=required,
      group_help=help_text,
  )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddSecurityProfileGroupResource(parser, release_track):
  """Adds Security Profile Group."""
  name = _SECURITY_PROFILE_GROUP_RESOURCE_NAME
  resource_spec = concepts.ResourceSpec(
      resource_collection=_SECURITY_PROFILE_GROUP_RESOURCE_COLLECTION,
      resource_name="security_profile_group",
      api_version=spg_api.GetApiVersion(release_track),
      organizationsId=concepts.ResourceParameterAttributeConfig(
          "organization",
          "Organization ID of Security Profile Group",
          parameter_name="organizationsId",
      ),
      locationsId=concepts.ResourceParameterAttributeConfig(
          "location",
          "location of the {resource} - Global.",
          parameter_name="locationsId",
      ),
      securityProfileGroupsId=concepts.ResourceParameterAttributeConfig(
          "security_profile_group",
          "Name of security profile group {resource}.",
          parameter_name="securityProfileGroupsId",
      ),
  )
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=name,
      concept_spec=resource_spec,
      required=True,
      group_help="Security Profile Group Name.",
  )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)

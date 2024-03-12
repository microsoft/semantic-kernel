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
"""Flags for Firewall Plus Endpoint Association commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.network_security.firewall_endpoints import activation_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import resources


ASSOCIATION_RESOURCE_NAME = "FIREWALL_ENDPOINT_ASSOCIATION"
ASSOCIATION_RESOURCE_COLLECTION = (
    "networksecurity.projects.locations.firewallEndpointAssociations"
)
ASSOCIATION_PARENT_RESOURCE_COLLECTION = "networksecurity.projects.locations"
ENDPOINT_RESOURCE_NAME = "FIREWALL_ENDPOINT"
TLS_INSPECTION_POLICY_RESOURCE_NAME = "--tls-inspection-policy"
ENDPOINT_RESOURCE_COLLECTION = (
    "networksecurity.organizations.locations.firewallEndpoints"
)
TLS_INSPECTION_POLICY_RESOURCE_COLLECTION = (
    "networksecurity.projects.locations.tlsInspectionPolicies"
)


def AddAssociationResource(release_track, parser):
  """Adds Association resource."""
  api_version = activation_api.GetApiVersion(release_track)
  resource_spec = concepts.ResourceSpec(
      ASSOCIATION_RESOURCE_COLLECTION,
      "firewall endpoint association",
      api_version=api_version,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=concepts.ResourceParameterAttributeConfig(
          "zone",
          "Zone of the {resource}.",
          parameter_name="locationsId",
      ),
      firewallEndpointAssociationsId=concepts.ResourceParameterAttributeConfig(
          "association-name",
          "Name of the {resource}",
          parameter_name="firewallEndpointAssociationsId",
      ),
  )
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=ASSOCIATION_RESOURCE_NAME,
      concept_spec=resource_spec,
      required=True,
      group_help="Firewall Plus.",
  )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddAssociationIDArg(
    parser,
    help_text="Name to give the association. If not specified, an auto-generated UUID will be used.",
):
  parser.add_argument("association_id", help=help_text, nargs="?", default=None)


def AddEndpointResource(release_track, parser):
  """Adds Firewall Plus endpoint resource."""
  api_version = activation_api.GetApiVersion(release_track)
  collection_info = resources.REGISTRY.Clone().GetCollectionInfo(
      ASSOCIATION_RESOURCE_COLLECTION, api_version
  )
  resource_spec = concepts.ResourceSpec(
      ENDPOINT_RESOURCE_COLLECTION,
      "firewall endpoint",
      api_version=api_version,
      organizationsId=concepts.ResourceParameterAttributeConfig(
          "organization",
          "Organization ID to which the changes should apply.",
          parameter_name="organizationsId",
      ),
      locationsId=concepts.ResourceParameterAttributeConfig(
          "endpoint-zone",
          "Zone of the {resource}.",
          parameter_name="locationsId",
          fallthroughs=[
              deps.ArgFallthrough("--zone"),
              deps.FullySpecifiedAnchorFallthrough(
                  [deps.ArgFallthrough(ASSOCIATION_RESOURCE_NAME)],
                  collection_info,
                  "locationsId",
              ),
          ],
      ),
      firewallEndpointsId=concepts.ResourceParameterAttributeConfig(
          "endpoint-name",
          "Name of the {resource}",
          parameter_name="firewallEndpointsId",
      ),
  )
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name="--endpoint",
      concept_spec=resource_spec,
      required=True,
      group_help="Firewall Plus.",
  )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddNetworkResource(parser):
  """Adds network resource."""
  resource_spec = concepts.ResourceSpec(
      "compute.networks",
      "network",
      api_version="v1",
      project=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      network=concepts.ResourceParameterAttributeConfig(
          "network-name",
          "Name of the {resource}",
          parameter_name="network",
      ),
  )
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name="--network",
      concept_spec=resource_spec,
      required=True,
      group_help="Firewall Plus.",
  )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddMaxWait(
    parser,
    default_max_wait,
    help_text="Time to synchronously wait for the operation to complete, after which the operation continues asynchronously. Ignored if --no-async isn't specified. See $ gcloud topic datetimes for information on time formats.",
):
  """Adds --max-wait flag."""
  parser.add_argument(
      "--max-wait",
      dest="max_wait",
      required=False,
      default=default_max_wait,
      help=help_text,
      type=arg_parsers.Duration(),
  )


def AddTLSInspectionPolicy(
    release_track,
    parser,
    help_text="Path to TLS Inspection Policy configuration to use for intercepting TLS-encrypted traffic in this network.",
):
  """Adds TLS Inspection Policy resource."""
  api_version = activation_api.GetApiVersion(release_track)
  collection_info = resources.REGISTRY.Clone().GetCollectionInfo(
      ASSOCIATION_RESOURCE_COLLECTION, api_version
  )
  resource_spec = concepts.ResourceSpec(
      TLS_INSPECTION_POLICY_RESOURCE_COLLECTION,
      "TLS Inspection Policy",
      api_version=api_version,
      projectsId=concepts.ResourceParameterAttributeConfig(
          "tls-inspection-policy-project",
          "Project of the {resource}.",
          parameter_name="projectsId",
          fallthroughs=[
              deps.ArgFallthrough("--project"),
              deps.FullySpecifiedAnchorFallthrough(
                  [deps.ArgFallthrough(ASSOCIATION_RESOURCE_NAME)],
                  collection_info,
                  "projectsId",
              ),
          ],
      ),
      locationsId=concepts.ResourceParameterAttributeConfig(
          "tls-inspection-policy-region",
          """
          Region of the {resource}.
          NOTE: TLS Inspection Policy needs to be
          in the same region as Firewall Plus endpoint resource.
          """,
          parameter_name="locationsId",
      ),
      tlsInspectionPoliciesId=concepts.ResourceParameterAttributeConfig(
          "tls_inspection_policy",
          "Name of the {resource}",
          parameter_name="tlsInspectionPoliciesId",
      ),
  )
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=TLS_INSPECTION_POLICY_RESOURCE_NAME,
      concept_spec=resource_spec,
      required=False,
      group_help=help_text,
  )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddNoTLSInspectionPolicyArg(
    parser, help_text="Remove TLS inspection policy from this association."
):
  parser.add_argument(
      "--no-tls-inspection-policy", action="store_true", help=help_text
  )


def AddDisabledArg(
    parser,
    help_text=textwrap.dedent("""\
      Disable a firewall endpoint association. To enable a disabled association, use:

       $ {parent_command} update MY-ASSOCIATION --no-disabled

      """),
):
  parser.add_argument(
      "--disabled",
      action="store_true",
      default=None,
      help=help_text,
  )


def MakeGetUriFunc(release_track):
  return (
      lambda x: activation_api.GetEffectiveApiEndpoint(release_track) + x.name
  )


def AddZoneArg(
    parser, required=True, help_text="Zone of a firewall endpoint association"
):
  parser.add_argument("--zone", required=required, default="-", help=help_text)

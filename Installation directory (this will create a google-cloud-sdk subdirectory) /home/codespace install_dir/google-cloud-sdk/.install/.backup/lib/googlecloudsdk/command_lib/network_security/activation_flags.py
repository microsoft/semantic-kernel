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
"""Flags for Firewall Plus Endpoint commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.firewall_endpoints import activation_api
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties


ENDPOINT_RESOURCE_NAME = "FIREWALL_ENDPOINT"
BILLING_HELP_TEST = (
    "The Google Cloud project ID to use for API enablement check, quota, and"
    " endpoint uptime billing."
)


def AddEndpointResource(release_track, parser):
  """Adds Firewall Plus endpoint resource."""
  api_version = activation_api.GetApiVersion(release_track)
  resource_spec = concepts.ResourceSpec(
      "networksecurity.organizations.locations.firewallEndpoints",
      "firewall endpoint",
      api_version=api_version,
      organizationsId=concepts.ResourceParameterAttributeConfig(
          "organization",
          "Organization ID of the {resource}.",
          parameter_name="organizationsId",
      ),
      locationsId=concepts.ResourceParameterAttributeConfig(
          "zone",
          "Zone of the {resource}.",
          parameter_name="locationsId",
      ),
      firewallEndpointsId=concepts.ResourceParameterAttributeConfig(
          "endpoint-name",
          "Name of the {resource}",
          parameter_name="firewallEndpointsId",
      ),
  )
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=ENDPOINT_RESOURCE_NAME,
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


def MakeGetUriFunc(release_track):
  return (
      lambda x: activation_api.GetEffectiveApiEndpoint(release_track) + x.name
  )


def AddOrganizationArg(parser, help_text="Organization of the endpoint"):
  parser.add_argument("--organization", required=True, help=help_text)


def AddDescriptionArg(parser, help_text="Description of the endpoint"):
  parser.add_argument("--description", required=False, help=help_text)


def AddTargetFirewallAttachmentArg(
    parser,
    help_text="Target firewall attachment where third party endpoint forwards traffic."
):
  parser.add_argument(
      "--target-firewall-attachment", required=False, help=help_text
  )


def AddZoneArg(parser, required=True, help_text="Zone of the endpoint"):
  parser.add_argument("--zone", required=required, help=help_text)


def AddBillingProjectArg(
    parser,
    required=True,
    help_text=BILLING_HELP_TEST,
):
  """Add billing project argument to parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
    required: bool, whether to make this argument required.
    help_text: str, help text to overwrite the generic --billing-project help
      text.
  """
  parser.add_argument(
      "--billing-project",
      required=required,
      help=help_text,
      action=actions.StoreProperty(properties.VALUES.billing.quota_project),
  )


# We use the explicit --update-billing-project flag as opposed to the existent
# --billing-project flag because otherwise there will be an ambiguity when a
# user wants to update other things, but not the billing project.
# For example, to update the labels, a billing project is still needed for API
# quota, making the ambiguous call:
# gcloud network-security firewall-endpoints update \
#     --billing-project=proj --update-labels=k1=v1
# This is a common use for other gcloud update flags as well.
def AddUpdateBillingProjectArg(
    parser,
    required=False,
    help_text=BILLING_HELP_TEST,
):
  """Add update billing project argument to parser.

  Args:
    parser: ArgumentInterceptor, An argparse parser.
    required: bool, whether to make this argument required.
    help_text: str, help text to display on the --update-billing-project help
      text.
  """
  parser.add_argument(
      "--update-billing-project",
      required=required,
      help=help_text,
      metavar="BILLING_PROJECT",
      action=actions.StoreProperty(properties.VALUES.billing.quota_project),
  )

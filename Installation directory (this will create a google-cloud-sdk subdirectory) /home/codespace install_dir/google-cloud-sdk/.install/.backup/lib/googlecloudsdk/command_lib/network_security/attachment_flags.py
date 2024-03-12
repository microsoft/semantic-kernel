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
"""Flags for Firewall Attachment commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.firewall_attachments import attachment_api
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs

ATTACHMENT_RESOURCE_NAME = "FIREWALL_ATTACHMENT"
ATTACHMENT_RESOURCE_COLLECTION = (
    "networksecurity.projects.locations.firewallAttachments"
)


def AddAttachmentResource(
    release_track,
    parser,
    help_text="Path to Firewall Attachment resource",
):
  """Adds Firewall attachment resource."""
  api_version = attachment_api.GetApiVersion(release_track)
  resource_spec = concepts.ResourceSpec(
      ATTACHMENT_RESOURCE_COLLECTION,
      "firewall attachment",
      api_version=api_version,
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG,
      locationsId=concepts.ResourceParameterAttributeConfig(
          "zone",
          "Zone of the {resource}.",
          parameter_name="locationsId",
      ),
      firewallAttachmentsId=concepts.ResourceParameterAttributeConfig(
          "attachment-name",
          "Name of the {resource}",
          parameter_name="firewallAttachmentsId",
      ),
  )
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name=ATTACHMENT_RESOURCE_NAME,
      concept_spec=resource_spec,
      required=True,
      group_help=help_text,
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
      lambda x: attachment_api.GetEffectiveApiEndpoint(release_track) + x.name
  )


def AddProjectArg(parser, help_text="Project of the attachment"):
  parser.add_argument("--project", required=True, help=help_text)


def AddProducerForwardingRuleArg(
    parser,
    help_text="Path of a forwarding rule that points to a backend with GENEVE-capable VMs."
):
  parser.add_argument(
      "--producer-forwarding-rule", required=True, help=help_text
  )


def AddZoneArg(parser, required=True, help_text="Zone of the attachment"):
  parser.add_argument("--zone", required=required, help=help_text)

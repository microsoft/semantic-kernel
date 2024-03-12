# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Client for interaction with ZONE API CRUD DATAPLEX."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import util as dataplex_api
from googlecloudsdk.command_lib.iam import iam_util


def SetIamPolicy(zone_ref, policy):
  """Set Iam Policy request."""
  set_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsLakesZonesSetIamPolicyRequest(
      resource=zone_ref.RelativeName(),
      googleIamV1SetIamPolicyRequest=dataplex_api.GetMessageModule()
      .GoogleIamV1SetIamPolicyRequest(policy=policy))
  return dataplex_api.GetClientInstance(
  ).projects_locations_lakes_zones.SetIamPolicy(set_iam_policy_req)


def GetIamPolicy(zone_ref):
  """Get Iam Policy request."""
  get_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsLakesZonesGetIamPolicyRequest(
      resource=zone_ref.RelativeName())
  return dataplex_api.GetClientInstance(
  ).projects_locations_lakes_zones.GetIamPolicy(get_iam_policy_req)


def AddIamPolicyBinding(zone_ref, member, role):
  """Add iam policy binding request."""
  policy = GetIamPolicy(zone_ref)
  iam_util.AddBindingToIamPolicy(
      dataplex_api.GetMessageModule().GoogleIamV1Binding, policy, member, role)
  return SetIamPolicy(zone_ref, policy)


def RemoveIamPolicyBinding(lake_ref, member, role):
  """Remove iam policy binding request."""
  policy = GetIamPolicy(lake_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return SetIamPolicy(lake_ref, policy)


def SetIamPolicyFromFile(zone_ref, policy_file):
  """Set iam policy binding request from file."""
  policy = iam_util.ParsePolicyFile(
      policy_file,
      dataplex_api.GetMessageModule().GoogleIamV1Policy)
  return SetIamPolicy(zone_ref, policy)


def GenerateZoneForCreateRequest(args):
  """Create Zone for Message Create Requests."""
  module = dataplex_api.GetMessageModule()
  return module.GoogleCloudDataplexV1Zone(
      description=args.description,
      displayName=args.display_name,
      labels=dataplex_api.CreateLabels(module.GoogleCloudDataplexV1Zone, args),
      type=module.GoogleCloudDataplexV1Zone.TypeValueValuesEnum(args.type),
      discoverySpec=GenerateDiscoverySpec(args),
      resourceSpec=module.GoogleCloudDataplexV1ZoneResourceSpec(
          locationType=module.GoogleCloudDataplexV1ZoneResourceSpec
          .LocationTypeValueValuesEnum(args.resource_location_type)))


def GenerateZoneForUpdateRequest(args):
  """Create Zone for Message Update Requests."""
  module = dataplex_api.GetMessageModule()
  return module.GoogleCloudDataplexV1Zone(
      description=args.description,
      displayName=args.display_name,
      labels=dataplex_api.CreateLabels(module.GoogleCloudDataplexV1Zone, args),
      discoverySpec=GenerateDiscoverySpec(args))


def GenerateDiscoverySpec(args):
  return dataplex_api.GetMessageModule().GoogleCloudDataplexV1ZoneDiscoverySpec(
      enabled=args.discovery_enabled,
      includePatterns=args.discovery_include_patterns,
      excludePatterns=args.discovery_exclude_patterns,
      schedule=args.discovery_schedule,
      csvOptions=GenerateCsvOptions(args),
      jsonOptions=GenerateJsonOptions(args))


def GenerateCsvOptions(args):
  return dataplex_api.GetMessageModule(
  ).GoogleCloudDataplexV1ZoneDiscoverySpecCsvOptions(
      delimiter=args.csv_delimiter,
      disableTypeInference=args.csv_disable_type_inference,
      encoding=args.csv_encoding,
      headerRows=args.csv_header_rows)


def GenerateJsonOptions(args):
  return dataplex_api.GetMessageModule(
  ).GoogleCloudDataplexV1ZoneDiscoverySpecJsonOptions(
      encoding=args.json_encoding,
      disableTypeInference=args.json_disable_type_inference)


def GenerateUpdateMask(args):
  """Create Update Mask for Zones."""
  update_mask = []
  if args.IsSpecified('description'):
    update_mask.append('description')
  if args.IsSpecified('display_name'):
    update_mask.append('displayName')
  if args.IsSpecified('labels'):
    update_mask.append('labels')
  if args.IsSpecified('discovery_enabled'):
    update_mask.append('discoverySpec.enabled')
  if args.IsSpecified('discovery_include_patterns'):
    update_mask.append('discoverySpec.includePatterns')
  if args.IsSpecified('discovery_exclude_patterns'):
    update_mask.append('discoverySpec.excludePatterns')
  if args.IsSpecified('discovery_schedule'):
    update_mask.append('discoverySpec.schedule')
  if args.IsSpecified('csv_header_rows'):
    update_mask.append('discoverySpec.csvOptions.headerRows')
  if args.IsSpecified('csv_delimiter'):
    update_mask.append('discoverySpec.csvOptions.delimiter')
  if args.IsSpecified('csv_encoding'):
    update_mask.append('discoverySpec.csvOptions.encoding')
  if args.IsSpecified('csv_disable_type_inference'):
    update_mask.append('discoverySpec.csvOptions.disableTypeInference')
  if args.IsSpecified('json_encoding'):
    update_mask.append('discoverySpec.jsonOptions.encoding')
  if args.IsSpecified('json_disable_type_inference'):
    update_mask.append('discoverySpec.jsonOptions.disableTypeInference')
  return update_mask


def WaitForOperation(operation):
  """Waits for the given google.longrunning.Operation to complete."""
  return dataplex_api.WaitForOperation(
      operation,
      dataplex_api.GetClientInstance().projects_locations_lakes_zones)

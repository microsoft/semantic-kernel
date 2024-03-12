# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Utilities for `gcloud network-management`."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.core import exceptions


class NetworkManagementError(exceptions.Error):
  """Top-level exception for all Network Management errors."""


class InvalidInputError(NetworkManagementError):
  """Exception for invalid input."""


def GetClearSingleEndpointAttrErrorMsg(endpoints, endpoint_type):
  """Creates a message to specify at least one endpoint, separated by commas and or."""
  error_msg = ["Invalid Connectivity Test. "]
  if len(endpoints) > 1:
    error_msg.append("At least one of ")

  for index, endpoint in enumerate(endpoints):
    error_msg.append(
        "--{endpoint_type}-{endpoint}".format(
            endpoint_type=endpoint_type, endpoint=endpoint
        )
    )
    if index == 0 and len(endpoints) == 2:
      error_msg.append(" or ")
    elif index == len(endpoints) - 2:
      error_msg.append(", or ")
    elif index < len(endpoints) - 2:
      error_msg.append(", ")

  error_msg.append(" must be specified.")
  return "".join(error_msg)


def AppendLocationsGlobalToParent(unused_ref, unused_args, request):
  """Add locations/global to parent path, since it isn't automatically populated by apitools."""
  request.parent += "/locations/global"
  return request


def UpdateOperationRequestNameVariable(unused_ref, unused_args, request):
  request.name += "/locations/global"
  return request


def AddFieldToUpdateMask(field, patch_request):
  """Adds name of field to update mask."""
  update_mask = patch_request.updateMask
  if not update_mask:
    patch_request.updateMask = field
  elif field not in update_mask:
    patch_request.updateMask = update_mask + "," + field
  return patch_request


def ClearEndpointValue(endpoint, endpoint_name):
  proto_endpoint_fields = {
      "cloudFunction",
      "appEngineVersion",
      "cloudRunRevision",
  }
  if endpoint_name in proto_endpoint_fields:
    # Endpoint is a proto message: Set to None.
    setattr(endpoint, endpoint_name, None)
  else:
    # Endpoint is a string (only a URI): Set to "".
    setattr(endpoint, endpoint_name, "")


def ClearSingleEndpointAttr(patch_request, endpoint_type, endpoint_name):
  """Checks if given endpoint can be removed from Connectivity Test and removes it."""
  test = patch_request.connectivityTest
  endpoint = getattr(test, endpoint_type)
  endpoint_fields = {
      "instance",
      "ipAddress",
      "gkeMasterCluster",
      "cloudSqlInstance",
      "cloudFunction",
      "appEngineVersion",
      "cloudRunRevision",
      "forwardingRule",
  }
  non_empty_endpoint_fields = 0
  for field in endpoint_fields:
    if getattr(endpoint, field, None):
      non_empty_endpoint_fields += 1
  if non_empty_endpoint_fields > 1 or not getattr(
      endpoint, endpoint_name, None
  ):
    ClearEndpointValue(endpoint, endpoint_name)
    setattr(test, endpoint_type, endpoint)
    patch_request.connectivityTest = test
    return AddFieldToUpdateMask(
        endpoint_type + "." + endpoint_name, patch_request
    )
  else:
    endpoints = [
        "instance",
        "ip-address",
        "gke-master-cluster",
        "cloud-sql-instance",
    ]
    if endpoint_type == "source":
      endpoints.extend([
          "cloud-function",
          "app-engine-version",
          "cloud-run-revision",
      ])
    if endpoint_type == "destination":
      endpoints.extend([
          "forwarding-rule",
      ])
    raise InvalidInputError(
        GetClearSingleEndpointAttrErrorMsg(endpoints, endpoint_type)
    )


def ClearEndpointAttrs(unused_ref, args, patch_request):
  """Handles clear_source_* and clear_destination_* flags."""
  flags_and_endpoints = [
      ("clear_source_instance", "source", "instance"),
      ("clear_source_ip_address", "source", "ipAddress"),
      ("clear_source_gke_master_cluster", "source", "gkeMasterCluster"),
      ("clear_source_cloud_sql_instance", "source", "cloudSqlInstance"),
      ("clear_source_cloud_function", "source", "cloudFunction"),
      ("clear_source_app_engine_version", "source", "appEngineVersion"),
      ("clear_source_cloud_run_revision", "source", "cloudRunRevision"),
      ("clear_destination_instance", "destination", "instance"),
      ("clear_destination_ip_address", "destination", "ipAddress"),
      (
          "clear_destination_gke_master_cluster",
          "destination",
          "gkeMasterCluster",
      ),
      (
          "clear_destination_cloud_sql_instance",
          "destination",
          "cloudSqlInstance",
      ),
      (
          "clear_destination_forwarding_rule",
          "destination",
          "forwardingRule",
      ),
  ]

  for flag, endpoint_type, endpoint_name in flags_and_endpoints:
    if args.IsSpecified(flag):
      patch_request = ClearSingleEndpointAttr(
          patch_request,
          endpoint_type,
          endpoint_name,
      )

  return patch_request


def ClearSingleEndpointAttrBeta(patch_request, endpoint_type, endpoint_name):
  """Checks if given endpoint can be removed from Connectivity Test and removes it."""
  test = patch_request.connectivityTest
  endpoint = getattr(test, endpoint_type)
  endpoint_fields = {
      "instance",
      "ipAddress",
      "gkeMasterCluster",
      "cloudSqlInstance",
      "cloudFunction",
      "appEngineVersion",
      "cloudRunRevision",
      "forwardingRule",
  }
  non_empty_endpoint_fields = 0
  for field in endpoint_fields:
    if getattr(endpoint, field, None):
      non_empty_endpoint_fields += 1
  if non_empty_endpoint_fields > 1 or not getattr(
      endpoint, endpoint_name, None
  ):
    ClearEndpointValue(endpoint, endpoint_name)
    setattr(test, endpoint_type, endpoint)
    patch_request.connectivityTest = test
    return AddFieldToUpdateMask(
        endpoint_type + "." + endpoint_name, patch_request
    )
  else:
    endpoints = [
        "instance",
        "ip-address",
        "gke-master-cluster",
        "cloud-sql-instance",
    ]
    if endpoint_type == "source":
      endpoints.extend([
          "cloud-function",
          "app-engine-version",
          "cloud-run-revision",
      ])
    if endpoint_type == "destination":
      endpoints.extend([
          "forwarding-rule",
      ])
    raise InvalidInputError(
        GetClearSingleEndpointAttrErrorMsg(endpoints, endpoint_type)
    )


def ClearEndpointAttrsBeta(unused_ref, args, patch_request):
  """Handles clear_source_* and clear_destination_* flags."""
  flags_and_endpoints = [
      ("clear_source_instance", "source", "instance"),
      ("clear_source_ip_address", "source", "ipAddress"),
      ("clear_source_gke_master_cluster", "source", "gkeMasterCluster"),
      ("clear_source_cloud_sql_instance", "source", "cloudSqlInstance"),
      ("clear_source_cloud_function", "source", "cloudFunction"),
      ("clear_source_app_engine_version", "source", "appEngineVersion"),
      ("clear_source_cloud_run_revision", "source", "cloudRunRevision"),
      ("clear_destination_instance", "destination", "instance"),
      ("clear_destination_ip_address", "destination", "ipAddress"),
      (
          "clear_destination_gke_master_cluster",
          "destination",
          "gkeMasterCluster",
      ),
      (
          "clear_destination_cloud_sql_instance",
          "destination",
          "cloudSqlInstance",
      ),
      (
          "clear_destination_forwarding_rule",
          "destination",
          "forwardingRule",
      ),
  ]

  for flag, endpoint_type, endpoint_name in flags_and_endpoints:
    if args.IsSpecified(flag):
      patch_request = ClearSingleEndpointAttrBeta(
          patch_request,
          endpoint_type,
          endpoint_name,
      )

  return patch_request


def ValidateInstanceNames(unused_ref, args, request):
  """Checks if all provided instances are in valid format."""
  flags = [
      "source_instance",
      "destination_instance",
  ]
  instance_pattern = re.compile(
      r"projects/(?:[a-z][a-z0-9-\.:]*[a-z0-9])/zones/[-\w]+/instances/[-\w]+"
  )
  for flag in flags:
    if args.IsSpecified(flag):
      instance = getattr(args, flag)
      if not instance_pattern.match(instance):
        raise InvalidInputError(
            "Invalid value for flag {}: {}\n"
            "Expected instance in the following format:\n"
            "  projects/my-project/zones/zone/instances/my-instance".format(
                flag, instance
            )
        )

  return request


def ValidateNetworkURIs(unused_ref, args, request):
  """Checks if all provided networks are in valid format."""
  flags = [
      "source_network",
      "destination_network",
  ]
  network_pattern = re.compile(
      r"projects/(?:[a-z][a-z0-9-\.:]*[a-z0-9])/global/networks/[-\w]+"
  )
  for flag in flags:
    if args.IsSpecified(flag):
      network = getattr(args, flag)
      if not network_pattern.match(network):
        raise InvalidInputError(
            "Invalid value for flag {}: {}\n"
            "Expected network in the following format:\n"
            "  projects/my-project/global/networks/my-network".format(
                flag, network
            )
        )

  return request


def ValidateGKEMasterClustersURIs(unused_ref, args, request):
  """Checks if all provided GKE Master Clusters URIs are in correct format."""
  flags = [
      "source_gke_master_cluster",
      "destination_gke_master_cluster",
  ]
  instance_pattern = re.compile(
      r"projects/(?:[a-z][a-z0-9-\.:]*[a-z0-9])/(zones|locations)/[-\w]+/clusters/[-\w]+"
  )
  for flag in flags:
    if args.IsSpecified(flag):
      cluster = getattr(args, flag)
      if not instance_pattern.match(cluster):
        raise InvalidInputError(
            "Invalid value for flag {}: {}\nExpected Google Kubernetes Engine"
            " master cluster in the following format:\n "
            " projects/my-project/location/location/clusters/my-cluster".format(
                flag, cluster
            )
        )
  return request


def ValidateCloudSQLInstancesURIs(unused_ref, args, request):
  """Checks if all provided Cloud SQL Instances URIs are in correct format."""
  flags = [
      "source_cloud_sql_instance",
      "destination_cloud_sql_instance",
  ]
  instance_pattern = re.compile(
      r"projects/(?:[a-z][a-z0-9-\.:]*[a-z0-9])/instances/[-\w]+"
  )
  for flag in flags:
    if args.IsSpecified(flag):
      instance = getattr(args, flag)
      if not instance_pattern.match(instance):
        raise InvalidInputError(
            "Invalid value for flag {}: {}\n"
            "Expected Cloud SQL instance in the following format:\n"
            "  projects/my-project/instances/my-instance".format(flag, instance)
        )
  return request


def ValidateCloudFunctionsURIs(unused_ref, args, request):
  """Checks if all provided Cloud Functions URIs are in correct format."""
  flags = [
      "source_cloud_function",
  ]
  function_pattern = re.compile(
      r"projects/(?:[a-z][a-z0-9-\.:]*[a-z0-9])/locations/[-\w]+/functions/[-\w]+"
  )
  for flag in flags:
    if not args.IsSpecified(flag):
      continue

    function = getattr(args, flag)
    if not function_pattern.match(function):
      raise InvalidInputError(
          "Invalid value for flag {}: {}\n"
          "Expected Cloud Function in the following format:\n"
          "  projects/my-project/locations/location/functions/my-function"
          .format(flag, function)
      )
  return request


def ValidateAppEngineVersionsURIs(unused_ref, args, request):
  """Checks if all provided App Engine version URIs are in correct format."""
  flags = [
      "source_app_engine_version",
  ]
  version_pattern = re.compile(
      r"apps/(?:[a-z][a-z0-9-\.:]*[a-z0-9])/services/[-\w]+/versions/[-\w]+"
  )
  for flag in flags:
    if not args.IsSpecified(flag):
      continue

    version = getattr(args, flag)
    if not version_pattern.match(version):
      raise InvalidInputError(
          "Invalid value for flag {}: {}\n"
          "Expected App Engine version in the following format:\n"
          "  apps/my-project/services/my-service/versions/my-version".format(
              flag, version
          )
      )
  return request


def ValidateCloudRunRevisionsURIs(unused_ref, args, request):
  """Checks if all provided Cloud Run revisions URIs are in correct format."""
  flags = [
      "source_cloud_run_revision",
  ]
  revision_pattern = re.compile(
      r"projects/(?:[a-z][a-z0-9-\.:]*[a-z0-9])/locations/[-\w]+/revisions/[-\w]+"
  )
  for flag in flags:
    if not args.IsSpecified(flag):
      continue

    revision = getattr(args, flag)
    if not revision_pattern.match(revision):
      raise InvalidInputError(
          "Invalid value for flag {}: {}\n"
          "Expected Cloud Run revision in the following format:\n"
          "  projects/my-project/locations/location/revisions/my-revision"
          .format(flag, revision)
      )
  return request


def ValidateForwardingRulesURIs(unused_ref, args, request):
  """Checks if all provided forwarding rules URIs are in correct format."""
  flags = [
      "destination_forwarding_rule",
  ]
  forwarding_rule_pattern = re.compile(
      r"projects/(?:[a-z][a-z0-9-\.:]*[a-z0-9])/(global|regions/[-\w]+)/forwardingRules/[-\w]+"
  )
  for flag in flags:
    if not args.IsSpecified(flag):
      continue

    forwarding_rule = getattr(args, flag)
    if not forwarding_rule_pattern.match(forwarding_rule):
      raise InvalidInputError(
          "Invalid value for flag {flag}: {forwarding_rule}\n"
          + "Expected forwarding rule in one of the following formats:\n"
          + "  projects/my-project/global/forwardingRules/my-forwarding-rule\n"
          + "  projects/my-project/regions/us-central1/forwardingRules/my-forwarding-rule"
      )
  return request

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
"""Declarative Response Hooks for Cloud SCC's Asset responses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from apitools.base.py.extra_types import _JsonValueToPythonValue
from googlecloudsdk.api_lib.scc import securitycenter_client as sc_client
from googlecloudsdk.command_lib.scc.errors import InvalidSCCInputError


def ExtractSecurityMarksFromResponse(response, args):
  """Returns security marks from asset response."""
  del args
  list_asset_response = list(response)
  if len(list_asset_response) > 1:
    raise InvalidSCCInputError(
        "ListAssetResponse must only return one asset since it is filtered "
        "by Asset Name.")
  for asset_result in list_asset_response:
    return asset_result.asset.securityMarks


def ExtractMatchingAssetFromDescribeResponse(response, args):
  """Returns asset that matches the user provided asset or resource-name."""
  del args
  list_asset_response = list(response)
  if not list_asset_response:
    raise InvalidSCCInputError("Asset or resource does not exist.")
  if len(list_asset_response) > 1:
    raise InvalidSCCInputError(
        "ListAssetResponse must only return one asset since it is filtered "
        "by Asset Name or Resource Name.")
  for asset_result in list_asset_response:
    result_dictionary = {
        "asset": int(asset_result.asset.name.split("/")[3]),
        "resourceName": asset_result.asset.securityCenterProperties.resourceName
    }
    return result_dictionary


def ExtractMatchingAssetFromGetParentResponse(response, args):
  """Returns Parent for the user provided asset or resource-name."""
  del args
  asset_result = _ValidateAndGetAssetResult(response)
  asset_parent = _GetAssetResourceParent(asset_result)
  organization = _ExtractOrganization(asset_result)
  resource_name_filter = _FilterOnResourceName(asset_parent)
  asset = _GetAsset(organization, resource_name_filter)
  parent = _GetParent(asset)

  result_dictionary = {"parent": parent}
  return result_dictionary


def ExtractMatchingAssetFromGetProjectResponse(response, args):
  """Returns ProjectId for the user provided asset or resource-name."""
  del args
  asset_result = _ValidateAndGetAssetResult(response)
  asset_project = _GetAssetProject(asset_result)
  organization = _ExtractOrganization(asset_result)
  resource_name_filter = _FilterOnResourceName(asset_project)
  asset = _GetAsset(organization, resource_name_filter)
  project_id = _GetProjectId(asset)

  result_dictionary = {"projectId": project_id}
  return result_dictionary


def _ValidateAndGetAssetResult(response):
  list_asset_response = list(response)
  if not list_asset_response:
    raise InvalidSCCInputError(
        "Asset or resource does not exist for the provided Organization. Please"
        " verify that both the OrganizationId and AssetId/ResourceName are "
        "correct.")
  if len(list_asset_response) > 1:
    raise InvalidSCCInputError(
        "An asset can not have multiple projects. Something went wrong.")
  return list_asset_response[0]


def _GetAssetResourceParent(asset_result):
  asset_parent = asset_result.asset.securityCenterProperties.resourceParent
  if asset_parent is None:
    raise InvalidSCCInputError("Asset does not have a parent.")
  return asset_parent


def _GetAssetProject(asset_result):
  asset_project = asset_result.asset.securityCenterProperties.resourceProject
  if asset_project is None:
    raise InvalidSCCInputError(
        "Organization assets do not belong to a Project.")
  return asset_project


def _FilterOnResourceName(asset_property):
  return "securityCenterProperties.resourceName=\"" + asset_property + "\""


def _GetProjectId(asset):
  project_id = [
      x.value
      for x in asset.resourceProperties.additionalProperties
      if x.key == "projectId"
  ]
  if not project_id:
    raise InvalidSCCInputError("No projectId exists for this asset.")
  return _JsonValueToPythonValue(project_id[0])


def _GetParent(asset):
  parent = [
      x.value
      for x in asset.resourceProperties.additionalProperties
      if x.key == "name"
  ]
  if not parent:
    raise InvalidSCCInputError("No parent exists for this asset.")
  return _JsonValueToPythonValue(parent[0])


def _ExtractOrganization(asset_result):
  return (asset_result.asset.name.split("/")[0] + "/" +
          asset_result.asset.name.split("/")[1])


def _GetAsset(parent, request_filter=None):
  asset_service_client = sc_client.AssetsClient()
  list_asset_response_for_project = asset_service_client.List(
      parent=parent, request_filter=request_filter)
  list_asset_results = list_asset_response_for_project.listAssetsResults
  if len(list_asset_results) != 1:
    raise InvalidSCCInputError(
        "Something went wrong while retrieving the ProjectId for this Asset.")
  return list_asset_results[0].asset

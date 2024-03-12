# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Create hooks for Cloud Media Asset's asset type."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.media.asset import utils
from googlecloudsdk.core import resources


def AddParentInfoToAssetRequests(ref, args, req):
  """Python hook for yaml commands to wildcard the parent parameter in asset requests."""
  del ref  # Unused
  project = utils.GetProject()
  location = utils.GetLocation(args)
  req.parent = utils.GetAssetTypeParentTemplate(project, location,
                                                args.asset_type)
  return req


def ParseAssetConfigFile(ref, args, req):
  """Prepare the asset for create and update requests."""
  del ref  # Unused
  messages = apis.GetMessagesModule('mediaasset', 'v1alpha')
  if args.IsKnownAndSpecified('asset_config_file'):
    asset_data = json.loads(args.asset_config_file)
    asset = encoding.DictToMessage(asset_data, messages.Asset)
    utils.ValidateMediaAssetMessage(asset)
    req.asset = asset
  if args.IsKnownAndSpecified('labels'):
    req.asset.labels = encoding.DictToMessage(args.labels,
                                              messages.Asset.LabelsValue)
  return req


def GetExistingResource(api_version, request_message):
  """Get the modified resource.

  Args:
    api_version: the request's release track.
    request_message: request message type in the python client.

  Returns:
    The modified resource.
  """
  return utils.GetClient(api_version).projects_locations_assetTypes_assets.Get(
      request_message)


def ProcessOutput(response, args):
  """Wait for operations to finish and return the resource."""
  api_version = utils.GetApiVersionFromArgs(args)
  utils.WaitForOperation(response, api_version)

  project = utils.GetProject()
  location = utils.GetLocation(args)
  resource_ref = resources.REGISTRY.Create(
      'mediaasset.projects.locations.assetTypes.assets',
      projectsId=project,
      locationsId=location,
      assetTypesId=args.asset_type,
      assetsId=args.asset)

  if 'delete' in args.command_path:
    # No need to send another get request to check for the deleted asset.
    return response
  request_message = utils.GetApiMessage(
      api_version).MediaassetProjectsLocationsAssetTypesAssetsGetRequest(
          name=resource_ref.RelativeName())

  return GetExistingResource(api_version, request_message)

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
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources


def ParseCreateConfigFile(ref, args, req):
  """Reads the json file of with the asset type configs and parse the content to the request message."""
  del ref
  messages = apis.GetMessagesModule('mediaasset', 'v1alpha')
  message_class = messages.AssetType
  if args.create_asset_type_config_file:
    asset_type_configs = json.loads(args.create_asset_type_config_file)
    at = encoding.DictToMessage(asset_type_configs, message_class)
    utils.ValidateMediaAssetMessage(at)
    req.assetType = at
  if args.IsKnownAndSpecified('labels'):
    req.assetType.labels = encoding.DictToMessage(
        args.labels, messages.AssetType.LabelsValue)
  return req


def ParseUpdateConfigFile(ref, args, req):
  """Reads the json file with asset type configs and update mask, then parse the cotent to the request message."""
  del ref
  update_file_config = json.loads(args.update_asset_type_config_file)
  messages = apis.GetMessagesModule('mediaasset', 'v1alpha')
  # validate input file.
  if 'assetType' not in update_file_config:
    raise exceptions.Error('assetType needs to be included in the config file.')
  if 'updateMask' not in update_file_config:
    raise exceptions.Error(
        'updateMask needs to be included in the config file.')
  update_mask = update_file_config['updateMask']
  asset_type = update_file_config['assetType']
  if not isinstance(update_mask, list):
    raise exceptions.Error('updateMask needs to be a list.')
  if len(update_mask) != len(asset_type):
    raise exceptions.Error('updated assetType does not match with updateMask.')
  for update in update_mask:
    if update not in asset_type:
      raise exceptions.Error(
          'updated assetType does not match with updateMask.')
  # set request parameters.
  at = encoding.DictToMessage(asset_type, messages.AssetType)
  utils.ValidateMediaAssetMessage(at)
  req.assetType = at
  req.updateMask = ','.join(update_mask)
  return req


def GetExistingResource(api_version, request_message):
  """Get the modified resource.

  Args:
    api_version: the request's release track.
    request_message: request message type in the python client.

  Returns:
    The modified resource.
  """
  return utils.GetClient(api_version).projects_locations_assetTypes.Get(
      request_message)


def ProcessOutput(response, args):
  """Wait for operations to finish and return the resource."""
  api_version = utils.GetApiVersionFromArgs(args)
  utils.WaitForOperation(response, api_version)

  project = utils.GetProject()
  location = utils.GetLocation(args)
  resource_ref = resources.REGISTRY.Create(
      'mediaasset.projects.locations.assetTypes',
      projectsId=project,
      locationsId=location,
      assetTypesId=args.asset_type)

  if 'delete' in args.command_path:
    # No need to send another get request to check for the deleted complex type.
    return response
  request_message = utils.GetApiMessage(
      api_version).MediaassetProjectsLocationsAssetTypesGetRequest(
          name=resource_ref.RelativeName())

  return GetExistingResource(api_version, request_message)

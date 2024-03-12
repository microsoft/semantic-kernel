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
"""Hooks function for Cloud Media Asset's complex type."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.command_lib.media.asset import utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import resources


def ParseComplexTypeConfigFile(ref, args, req):
  """Reads the json with complex type configuration and set the content in the request."""
  del ref
  complex_type_dict = []
  if args.complex_type_config_file:
    complex_type_dict = json.loads(args.complex_type_config_file)
    messages = utils.GetApiMessage(utils.GetApiVersionFromArgs(args))
    ct = encoding.DictToMessage(complex_type_dict, messages.ComplexType)
    utils.ValidateMediaAssetMessage(ct)
    req.complexType = ct
  if 'update' in args.command_path:
    ValidateUpdateMask(args, complex_type_dict)
  return req


def ValidateUpdateMask(args, complex_type_dict):
  """Validate the update mask in update complex type requests."""
  update_masks = list(args.update_mask.split(','))
  for mask in update_masks:
    # walk the path in the dictionary to ensure it's correct
    mask_path = mask.split('.')
    mask_path_index = 0
    complex_type_walker = complex_type_dict
    while mask_path_index < len(mask_path):
      if mask_path[mask_path_index] not in complex_type_walker:
        raise exceptions.Error(
            'unrecognized field in update_mask: {0}.'.format(mask))
      complex_type_walker = complex_type_walker[mask_path[mask_path_index]]
      mask_path_index += 1


def GetExistingResource(api_version, request_message):
  """Get the modified resource.

  Args:
    api_version: The request release track.
    request_message: request message type in the python client.

  Returns:
    The modified resource.
  """
  return utils.GetClient(api_version).projects_locations_complexTypes.Get(
      request_message)


def ProcessOutput(response, args):
  """Wait for operations to finish and return the resource."""
  api_version = utils.GetApiVersionFromArgs(args)
  utils.WaitForOperation(response, api_version)

  project = utils.GetProject()
  location = utils.GetLocation(args)
  resource_ref = resources.REGISTRY.Create(
      'mediaasset.projects.locations.complexTypes',
      projectsId=project,
      locationsId=location,
      complexTypesId=args.complex_type)

  if 'delete' in args.command_path:
    # No need to send another get request to check for the deleted complex type.
    return response
  request_message = utils.GetApiMessage(
      api_version).MediaassetProjectsLocationsComplexTypesGetRequest(
          name=resource_ref.RelativeName())

  return GetExistingResource(api_version, request_message)

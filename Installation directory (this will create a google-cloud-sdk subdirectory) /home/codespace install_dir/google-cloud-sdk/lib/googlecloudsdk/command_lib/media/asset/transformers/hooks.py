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
"""Hooks function for Cloud Media Asset's transformers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.media.asset import utils
from googlecloudsdk.core import resources


def ParseTransformerConfigFile(ref, args, req):
  """Reads the json file of with the transformer configs and parse the content to the request message."""
  del ref
  messages = apis.GetMessagesModule('mediaasset', 'v1alpha')
  message_class = messages.Transformer
  if args.create_transformer_configs_file:
    transformer_configs = json.loads(args.create_transformer_configs_file)
    transformer = encoding.DictToMessage(transformer_configs, message_class)
    utils.ValidateMediaAssetMessage(transformer)
    req.transformer = transformer
  if args.IsKnownAndSpecified('labels'):
    req.transformer.labels = encoding.DictToMessage(
        args.labels, messages.Transformer.LabelsValue)
  return req


def GetExistingResource(api_version, request_message):
  """Get the modified resource.

  Args:
    api_version: The request release track.
    request_message: request message type in the python client.

  Returns:
    The modified resource.
  """
  return utils.GetClient(api_version).projects_locations_transformers.Get(
      request_message)


def ProcessOutput(response, args):
  """Wait for operations to finish and return the resource."""
  api_version = utils.GetApiVersionFromArgs(args)
  utils.WaitForOperation(response, api_version)

  project = utils.GetProject()
  location = utils.GetLocation(args)
  resource_ref = resources.REGISTRY.Create(
      'mediaasset.projects.locations.transformers',
      projectsId=project,
      locationsId=location,
      transformersId=args.transformer)

  if 'delete' in args.command_path:
    # No need to send another get request to check for the deleted complex type.
    return response
  request_message = utils.GetApiMessage(
      api_version).MediaassetProjectsLocationsTransformersGetRequest(
          name=resource_ref.RelativeName())

  return GetExistingResource(api_version, request_message)

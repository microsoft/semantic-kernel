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

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
import six

MEDIA_ASSET_API = 'mediaasset'
OPERATIONS_COLLECTION = 'mediaasset.projects.locations.operations'
PARENT_TEMPLATE = 'projects/{}/locations/{}'
ASSET_TYPE_PARENT_TEMPLATE = 'projects/{}/locations/{}/assetTypes/{}'
ASSET_PARENT_TEMPLATE = 'projects/{}/locations/{}/assetTypes/{}/assets/{}'
ANNOTATION_PARENT_TEMPLATE = ASSET_PARENT_TEMPLATE + '/annotationSets/{}'


def GetApiMessage(api_version):
  return apis.GetMessagesModule(MEDIA_ASSET_API, api_version)


def GetClient(api_version):
  return apis.GetClientInstance(MEDIA_ASSET_API, api_version)


def GetProject():
  return properties.VALUES.core.project.Get(required=True)


def GetLocation(args):
  return args.location or properties.VALUES.media_asset.location.Get(
      required=True)


def GetParentTemplate(project, location):
  return PARENT_TEMPLATE.format(project, location)


def GetAssetTypeParentTemplate(project, location, asset_type):
  return ASSET_TYPE_PARENT_TEMPLATE.format(project, location, asset_type)


def GetAssetParentTemplate(project, location, asset_type, asset):
  return ASSET_PARENT_TEMPLATE.format(project, location, asset_type, asset)


def GetAnnotationParentTemplate(project, location, asset_type, asset,
                                annotation_set):
  return ANNOTATION_PARENT_TEMPLATE.format(project, location, asset_type, asset,
                                           annotation_set)


class UnsupportedReleaseTrackError(Exception):
  """Raised when calling an api with a unsupported release track."""


def GetApiVersionFromArgs(args):
  """Return API version based on args.

  Update this whenever there is a new version.

  Args:
    args: The argparse namespace.

  Returns:
    API version (e.g. v1alpha or v1beta).

  Raises:
    UnsupportedReleaseTrackError: If invalid release track from args.
  """

  release_track = args.calliope_command.ReleaseTrack()
  if release_track == base.ReleaseTrack.ALPHA:
    return 'v1alpha'
  if release_track == base.ReleaseTrack.BETA:
    return 'v1beta'
  if release_track == base.ReleaseTrack.GA:
    return 'v1'
  raise UnsupportedReleaseTrackError(release_track)


def ValidateMediaAssetMessage(message):
  """Validate all parsed message from file are valid."""
  errors = encoding.UnrecognizedFieldIter(message)
  unrecognized_field_paths = []
  for edges_to_message, field_names in errors:
    message_field_path = '.'.join(six.text_type(e) for e in edges_to_message)
    for field_name in field_names:
      unrecognized_field_paths.append('{}.{}'.format(message_field_path,
                                                     field_name))
  if unrecognized_field_paths:
    error_msg_lines = [
        'Invalid schema, the following fields are unrecognized:'
    ] + unrecognized_field_paths
    raise exceptions.Error('\n'.join(error_msg_lines))


def WaitForOperation(response, api_version):
  """Wait for an operation to finish."""
  operation_ref = resources.REGISTRY.ParseRelativeName(
      response.name, collection=OPERATIONS_COLLECTION)
  return waiter.WaitFor(
      waiter.CloudOperationPollerNoResources(
          GetClient(api_version).projects_locations_operations), operation_ref,
      'Waiting for [{0}] to finish'.format(operation_ref.Name()))

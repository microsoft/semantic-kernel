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
"""Base utility used for updating resource maps."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis_internal
from googlecloudsdk.command_lib.util.apis import registry
from googlecloudsdk.command_lib.util.resource_map import base
from googlecloudsdk.command_lib.util.resource_map.resource_map import ResourceMap


class ResourceMapUpdateError(base.ResourceMapError):
  """General Purpose Exception."""


class ResourceMapUpdateUnmatchedError(ResourceMapUpdateError):
  """Exception when an update map has unmatched members."""

  def __init__(self, unmatched):
    super(ResourceMapUpdateUnmatchedError, self).__init__(
        'Registered update map has unmatched members. Please '
        'fix error leading to mismatch or add to allowlist: \n {}'.format(
            unmatched))


class MapUpdateUtil(object):
  """Resource Map Update Utility object.

  This object allows the execution of Resource Map updates as well as the
  registering of custom update masks for specific resource map metadata values.

  Attributes:
    _update_maps: Registered update maps used to add metadata values to the
      resource map.
    _resource_map: The resource map being updated.
  """

  _update_maps = []
  _resource_map = {}

  def __init__(self, resource_map):
    self._resource_map = resource_map

  def register_update_map(self, update_map):
    """Registers an update map and map of allowed mismatches while updating.

    Args:
      update_map: Map with an analogous structure to the resource map which
        contains metadata fields and values to apply to the resource map.
    """
    self._update_maps.append(update_map)

  def update(self, skip_export=False, skip_registered_maps=False):
    """Updates resource map with apitools collections and registered maps.

    Args:
      skip_export: If true, will update map but not save to file.
      skip_registered_maps: If true, will only update map with apitools
        collections and no registered maps.
    """
    self.update_map_with_collections()
    if not skip_registered_maps:
      self.update_map_with_registered_maps()
    if not skip_export:
      self._resource_map.export()

  def update_map_with_registered_maps(self):
    """Updates resource map using registered resource maps.

    This will iterate through each registered resource map and apply any
    contained metadata to the resource map. All registered resource maps must
    have an analogous structure to the underlying resource map.
    """
    for update_map in self._update_maps:
      for api in self._resource_map:
        api_name = api.get_api_name()
        for resource in api:
          resource_name = resource.get_resource_name()
          if api_name in update_map and resource_name in update_map[api_name]:
            for key, value in update_map[api_name][resource_name].items():
              setattr(resource, key, value)

  def update_map_with_collections(self):
    """Updates the resource map with existing apitools collections."""
    apitools_api_version_map = self.get_apitools_apis()
    apitools_api_names = set(apitools_api_version_map.keys())

    yaml_file_api_names = {api.get_api_name() for api in self._resource_map}

    apis_to_add = apitools_api_names - yaml_file_api_names
    apis_to_update = apitools_api_names & yaml_file_api_names
    apis_to_remove = yaml_file_api_names - apitools_api_names

    for api_name in apis_to_add:
      self.add_api_to_map(api_name, apitools_api_version_map[api_name])

    for api_name in apis_to_update:
      self.update_api_in_map(api_name, apitools_api_version_map[api_name])

    for api_name in apis_to_remove:
      self._resource_map.remove_api(api_name)

  def add_api_to_map(self, api_name, api_versions):
    """Adds an API and all contained resources to the ResourceMap.

    Args:
      api_name: Name of the api to be added.
      api_versions: All registered versions of the api.
    """
    api_data = base.ApiData(api_name, {})
    collection_to_apis_dict = self.get_collection_to_apis_dict(
        api_name, api_versions)
    for collection_name, supported_apis in collection_to_apis_dict.items():
      api_data.add_resource(
          base.ResourceData(collection_name, api_name,
                            {'supported_apis': supported_apis}))

    self._resource_map.add_api(api_data)

  def update_api_in_map(self, api_name, api_versions):
    """Updates resources in an existing API in the ResourceMap.

    Args:
      api_name: Name of the api to be added.
      api_versions: All registered versions of the api.
    """
    api_data = self._resource_map.get_api(api_name)

    collection_to_apis_dict = self.get_collection_to_apis_dict(
        api_name, api_versions)
    collection_names = set(collection_to_apis_dict.keys())
    map_resource_names = {resource.get_resource_name() for resource in api_data}

    resources_to_add = collection_names - map_resource_names
    resources_to_update = collection_names & map_resource_names
    resources_to_remove = map_resource_names - collection_names

    for resource_name in resources_to_add:
      supported_apis = collection_to_apis_dict[resource_name]
      api_data.add_resource(
          base.ResourceData(resource_name, api_name,
                            {'supported_apis': supported_apis}))

    for resource_name in resources_to_update:
      supported_apis = collection_to_apis_dict[resource_name]
      resource_data = api_data.get_resource(resource_name)
      if 'supported_apis' in resource_data:
        resource_data.update_metadata('supported_apis', supported_apis)
      else:
        resource_data.add_metadata('supported_apis', supported_apis)

    for resource_name in resources_to_remove:
      api_data.remove_resource(resource_name)

  def get_collection_to_apis_dict(self, api_name, api_versions):
    """Gets collection names for all collections in all versions of an api.

    Args:
      api_name: Name of the api to be added.
      api_versions: All registered versions of the api.

    Returns:
      collction_names: Names of every registered apitools collection.
    """
    collection_to_apis_dict = {}
    for version in api_versions:
      resource_collections = [
          registry.APICollection(c)
          for c in apis_internal._GetApiCollections(api_name, version)  # pylint:disable=protected-access
      ]
      for resource_collection in resource_collections:
        if resource_collection.name in collection_to_apis_dict:
          collection_to_apis_dict[resource_collection.name].append(version)
        else:
          collection_to_apis_dict[resource_collection.name] = [version]
    return collection_to_apis_dict

  # TODO(b/197004182) Refactor for common use between maps
  def get_apitools_apis(self):
    """Returns all apitools collections and associated versions."""
    apitools_apis = {}
    for api in registry.GetAllAPIs():
      if api.name not in apitools_apis:
        apitools_apis[api.name] = []
      apitools_apis[api.name].append(api.version)

    return apitools_apis


def update():
  """Primary entrypoint for updating the base resource map."""
  resource_map = ResourceMap()
  updater = MapUpdateUtil(resource_map)
  updater.update()

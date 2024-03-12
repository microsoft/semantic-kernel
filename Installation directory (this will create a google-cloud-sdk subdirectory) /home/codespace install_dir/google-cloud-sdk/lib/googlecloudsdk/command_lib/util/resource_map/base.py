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
"""Utility for retrieving and parsing the Resource Map."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.util import files
import six

_RELEASE_TRACKS = [
    six.text_type(track) for track in calliope_base.ReleaseTrack.AllValues()
]


class ResourceMapError(exceptions.Error):
  """General Purpose Exception."""


class ResourceMapInitializationError(ResourceMapError):
  """Exception for when an error occurs while initializing the resource map."""

  def __init__(self, init_error):
    super(ResourceMapInitializationError,
          self).__init__('Error while '
                         'initializing resource map: [{}]'.format(init_error))


class PrivateAttributeNotFoundError(ResourceMapError):
  """Exception for when a private attribute that doesn't exist is accessed."""

  def __init__(self, data_wrapper, attribute_name):
    super(PrivateAttributeNotFoundError,
          self).__init__('[{}] does not have private attribute [{}].'.format(
              data_wrapper, attribute_name))


class ApiNotFoundError(ResourceMapError):
  """Exception for when an API does not exist in the ResourceMap."""

  def __init__(self, api_name):
    super(ApiNotFoundError,
          self).__init__('[{}] API not found in ResourceMap.'.format(api_name))


class ApiAlreadyExistsError(ResourceMapError):
  """Exception for when an API being added already exists in the ResourceMap."""

  def __init__(self, api_name):
    super(ApiAlreadyExistsError, self).__init__(
        '[{}] API already exists in ResourceMap.'.format(api_name))


class ResourceNotFoundError(ResourceMapError):
  """Exception for when a Resource does not exist in the API."""

  def __init__(self, resource_name):
    super(ResourceNotFoundError, self).__init__(
        '[{}] resource not found in ResourceMap.'.format(resource_name))


class ResourceAlreadyExistsError(ResourceMapError):
  """Exception for when a Resource being added already exists in the ResourceMap."""

  def __init__(self, api_name):
    super(ResourceAlreadyExistsError, self).__init__(
        '[{}] API already exists in ResourceMap.'.format(api_name))


class MetadataNotFoundError(ResourceMapError):
  """Exception for when a metadata field does not exist in the Resource."""

  def __init__(self, resource_name, metadata_field):
    super(MetadataNotFoundError, self).__init__(
        '[{}] metadata field not found in [{}] Resource.'.format(
            metadata_field, resource_name))


class TrackLevelResourceReleaseTrackError(ResourceMapError):
  """Exception for when an attempt to access a releast track of a RT occurs."""

  def __init__(self, attempted_rt, accessed_rt):
    super(TrackLevelResourceReleaseTrackError,
          self).__init__('Attempted accessing of [{}'
                         '] track of TrackLevelResourceData[{}'
                         ']'.format(attempted_rt, accessed_rt))


class MetadataAlreadyExistsError(ResourceMapError):
  """Exception for when a metadata field does not exist in the Resource."""

  def __init__(self, resource_name, metadata_field):
    super(MetadataAlreadyExistsError, self).__init__(
        '[{}] metadata already exists in [{}] Resource.'.format(
            metadata_field, resource_name))


class UnwrappedDataException(ResourceMapError):
  """Exception for when unwrapped data is added to the map."""

  def __init__(self, field_type, data):
    super(UnwrappedDataException, self).__init__(
        'The following data must be wrapped in a(n) {}Data wrapper prior to '
        'being added to the resource map: [{}]'
        .format(field_type, data))


class ResourceMapBase(six.with_metaclass(abc.ABCMeta)):
  """Base data wrapper class for Resource Map metadata yaml files.

  This object loads the relevant resource map file upon instantiation and sets
  the parsed dictionary as the internal attribute _resource_map_data. Underlying
  dictionary data is never interacted with directly, and is instead is
  set/retrieved/interacted with via an ApiData wrapper object.

  Attributes:
    _resource_map_data: Dict containing metadata for each resource in each api.
  """

  def __init__(self):
    self._map_file_path = None
    self._schema_file_path = None
    self._register_paths()
    self._resource_map_data = {}
    self._load_resource_map()

  def __getattr__(self, api_name):
    """Returns underlying API data when accessing attribute."""
    if api_name.startswith('_'):
      raise PrivateAttributeNotFoundError('ResourceMap', api_name)
    return self.get_api(api_name)

  def __contains__(self, api_name):
    """Returns True if api_name exists in self._resource_map_data."""
    return api_name in self._resource_map_data

  def __iter__(self):
    """Yields ApiData wrapper objects for each API in _resource_map_data."""
    for api_name, api_data in six.iteritems(self._resource_map_data):
      yield ApiData(api_name, api_data)

  def __eq__(self, other):
    return self.to_dict() == other.to_dict()

  @abc.abstractmethod
  def _register_paths(self):
    """Must be overridden by child classes to register map and schema paths.

    Must explicitly set self._map_file_path and self._schema_file_path to
    appropriate filepaths in the overridden method of the child class.
    """
    pass

  def _load_resource_map(self):
    """Loads the ~/resource_map.yaml file into self._resource_map_data."""
    try:
      with files.FileReader(self._map_file_path) as f:
        self._resource_map_data = yaml.load(f)
      if not self._resource_map_data:
        self._resource_map_data = {}
    except files.MissingFileError as err:
      raise ResourceMapInitializationError(err)

  def _export_resource_map(self, file_path=None, prune=False, validate=True):
    """Prunes and exports self._resource_map_data to ~/resource_map.yaml."""
    try:
      if prune:
        self.prune()
      if validate:
        self._validate_resource_map()
      with files.FileWriter(file_path or self._map_file_path) as f:
        yaml.dump(self._resource_map_data, stream=f)
    except files.MissingFileError as err:
      raise ResourceMapInitializationError(err)

  def _validate_resource_map(self):
    """Validates resource map against ~/resource_map_schema.yaml."""
    yaml_validator.Validator(self._schema_file_path).Validate(
        self._resource_map_data)

  def to_dict(self):
    return self._resource_map_data

  def prune(self):
    """Prunes the resource map, removing redundant metadata values in the map.

    Calls prune() on each ApiData wrapper object, which in turn calls prune()
    on each underlying resource. Pruning each resource will remove any instances
    of a track-specific metadata field being set to the same value as the parent
    resource metadata field, eliminating any redundancies and keeping the map
    as clean as possible.
    """

    for api_data in iter(self):
      api_data.prune()

  def get_api(self, api_name):
    """Returns the api data wrapped in an ApiData object."""
    if api_name not in self._resource_map_data:
      raise ApiNotFoundError(api_name)
    return ApiData(api_name, self._resource_map_data[api_name])

  def add_api(self, api_data):
    """Adds an api to the resource map.

    Args:
      api_data: Data for api being added. Must be wrapped in an ApiData object.

    Raises:
      ApiAlreadyExistsError: API already exists in resource map.
      UnwrappedDataException: API data attempting to be added without being
        wrapped in an ApiData wrapper object.
    """
    if not isinstance(api_data, ApiData):
      raise UnwrappedDataException('Api', api_data)
    elif api_data.get_api_name() in self._resource_map_data:
      raise ApiAlreadyExistsError(api_data.get_api_name())
    else:
      self._resource_map_data.update(api_data.to_dict())

  def update_api(self, api_data):
    """Updates an API's data with the provided api data.

    Args:
      api_data: API Data to update the api with. Must be provided as an ApiData
      object.

    Raises:
      ApiNotFoundError: Api to be updated does not exist.
      UnwrappedDataException: API data attempting to be added without being
        wrapped in an ApiData wrapper object.
    """
    if not isinstance(api_data, ApiData):
      raise UnwrappedDataException('Api', api_data)
    if api_data.get_api_name() not in self._resource_map_data:
      raise ApiNotFoundError(api_data.get_api_name())
    else:
      self._resource_map_data.update(api_data.to_dict())

  def remove_api(self, api_name):
    """Removes an API from the resource map."""
    if api_name not in self._resource_map_data:
      raise ApiNotFoundError(api_name)
    del self._resource_map_data[api_name]

  def export(self, file_path=None):
    """Public method to export resource map to file."""
    self._export_resource_map(file_path)


class ApiData(object):
  """Data wrapper for an API object in the Resource Map metadata file.

  Attributes:
    _api_name: Name of the API.
    _api_data: Dict of resources and associated metadata constituting the api.
  """

  def __init__(self, api_name, api_data):
    self._api_name = api_name
    self._api_data = api_data

  def __getattr__(self, resource_name):
    """Returns the specified resource's data wrapped in a ResourceData object."""
    if resource_name.startswith('_'):
      raise PrivateAttributeNotFoundError('ApiData', resource_name)
    return ResourceData(resource_name, self._api_name,
                        self._api_data[resource_name])

  def __contains__(self, resource_name):
    return resource_name in self._api_data

  def __iter__(self):
    """Yields ResourceData wrapper objects for each API in _resource_map_data."""
    for resource_name, resource_data in self._api_data.items():
      yield ResourceData(resource_name, self._api_name, resource_data)

  def __repr__(self):
    return repr(self._api_data)

  def __eq__(self, other):
    return self.to_dict() == other.to_dict()

  def to_str(self):
    return six.text_type(self.to_dict())

  def to_dict(self):
    return {self.get_api_name(): self._api_data}

  def get_api_name(self):
    return six.text_type(self._api_name)

  def get_resource(self, resource_name):
    """Returns the data for the specified resource in a ResourceData object."""
    if resource_name not in self._api_data:
      raise ResourceNotFoundError(resource_name)
    return ResourceData(resource_name, self._api_name,
                        self._api_data[resource_name])

  def add_resource(self, resource_data):
    if not isinstance(resource_data, ResourceData):
      raise UnwrappedDataException('Resource', resource_data)
    elif resource_data.get_resource_name() in self._api_data:
      raise ResourceAlreadyExistsError(resource_data.get_resource_name())
    else:
      self._api_data.update(resource_data.to_dict())

  def update_resource(self, resource_data):
    if not isinstance(resource_data, ResourceData):
      raise UnwrappedDataException('Resource', resource_data)
    elif resource_data.get_resource_name() not in self._api_data:
      raise ResourceNotFoundError(resource_data.get_resource_name())
    else:
      self._api_data.update(resource_data.to_dict())

  def remove_resource(self, resource_name, must_exist=True):
    if must_exist and resource_name not in self._api_data:
      raise ResourceNotFoundError(resource_name)
    del self._api_data[resource_name]

  def prune(self):
    for resource_data in iter(self):
      resource_data.prune()


class ResourceData(object):
  """Data wrapper for a Resource object in the ResourceMap metadata file.

  Attributes:
    _resource_name: Name of the resource.
    _api_name: Name of the parent api.
    _resource_data: Metadata for the resource.
  """

  def __init__(self, resource_name, api_name, resource_data):
    self._resource_name = resource_name
    self._api_name = api_name
    self._resource_data = resource_data

  def __getattr__(self, metadata_field):
    """Returns metadata value or TrackLevelResourceData object.

    Attribute being accessed will be either a metadata field for the resource,
    or the release track (GA, BETA, or ALPHA). If the attribute is a metadata
    field the appropriate value will be returned from self._resource_data. If
    the atatribute is a release track, a TrackLevelResourceData object will be
    returned. This enables both of the following usecases:

      `value = map.api.resource.metadata_field` OR
      'value = map.api.resource.ALPHA.metadata_field`

    Args:
      metadata_field: Field or release track being accessed

    Returns:
      Metadata field value OR TrackLevelResourceData object.

    Raises:
      MetadataNotFoundError: Metadata field does not exist.
      PrivateAttributeNotFoundError: Private attribute doesn't exist in object.

    """
    if metadata_field in _RELEASE_TRACKS:
      return self.get_release_track_data(metadata_field)
    elif metadata_field.startswith('_'):
      raise PrivateAttributeNotFoundError('ResourceData', metadata_field)
    else:
      return self.get_metadata(metadata_field)

  def __setattr__(self, metadata_field, value):
    """Sets the specified metadata field to the provided value.

    If the object is not yet instantiated, then standard __setattr__ behavior
    is observed, allowing for proper object instantiation. After initialization,
    the specified metadata field within self._resource_data is set to the
    provided value

    Args:
      metadata_field: Metadata field to set the value for.
      value: Value to set the specified metadata field to.

    Returns:
      True
    """

    if metadata_field.startswith('_'):
      super(ResourceData, self).__setattr__(metadata_field, value)
    elif metadata_field not in self._resource_data:
      self.add_metadata(metadata_field, value)
    else:
      self.update_metadata(metadata_field, value)

  def __eq__(self, other):
    return self.to_dict() == other.to_dict()

  def __contains__(self, metadata_field):
    return self.has_metadata_field(metadata_field)

  def prune(self):
    """Removes any redundant metadata specifications between track and top."""
    for track in _RELEASE_TRACKS:
      if track in self._resource_data:
        track_resource_data = self._resource_data[track]

        for key in list(track_resource_data.keys()):
          if key in self._resource_data and self._resource_data[
              key] == track_resource_data[key]:
            del track_resource_data[key]

        if not track_resource_data:
          del self._resource_data[track]

  def to_dict(self):
    return {self.get_resource_name(): self._resource_data}

  def has_metadata_field(self, metadata_field):
    return metadata_field in self._resource_data

  def get_resource_name(self):
    return self._resource_name

  def get_api_name(self):
    return self._api_name

  def get_full_collection_name(self):
    return '{}.{}'.format(self.get_api_name(), self.get_resource_name())

  def get_metadata(self, metadata_field):
    if metadata_field not in self._resource_data:
      raise MetadataNotFoundError(self._resource_name, metadata_field)
    return self._resource_data[metadata_field]

  def get_release_track_data(self, release_track):
    return TrackLevelResourceData(
        self._resource_name,
        self._api_name,
        self._resource_data,
        track=release_track)

  def add_metadata(self, metadata_field, value):
    if metadata_field in self._resource_data:
      raise MetadataAlreadyExistsError(self._resource_name, metadata_field)
    else:
      self._resource_data[metadata_field] = value

  def update_metadata(self, metadata_field, value):
    if metadata_field not in self._resource_data:
      raise MetadataNotFoundError(self._resource_name, metadata_field)
    else:
      self._resource_data[metadata_field] = value

  def remove_metadata(self, metadata_field):
    if metadata_field not in self._resource_data:
      raise MetadataNotFoundError(self._resource_name, metadata_field)
    else:
      del self._resource_data[metadata_field]


class TrackLevelResourceData(ResourceData):
  """Data wrapper for track-specific resource metadata.

  This data wrapper represents the metadata for a specific release track of a
  resource. Retrieval of metadata will first check for a track level
  specification of the metadata, and if not found will then retrieve the
  top level metadata value.

  Attributes:
    _resource_name: Name of the resource.
    _api_name: Name of the parent api.
    _resource_data: Metadata for the resource.
    _track: Release track for the resource.
    _track_resource_data: Track specific metadata for the resource.
  """

  def __init__(self, resource_name, api_name, resource_data, track):
    self._track = track
    self._track_resource_data = resource_data.get(self._track, {})
    super(TrackLevelResourceData, self).__init__(resource_name, api_name,
                                                 resource_data)

  def __getattr__(self, metadata_field):
    """Retrieves the track-specific metadata value for the resource.

    If the specified release track does not have a specified value, the parent
    metadata field value for the resource will be returned.

    Args:
      metadata_field: Metadata field value to retrieve

    Returns:
      Metadata field value for the specified release track-specific or the
      parent metadata field.

    Raises:
      MetadataNotFoundError: Metadata field value wasn't found for the specific
      track or for the parent.
      PrivateAttributeNotFoundError: Private attribute doesn't exist in object.
    """
    if metadata_field.startswith('_'):
      raise PrivateAttributeNotFoundError('TrackLevelResourceData',
                                          metadata_field)
    else:
      return self.get_metadata(metadata_field)

  def __setattr__(self, metadata_field, value):
    """Sets the specified metadata field to the provided value.

    If the object is not yet instantiated, then standard __setattr__ behavior
    is observed, allowing for proper object intitialization. After
    initialization, the specified metadata field for the release track is set
    to the provided value.

    Args:
      metadata_field: Metadata field to set the value for.
      value: Value to set the specified metadata field to.

    Returns:
      True
    """

    if metadata_field.startswith('_'):
      super(TrackLevelResourceData, self).__setattr__(metadata_field, value)
    else:
      if metadata_field in self._track_resource_data:
        return self.update_metadata(metadata_field, value)
      else:
        return self.add_metadata(metadata_field, value)

  def to_dict(self):
    return {self._resource_name: self._resource_data}

  def get_metadata(self, metadata_field):
    if metadata_field in self._track_resource_data:
      return self._track_resource_data[metadata_field]
    elif metadata_field in self._resource_data:
      return self._resource_data[metadata_field]
    else:
      raise MetadataNotFoundError(self._resource_name, metadata_field)

  def add_metadata(self, metadata_field, value):
    if metadata_field in self._track_resource_data:
      raise MetadataAlreadyExistsError(self._resource_name, metadata_field)
    else:
      self._track_resource_data[metadata_field] = value

  def update_metadata(self, metadata_field, value):
    if metadata_field not in self._track_resource_data:
      raise MetadataNotFoundError(self._resource_name, metadata_field)
    else:
      self._track_resource_data[metadata_field] = value

  def remove_metadata(self, metadata_field):
    if metadata_field not in self._track_resource_data:
      raise MetadataNotFoundError(self._resource_name, metadata_field)
    else:
      del self._track_resource_data[metadata_field]

  def get_release_track(self):
    return self._track

  def get_release_track_data(self, release_track):
    raise TrackLevelResourceReleaseTrackError(release_track, self._track)

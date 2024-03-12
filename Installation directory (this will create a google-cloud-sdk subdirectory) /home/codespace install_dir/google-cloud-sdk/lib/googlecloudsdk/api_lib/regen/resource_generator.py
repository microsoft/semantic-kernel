# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Resource definition generator."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from collections import OrderedDict
import json
import re

from googlecloudsdk.api_lib.util import resource as resource_util
from googlecloudsdk.core.util import files
import six


_COLLECTION_SUB_RE = r'[a-zA-Z][a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)+'
_METHOD_ID_RE_RAW = r'(?P<collection>{collection})\.get'.format(
    collection=_COLLECTION_SUB_RE)
_METHOD_ID_RE = re.compile(_METHOD_ID_RE_RAW)
DEFAULT_PATH_NAME = ''


class Error(Exception):
  """Errors raised by this module."""


class NoMatchingMethodError(Error):
  """Raised when no matching method can be found."""


class UnsupportedDiscoveryDoc(Error):
  """Raised when some unsupported feature is detected."""


class ConflictingCollection(Error):
  """Raised when collection names conflict and need to be resolved."""


class DiscoveryDoc(object):
  """Encapsulates access to discovery doc."""

  def __init__(self, discovery_doc_dict):
    self._discovery_doc_dict = discovery_doc_dict

  @classmethod
  def FromJson(cls, path):
    with files.FileReader(path) as f:
      return cls(json.load(f, object_pairs_hook=OrderedDict))

  @property
  def api_name(self):
    return self._discovery_doc_dict['name']

  @property
  def api_version(self):
    return self._discovery_doc_dict['version']

  @property
  def base_url(self):
    return self._discovery_doc_dict['baseUrl']

  @property
  def docs_url(self):
    return self._discovery_doc_dict['documentationLink']

  def GetResourceCollections(self, custom_resources, api_version):
    """Returns all resources collections found in this discovery doc.

    Args:
      custom_resources: {str, str}, A mapping of collection name to path that
          have been registered manually in the yaml file.
      api_version: Override api_version for each found resource collection.

    Returns:
      list(resource_util.CollectionInfo).
    """
    collections = self._ExtractResources(
        api_version, self._discovery_doc_dict)
    collections.extend(
        self._GenerateMissingParentCollections(
            collections, custom_resources, api_version))
    return collections

  def _ExtractResources(self, api_version, infos):
    """Extract resource definitions from discovery doc."""
    collections = []

    if infos.get('methods'):
      methods = infos.get('methods')
      get_method = methods.get('get')
      if get_method:
        collection_info = self._GetCollectionFromMethod(
            api_version, get_method)
        collections.append(collection_info)
    if infos.get('resources'):
      for _, info in infos.get('resources').items():
        subresource_collections = self._ExtractResources(api_version, info)
        collections.extend(subresource_collections)
    return collections

  def _GetCollectionFromMethod(self, api_version, get_method):
    """Created collection_info object given discovery doc get_method."""
    collection_name = _ExtractCollectionName(get_method['id'])
    # Remove api name from collection. It might not match passed in, or
    # even api name in url. We choose to use api name as defined by url.
    collection_name = collection_name.split('.', 1)[1]
    flat_path = get_method.get('flatPath')
    path = get_method.get('path')
    return self._MakeResourceCollection(
        api_version, collection_name, path, flat_path
    )

  def _MakeResourceCollection(
      self, api_version, collection_name, path, flat_path=None
  ):
    """Make resource collection object given its name and path."""
    if flat_path == path:
      flat_path = None
    # Normalize base url so it includes api_version.
    url = self.base_url + path
    url_api_name, url_api_version, path = resource_util.SplitEndpointUrl(url)
    if url_api_version != api_version:
      raise UnsupportedDiscoveryDoc(
          'Collection {0} for version {1}/{2} is using url {3} '
          'with version {4}'.format(
              collection_name, self.api_name, api_version, url, url_api_version
          )
      )
    if flat_path:
      _, _, flat_path = resource_util.SplitEndpointUrl(
          self.base_url + flat_path
      )
    # Use url_api_name instead as it is assumed to be source of truth.
    # Also note that api_version not always equal to url_api_version,
    # this is the case where api_version is an alias.
    url = url[:-len(path)]
    return resource_util.CollectionInfo(
        url_api_name,
        api_version,
        url,
        self.docs_url,
        collection_name,
        path,
        {DEFAULT_PATH_NAME: flat_path} if flat_path else {},
        resource_util.GetParamsFromPath(path),
    )

  def _GenerateMissingParentCollections(
      self, collections, custom_resources, api_version
  ):
    """Generates parent collections for any existing collection missing one.

    Args:
      collections: [resource.CollectionInfo], The existing collections from the
        discovery doc.
      custom_resources: {str, str}, A mapping of collection name to path that
        have been registered manually in the yaml file.
      api_version: Override api_version for each found resource collection.

    Raises:
      ConflictingCollection: If multiple parent collections have the same name
        but different paths, and a custom resource has not been declared to
        resolve the conflict.

    Returns:
      [resource.CollectionInfo], Additional collections to include in the
      resource module.
    """
    all_names = {c.name: c for c in collections}
    all_paths = {c.GetPath(DEFAULT_PATH_NAME) for c in collections}
    generated = []
    in_progress = list(collections)
    to_process = []
    ignored = {}

    while in_progress:
      # We need to do multiple passes to recursively create all parent
      # collections of generated collections as well.
      for c in in_progress:
        parent_name, parent_path = _GetParentCollection(c)
        if not parent_name:
          continue  # No parent collection.
        if parent_path in all_paths:
          continue  # Parent path is already explicitly registered.
        if parent_name in custom_resources:
          # There is a manual entry to resolve this, don't add this collection.
          ignored.setdefault(parent_name, set()).add(parent_path)
          continue
        if parent_name in all_names:
          # Parent path is not registered, but a collection with the parent name
          # already exists. This conflict needs to be resolved manually.
          raise ConflictingCollection(
              'In API [{api}/{version}], the parent of collection [{c}] is not '
              'registered, but a collection with [{parent_name}] and path '
              '[{existing_path}] already exists. Update the api config file to '
              'manually add the parent collection with a path of '
              '[{parent_path}].'.format(
                  api=c.api_name, version=api_version, c=c.name,
                  parent_name=parent_name, existing_path=
                  all_names[parent_name].GetPath(DEFAULT_PATH_NAME),
                  parent_path=parent_path))
        parent_collection = self.MakeResourceCollection(
            parent_name, parent_path, True, api_version)
        to_process.append(parent_collection)
        all_names[parent_name] = parent_collection
        all_paths.add(parent_path)

      generated.extend(to_process)
      in_progress = to_process
      to_process = []

    # Print warnings if people have declared custom resources that are
    # unnecessary.
    for name, paths in six.iteritems(ignored):
      if len(paths) > 1:
        # There are multiple unique paths for this collection name. It is
        # required to be declared to disambiguate.
        continue
      path = paths.pop()
      if path == custom_resources[name]['path']:
        # There is 1 path and it is the same as the custom one registered.
        print(('WARNING: Custom resource [{}] in API [{}/{}] is redundant.'
               .format(name, self.api_name, api_version)))
    return generated

  def MakeResourceCollection(self, collection_name, path, enable_uri_parsing,
                             api_version):
    _, url_api_version, _ = resource_util.SplitEndpointUrl(self.base_url)
    if url_api_version:
      base_url = self.base_url
    else:
      base_url = '{}{}/'.format(self.base_url, api_version)
    return resource_util.CollectionInfo(
        self.api_name, api_version, base_url, self.docs_url,
        collection_name, path, {}, resource_util.GetParamsFromPath(path),
        enable_uri_parsing)


def _ExtractCollectionName(method_id):
  """Extract the name of the collection from a method ID."""
  match = _METHOD_ID_RE.match(method_id)
  if match:
    return match.group('collection')
  else:
    raise NoMatchingMethodError(
        'Method {0} does not match regexp {1}.'
        .format(method_id, _METHOD_ID_RE_RAW))


def _GetParentCollection(collection_info):
  """Generates the name and path for a parent collection.

  Args:
    collection_info: resource.CollectionInfo, The collection to calculate the
      parent of.

  Returns:
    (str, str), A tuple of parent name and path or (None, None) if there is no
    parent.
  """
  params = collection_info.GetParams(DEFAULT_PATH_NAME)
  if len(params) < 2:
    # There is only 1 param, this is the top level.
    return None, None
  path = collection_info.GetPath(DEFAULT_PATH_NAME)
  # Chop off the last segment in the path.
  #   a/{a}/b/{b} --> a/{a}
  #   a/{a}/b --> a/{a}
  #   a/{a}/b/{b}/{c} --> a/{a}
  #   a/{a}/b/c/{b}/{c} --> a/{a}
  parts = path.split('/')
  _PopSegments(parts, True)
  _PopSegments(parts, False)
  if not parts:
    return None, None

  parent_path = '/'.join(parts)
  # Sometimes the parent is just all parameters (when the parent can be a
  # projects, org, or folder. This is not useful as a parent collection so just
  # skip it.
  _PopSegments(parts, True)
  if not parts:
    return None, None

  if '.' in collection_info.name:
    # The discovery doc uses dotted paths for collections, chop off the last
    # segment and use that.
    parent_name, _ = collection_info.name.rsplit('.', 1)
  else:
    # The discovery doc uses short names for collections, use the name of the
    # last static part of the path.
    parent_name = parts[-1]
  return parent_name, parent_path


def _PopSegments(parts, is_params):
  if parts:
    while (parts[-1].startswith('{') == is_params and
           parts[-1].endswith('}') == is_params):
      parts.pop()
      if not parts:
        break

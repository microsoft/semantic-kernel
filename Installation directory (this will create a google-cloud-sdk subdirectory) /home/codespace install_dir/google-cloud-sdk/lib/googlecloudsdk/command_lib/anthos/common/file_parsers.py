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
"""Classes for reading and writing Anthos related files."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import copy
import io


from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files

try:  # Fallback for <= PY3.2
  collections_abc = collections.abc
except AttributeError:
  collections_abc = collections

AUTH_VERSION_1_ALPHA = 'authentication.gke.io/v1alpha1'
AUTH_VERSION_2_ALPHA = 'authentication.gke.io/v2alpha1'
API_VERSION = 'apiVersion'


class YamlConfigObjectError(core_exceptions.Error):
  """Raised when an invalid Operation is invoked on YamlConfigObject."""


class YamlConfigFileError(core_exceptions.Error):
  """Base class for YamlConfigFile Errors."""


class YamlConfigObjectFieldError(YamlConfigObjectError):
  """Raised when an invalid field is used on  a YamlConfigObject."""

  def __init__(self, field, object_type, custom_message=None):
    error_msg = 'Invalid field [{}] for YamlConfigObject type [{}]'.format(
        field, object_type)
    if custom_message:
      error_msg = '{}: {}'.format(error_msg, custom_message)
    super(YamlConfigObjectFieldError, self).__init__(error_msg)


def FindOrSetItemInDict(item, item_path, item_sep='.', set_value=None):
  """Finds (potentially) nested value based on specified node_path.

  If set_value is passed will set the value at item_path,
  creating if needed.
  Args:
      item: Dict, Map like object to search.
      item_path: str, An item_sep separated path to nested item in map.
      item_sep: str, Path item separator, default is '.'.
      set_value: object, value to set at item_path. If path is not found
        create a new item at item_path with value of set_value.

  Returns:
      Object, data found in input item at item_path or None.

  Raises:
    KeyError: If item_path not found or empty.
  """
  if not item_path:
    raise KeyError(item_path)
  parts = item_path.split(item_sep)
  parts.reverse()
  context = item
  while parts:
    part = parts.pop()
    if part in context and yaml.dict_like(context):  # path element exists in
      # in context AND context
      # is dict() like.
      if set_value and not parts:  # e.g. at bottom of path with a value to set
        context[part] = set_value
      context = context.get(part)  # continue down the path
    else:  # part not found
      if set_value and yaml.dict_like(context):  # Upsert New Value if possible,
                                                 # otherwise, Error
        if parts:  # more of the path remains, so insert empty containers
          context[part] = collections.OrderedDict()
          context = context.get(part)
        else:  # e.g. at bottom of path
          context[part] = set_value
      else:
        raise KeyError('Path [{}] not found'.format(item_path))
  return context


def DeleteItemInDict(item, item_path, item_sep='.'):
  """Finds and deletes (potentially) nested value based on specified node_path.

  Args:
      item: Dict, Map like object to search.
      item_path: str, An item_sep separated path to nested item in map.
      item_sep: str, Path item separator, default is '.'.

  Raises:
    KeyError: If item_path not found or empty.
  """
  if not item_path:
    raise KeyError('Missing Path')
  parts = item_path.split(item_sep)
  parts.reverse()
  context = item
  while parts:
    part = parts.pop()
    if part in context and yaml.dict_like(context):
      elem = context.get(part)
      if not parts:
        if elem:
          del context[part]
        else:
          raise KeyError('Path [{}] not found'.format(item_path))
      else:
        context = elem
    else:
      raise KeyError('Path [{}] not found'.format(item_path))


class YamlConfigObject(collections_abc.MutableMapping):
  """Abstraction for managing resource configuration Object.

  Attributes:
    content: YAMLObject, The parsed underlying config data.
  """

  def __init__(self, content):
    self._content = content

  @property
  def content(self):
    return copy.deepcopy(self._content)

  def _FindOrSetItem(self, item_path, item_sep='.', set_value=None):
    """Finds (potentially) nested value based on specified item_path.

    Args:
        item_path: str, An item_sep separated path to nested item in map.
        item_sep: str, Path item separator, default is '.'.
        set_value: object, value to set at item_path. If path is not found
          create a new item at item_path with value of set_value.

    Returns:
        Object, item found in map at item_path or None.
    """
    return FindOrSetItemInDict(self._content, item_path, item_sep, set_value)

  def __str__(self):
    yaml.convert_to_block_text(self._content)
    return yaml.dump(self._content, round_trip=True)

  def __setitem__(self, key, value):
    self._FindOrSetItem(key, set_value=value)

  def __getitem__(self, key):
    return self._FindOrSetItem(key)

  def __delitem__(self, key):
    DeleteItemInDict(self._content, key)

  def __iter__(self):
    return iter(self._content)

  def __len__(self):
    return len(self._content)

  def __contains__(self, key_path):
    try:
      self._FindOrSetItem(key_path)
    except KeyError:
      return False
    return True


class LoginConfigObject(YamlConfigObject):
  """Auth Login Config file abstraction."""

  PREFERRED_AUTH_KEY = 'spec.preferredAuthentication'
  AUTH_PROVIDERS_KEY = 'spec.authentication'
  CLUSTER_NAME_KEY = 'spec.name'

  @property
  def version(self):
    return self[API_VERSION]

  def _FindMatchingAuthMethod(self, method_name, method_type):
    providers = self.GetAuthProviders(name_only=False)
    found = [
        x for x in providers
        if x['name'] == method_name and x[method_type] is not None
    ]
    if found:  # return first matching item
      return found.pop()
    return None

  def IsLdap(self):
    """Returns true is the current preferredAuth Method is ldap."""
    try:
      auth_name = self.GetPreferredAuth()
      found_auth = self._FindMatchingAuthMethod(auth_name, 'ldap')
      if found_auth:
        return True
    except (YamlConfigObjectFieldError, KeyError):
      pass  # Fall through to False return

    return False

  def GetPreferredAuth(self):
    if self.version == AUTH_VERSION_2_ALPHA:
      return self[self.PREFERRED_AUTH_KEY]
    else:
      raise YamlConfigObjectFieldError(self.PREFERRED_AUTH_KEY,
                                       self.__class__.__name__,
                                       'requires config version [{}]'.format(
                                           AUTH_VERSION_2_ALPHA))

  def SetPreferredAuth(self, auth_value):
    if self.version == AUTH_VERSION_2_ALPHA:
      self[self.PREFERRED_AUTH_KEY] = auth_value
    else:
      raise YamlConfigObjectFieldError(self.PREFERRED_AUTH_KEY,
                                       self.__class__.__name__,
                                       'requires config version [{}]'.format(
                                           AUTH_VERSION_2_ALPHA))

  def GetAuthProviders(self, name_only=True):
    try:
      providers = self[self.AUTH_PROVIDERS_KEY]
    except KeyError:
      return None
    if not providers:
      return None
    if name_only:
      return [provider['name'] for provider in providers]
    return providers


class YamlConfigFile(object):
  """Utility class for searching and editing collections of YamlObjects.

  Attributes:
    item_type: class, YamlConfigObject class type of the items in file
    file_contents: str, YAML contents used to load YamlConfigObjects
    file_path: str, file path that YamlConfigObjects were loaded from
    data: [YamlObject], data loaded from file path. Could be 1 or more objects.
    yaml: str, yaml string representation of object.
  """

  def __init__(self, item_type, file_contents=None, file_path=None):
    self._file_contents = file_contents
    self._file_path = file_path
    self._item_type = item_type

    if not self._file_contents and not self._file_path:
      raise YamlConfigFileError('Could Not Initialize YamlConfigFile:'
                                'file_contents And file_path Are Both Empty')
    # Priority is to try to load from contents if specified. Else from file.
    if self._file_contents:
      try:
        items = yaml.load_all(self._file_contents, round_trip=True)
        self._data = [item_type(x) for x in items]
      except yaml.YAMLParseError as fe:
        raise YamlConfigFileError('Error Parsing Config File: [{}]'.format(fe))
    elif self._file_path:
      try:
        items = yaml.load_all_path(self._file_path, round_trip=True)
        self._data = [item_type(x) for x in items]
      except yaml.FileLoadError as fe:
        raise YamlConfigFileError('Error Loading Config File: [{}]'.format(fe))

  @property
  def item_type(self):
    return self._item_type

  @property
  def data(self):
    return self._data

  @property
  def yaml(self):
    if len(self._data) == 1:
      return str(self._data[0])
    return '---\n'.join([str(x) for x in self._data])

  @property
  def file_contents(self):
    return self._file_contents

  @property
  def file_path(self):
    return self._file_path

  def __str__(self):
    return self.yaml

  def __eq__(self, other):
    if isinstance(other, YamlConfigFile):
      return (len(self.data) == len(other.data) and
              all(x == y for x, y in zip(self.data, other.data)))
    return False

  def FindMatchingItem(self, search_path, value):
    """Find all YamlObjects with matching data at search_path."""
    results = []
    for obj in self.data:
      if obj[search_path] == value:
        results.append(obj)
    return results

  def FindMatchingItemData(self, search_path):
    """Find all data in YamlObjects at search_path."""
    results = []
    for obj in self.data:
      value = obj[search_path]
      if value:
        results.append(value)
    return results

  def SetMatchingItemData(self, object_path, object_value,
                          item_path, item_value, persist=True):
    """Find all matching YamlObjects and set values."""
    results = []
    found_items = self.FindMatchingItem(object_path, object_value)
    for ymlconfig in found_items:
      ymlconfig[item_path] = item_value
      results.append(ymlconfig)
    if persist:
      self.WriteToDisk()
    return results

  def WriteToDisk(self):
    """Overwrite Original Yaml File."""
    # Only write if file_path is specified.
    if not self.file_path:
      raise YamlConfigFileError('Could Not Write To Config File: Path Is Empty')
    out_file_buf = io.BytesIO()
    tmp_yaml_buf = io.TextIOWrapper(out_file_buf, newline='\n',
                                    encoding='utf-8')
    yaml.dump_all_round_trip([x.content for x in self.data],
                             stream=tmp_yaml_buf)
    with files.BinaryFileWriter(self.file_path) as f:
      tmp_yaml_buf.seek(0)
      f.write(out_file_buf.getvalue())


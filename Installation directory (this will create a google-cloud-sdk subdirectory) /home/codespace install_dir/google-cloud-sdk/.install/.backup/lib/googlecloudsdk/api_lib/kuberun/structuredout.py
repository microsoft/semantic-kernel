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
"""Helper for JSON-based Kubernetes object wrappers."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


_ROOT_ALIAS_KEY = 'aliases'


class DictWithAliases(dict):
  """A dict intended for serialized results which need computed values.

  DictWithAliases behaves like a dictionary with the exception of containing
  a MakeSerializable hook which excludes the "aliases" key if present in the
  dictionary from being returned. This is to allow additional pieces of data
  to be stored in the object which will not be output via the structured
  --format types for the commands.

  Example:
  d = DictWithAliases({'key': 'value', 'aliases': {'foo': 'bar'}})
  print(d['aliases']['foo']) # prints 'bar'
  d.MakeSeralizable() # returns {'key': 'value'}
  """

  def MakeSerializable(self):
    """Returns the underlying data without the aliases key for serialization."""
    data = self.copy()
    data.pop(_ROOT_ALIAS_KEY, None)
    return data

  def AddAlias(self, key, value):
    self.setdefault(_ROOT_ALIAS_KEY, {})[key] = value


# NOTE: The kuberun surface is generally moving away from using MapObject in
# favor of having commands return dictionaries. In cases where a plain Python
# dictionary can't be used and computed values are needed, the DictWithAliases
# class provides a means to add computed data to a python dictionary which will
# be excluded in the serialized output.
class MapObject(object):
  """Base class to wrap dict-like structures and support attributes for keys."""

  def __init__(self, props):
    self._props = props

  def __eq__(self, o):
    return self._props == o._props

  @property
  def props(self):
    return self._props

  def MakeSerializable(self):
    return self._props

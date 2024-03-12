# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Simple immutable data object."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import six


class _DataType(type):
  """Dumb immutable data type."""

  # TODO(b/154131605): This a type that is an immutable data object. Can't use
  # attrs because it's not part of googlecloudsdk and can't use namedtuple
  # because it's not efficient on python 2 (it generates code, which needs
  # to be parsed and interpretted). Remove this code when we get support
  # for attrs or another dumb data object in gcloud.

  def __new__(cls, classname, bases, class_dict):
    class_dict = class_dict.copy()
    names = class_dict.get('NAMES', tuple())
    class_dict.update(
        (name, cls._CreateAccessor(i)) for i, name in enumerate(names))

    return super(_DataType, cls).__new__(cls, classname, bases, class_dict)

  @staticmethod
  def _CreateAccessor(i):
    """Create an tuple accessor property."""
    return property(lambda tpl: tpl[i])  # pylint: disable=unused-variable


class DataObject(six.with_metaclass(_DataType, tuple)):
  """Parent class of dumb data object."""

  def __new__(cls, **kwargs):
    names = getattr(cls, 'NAMES', tuple())
    invalid_names = set(kwargs) - set(names)
    if invalid_names:
      raise ValueError('Invalid names: ' + repr(invalid_names))

    tpl = tuple(kwargs[name] if name in kwargs else None for name in names)
    return super(DataObject, cls).__new__(cls, tpl)

  def replace(self, **changes):  # pylint: disable=invalid-name
    # https://docs.python.org/3/library/dataclasses.html#dataclasses.replace
    out = dict((n, changes.get(n, getattr(self, n, None))) for n in self.NAMES)
    return self.__class__(**out)

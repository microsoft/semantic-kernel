# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Functions for working with dictionaries representing yaml files."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def GetOrCreate(obj, path, constructor=dict):
  """Get or create the object by following the field names in the path.

  not exist, create the appropriate value.

  Args:
    obj: A dictionary representing a yaml dictionary
    path: A list of strings representing fields to follow.
    constructor: If the object at the end of the path does not exist, create an
      object using the constructor given.

  Returns:
    An object at found by following the path.
  """
  first, rest = path[0], path[1:]

  if rest:
    if first not in obj:
      obj[first] = dict()
    return GetOrCreate(obj[first], rest, constructor)
  else:
    if first not in obj:
      obj[first] = constructor()
    return obj[first]


def GetAll(obj, path):
  """Given a yaml object, yield all objects found by following a path.

  Given a yaml object, read each field in the path and return the object
  found at the end. If a field has a list value, follow the path for each
  object in the list.

  E.g.
  >>> X = {'A': {'B': [{'C': {'D': 1}}, {'C': {'D': 2}}]}}
  >>> sorted(list(GetAll(X, path=('A', 'B', 'C', 'D'))))
  [1, 2]

  Args:
    obj: A dictionary representing a yaml dictionary
    path: A list of strings representing fields to follow.

  Yields:
    Values that are found by following the given path.
  """
  if not path:
    yield obj
    return

  first, rest = path[0], path[1:]
  if first in obj:
    if isinstance(obj[first], dict):
      for extracted_obj in GetAll(obj[first], rest):
        yield extracted_obj
    elif isinstance(obj[first], list):
      for x in obj[first]:
        for extracted_obj in GetAll(x, rest):
          yield extracted_obj
    else:
      if rest:
        raise ValueError(first + ' is not a dictionary or a list')
      else:
        yield obj[first]

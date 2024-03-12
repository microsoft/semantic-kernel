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
"""Functions for formatting debugging output."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def generic_repr(class_instance):
  """Generic debug output for object that lists its property keys and values.

  Use as function:
  x = X()
  generic_repr(x)
  # X(y='hi', z=1)  # ID: 140030868127696

  Use as addition to class:
  class X:
    def __init__(self, y='hi'):
      self.y = y
      self.z = 1

    def __repr__(self):
      return generic_repr(self)
  # X(y='hi', z=1)  # ID: 140030868127696

  Note: Declaring a class by running eval on this repr output will work
  only if all properties are settable in the class's __init__. Nested objects
  may also cause an issue.

  Args:
    class_instance (object): Instance of class to print debug output for.

  Returns:
    Debug output string.
  """
  sorted_attributes = sorted(
      class_instance.__dict__.items(),
      key=lambda key_value_pair: key_value_pair[0])
  return "{class_name}({attributes})  # ID: {id}".format(
      class_name=class_instance.__class__.__name__,
      attributes=", ".join(
          "{}={!r}".format(k, v) for k, v in sorted_attributes),
      id=id(class_instance))

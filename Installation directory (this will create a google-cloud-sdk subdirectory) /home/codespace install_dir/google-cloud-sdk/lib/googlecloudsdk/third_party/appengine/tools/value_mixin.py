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
"""ValueMixin provides comparison and string methods based on fields."""

from __future__ import unicode_literals


class ValueMixin(object):
  """Provides simplistic but often sufficient comparison and string methods."""

  def __eq__(self, other):
    return getattr(other, '__dict__', None) == self.__dict__

  def __ne__(self, other):
    return not self == other

  def __hash__(self):
    return hash(frozenset(list(self.__dict__.items())))

  def __repr__(self):
    """Returns a string representation like `MyClass(foo=23, bar=skidoo)`."""
    d = self.__dict__
    attrs = ['{}={}'.format(key, d[key]) for key in sorted(d)]
    return '{}({})'.format(self.__class__.__name__, ', '.join(attrs))

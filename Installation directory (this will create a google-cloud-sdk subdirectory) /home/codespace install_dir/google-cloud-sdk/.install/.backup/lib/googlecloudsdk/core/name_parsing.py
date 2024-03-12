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
"""Convenience utilities for manipulating collection and resource names."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re


def singularize(collection_name):
  """Convert the input collection name to singular form."""
  ending_plurals = [('cies', 'cy'), ('xies', 'xy'), ('ries', 'ry'),
                    ('xes', 'x'), ('esses', 'ess')]
  singular_collection_name = None
  for plural_suffix, replacement_singular in ending_plurals:
    if collection_name.endswith(plural_suffix):
      singular_collection_name = collection_name.replace(
          plural_suffix, replacement_singular)
  if not singular_collection_name:
    singular_collection_name = collection_name
    if collection_name[-1] == 's':
      singular_collection_name = singular_collection_name[:-1]
  return singular_collection_name


def pluralize(collection_name):
  """Convert the input collection name to singular form."""
  if re.search('[sxz]$', collection_name):
    return re.sub('$', 'es', collection_name)
  elif re.search('[^aeioudgkprt]h$', collection_name):
    return re.sub('$', 'es', collection_name)
  elif re.search('[aeiou]y$', collection_name):
    return re.sub('y$', 'ys', collection_name)
  elif re.search('[crx]y$', collection_name):
    return re.sub('y$', 'ies', collection_name)
  else:
    return collection_name + 's'


def split_name_on_capitals(collection_name, delimiter=' '):
  """Split camel-cased collection names on capital letters."""
  split_with_spaces = delimiter.join(
      re.findall('[a-zA-Z][^A-Z]*', collection_name))
  return split_with_spaces


def convert_collection_name_to_delimited(collection_name,
                                         delimiter=' ',
                                         make_singular=True):
  collection_name_modified = collection_name
  if '.' in collection_name:
    collection_name_modified = collection_name.split('.')[-1]
  if make_singular:
    collection_name_modified = singularize(collection_name_modified)
  return split_name_on_capitals(
      collection_name_modified, delimiter=delimiter).lower()

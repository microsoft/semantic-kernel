# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Various functions intended to be used as an argument type function."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import resources

import six


def Resource(collection, api_version=None):
  """A hook to do basic parsing of a resource in a single flag.

  Args:
    collection: str, The collection the resource is in.
    api_version: str, An optional version to use to parse this resource.

  Returns:
    f(value) -> resource_ref, An argument processing function that returns the
    parsed resource reference.
  """
  collection_info = resources.REGISTRY.GetCollectionInfo(
      collection, api_version=api_version)
  params = collection_info.GetParams('')

  def Parse(value):
    if not value:
      return None
    ref = resources.REGISTRY.Parse(
        value, collection=collection,
        params={k: f for k, f in six.iteritems(arg_utils.DEFAULT_PARAMS)
                if k in params})
    return ref

  return Parse


def LowerCaseType(value):
  return value.lower()

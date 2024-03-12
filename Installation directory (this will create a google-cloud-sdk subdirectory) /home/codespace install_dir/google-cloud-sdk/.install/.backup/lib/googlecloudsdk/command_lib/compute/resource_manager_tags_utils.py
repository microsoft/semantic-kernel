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
"""Code that's shared between multiple org firewall policies subcommands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.resource_manager import tag_utils


def GetResourceManagerTags(resource_manager_tags):
  """Returns a map of resource manager tags, translating namespaced tags if needed.

  Args:
    resource_manager_tags: Map of resource manager tag key value pairs with
      either namespaced name or name.

  Returns:
    Map of resource manager tags with format tagKeys/[0-9]+, tagValues/[0-9]+
  """

  ret_resource_manager_tags = {}
  for key, value in resource_manager_tags.items():
    if not key.startswith('tagKeys/'):
      key = tag_utils.GetNamespacedResource(key, tag_utils.TAG_KEYS).name
    if not value.startswith('tagValues/'):
      value = tag_utils.GetNamespacedResource(value, tag_utils.TAG_VALUES).name
    ret_resource_manager_tags[key] = value

  return ret_resource_manager_tags

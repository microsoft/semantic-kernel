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
"""Wrapper for JSON-based Module status."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import component_status

import six


class ModuleStatus(object):
  """Class that wraps a KubeRun Module Status JSON object."""

  def __init__(self, name, components):
    """Initialize a new ModuleStatus object.

    Args:
      name: the name of the module
      components: a list of ComponentStatus objects
    """
    self.name = name
    self.components = components

  @classmethod
  def FromJSON(cls, name, json_map):
    """Instantiate a new ModuleStatus from JSON.

    Args:
      name: the name of the Module
      json_map: a JSON dict mapping component name to the JSON representation of
        ComponentStatus (see ComponentStatus.FromJSON)

    Returns:
      a ModuleStatus object
    """
    # sort components by name so that the result is stable
    comps = sorted([
        component_status.ComponentStatus.FromJSON(comp_name, json)
        for comp_name, json in json_map['components'].items()
    ],
                   key=lambda c: c.name)
    return cls(name=name, components=comps)

  def __repr__(self):
    # TODO(b/171419038): Create a common base class for these data wrappers
    items = sorted(self.__dict__.items())
    attrs_as_kv_strings = ['{}={!r}'.format(k, v) for (k, v) in items]
    return six.text_type('ModuleStatus({})').format(
        ', '.join(attrs_as_kv_strings))

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.__dict__ == other.__dict__
    return False

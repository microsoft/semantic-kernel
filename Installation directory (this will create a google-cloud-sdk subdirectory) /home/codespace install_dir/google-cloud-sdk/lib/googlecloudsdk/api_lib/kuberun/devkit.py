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
"""Wrapper for JSON-based Development Kit metadata."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import component_template


class DevKit(object):
  """Class that wraps a DevKit JSON object."""

  @classmethod
  def FromJSON(cls, json_object):
    components = [component_template.ComponentTemplate.FromJSON(x) for x in
                  json_object.get('components', [])]
    return cls(
        id_=json_object['id'],
        name=json_object['name'],
        version=json_object['version'],
        description=json_object['description'],
        components=components)

  def __init__(self, id_=None, name=None, version=None, description=None,
               components=None):
    self._id = id_
    self._name = name
    self._version = version
    self._description = description
    if components is None:
      components = []
    self._components = components

  @property
  def id(self):
    return self._id

  @property
  def name(self):
    return self._name

  @property
  def version(self):
    return self._version

  @property
  def description(self):
    return self._description

  @property
  def components(self):
    return self._components

  def __repr__(self):
    return ('<DevKit: id="{0.id}" name="{0.name}" version="{0.version}" '
            'description="{0.description}">').format(self)

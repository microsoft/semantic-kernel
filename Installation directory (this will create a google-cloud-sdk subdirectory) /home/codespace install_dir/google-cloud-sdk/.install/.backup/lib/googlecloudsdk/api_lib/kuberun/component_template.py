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


class ComponentTemplate:
  """Class that wraps a ComponentTemplate JSON object."""

  def __init__(self, name, event_input, description):
    self.name = name
    self.event_input = event_input
    self.description = description

  @classmethod
  def FromJSON(cls, json_object):
    return cls(
        name=json_object['name'],
        event_input=json_object['event-input'],
        description=json_object['description'])

  def __repr__(self):
    return ('<ComponentTemplate: name="{0.name}" event_input="{0.event_input}" '
            'description="{0.description}">').format(self)

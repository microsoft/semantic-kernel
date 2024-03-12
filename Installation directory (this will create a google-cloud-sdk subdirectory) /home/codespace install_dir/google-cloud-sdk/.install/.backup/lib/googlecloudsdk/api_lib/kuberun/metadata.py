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
"""Wrapper for JSON-based Kubernetes object's metadata."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import structuredout


class Metadata(structuredout.MapObject):
  """Wraps the metadata fields of Kubernetes objects."""

  @property
  def labels(self):
    return self._props.get('labels', dict())

  @property
  def creationTimestamp(self):
    return self._props['creationTimestamp']

  @property
  def annotations(self):
    return self._props.get('annotations', dict())

  @property
  def namespace(self):
    return self._props['namespace']

  @property
  def name(self):
    return self._props['name']

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
"""Wrapper for JSON-based Kubernetes object's status."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import structuredout
from googlecloudsdk.command_lib.kuberun import kubernetes_consts as k8s


class Status(structuredout.MapObject):
  """Wraps the status field of a Kubernetes object."""

  @property
  def conditions(self):
    return [Condition(x) for x in self._props[k8s.FIELD_CONDITIONS]]

  @property
  def latestReadyRevisionName(self):
    return self._props.get(k8s.FIELD_LATEST_READY_REVISION_NAME)

  @property
  def latestCreatedRevisionName(self):
    return self._props.get(k8s.FIELD_LATEST_CREATED_REVISION_NAME)

  @property
  def url(self):
    return self._props.get('url')


class Condition(structuredout.MapObject):
  """Wraps the condition field of a Kubernetes Status object."""

  @property
  def status(self):
    if self._props[k8s.FIELD_STATUS].lower() == 'true':
      return True
    elif self._props[k8s.FIELD_STATUS].lower() == 'false':
      return False
    else:
      return None

  @property
  def type(self):
    return self._props[k8s.FIELD_TYPE]

  @property
  def message(self):
    return self._props.get(k8s.FIELD_MESSAGE)

  @property
  def lastTransitionTime(self):
    return self._props.get(k8s.FIELD_LAST_TRANSITION_TIME)

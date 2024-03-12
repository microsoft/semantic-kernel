# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Wraps a Cloud Run Route message, making fields more convenient to access."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import k8s_object


class Route(k8s_object.KubernetesObject):
  """Wraps a Cloud Run Route message, making fields more convenient to access.

  Setting properties on a Route (where possible) writes through to the nested
  Kubernetes-style fields.
  """

  API_CATEGORY = 'serving.knative.dev'
  KIND = 'Route'

  @property
  def traffic(self):
    return self._m.spec.traffic

  @traffic.setter
  def traffic(self, value):
    self._m.spec.traffic = value

  @property
  def domain(self):
    return self._m.status.url or self._m.status.domain

  @property
  def active_revisions(self):
    """Return the revisions whose traffic target is positive."""
    revisions = {}
    for traffic_target in self._m.status.traffic:
      if traffic_target.percent:
        revisions[traffic_target.revisionName] = traffic_target.percent
    return revisions


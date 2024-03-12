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
"""JSON-based Knative service wrapper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import kubernetesobject
from googlecloudsdk.api_lib.kuberun import revision
from googlecloudsdk.api_lib.kuberun import traffic

SERVICE_LABEL = 'serving.knative.dev/service'
# Used to force a new revision, and also to tie a particular request for changes
# to a particular created revision.
NONCE_LABEL = 'client.knative.dev/nonce'
# Annotation for the user-specified image.
USER_IMAGE_ANNOTATION = kubernetesobject.CLIENT_GROUP + '/user-image'

ENDPOINT_VISIBILITY = 'serving.knative.dev/visibility'
CLUSTER_LOCAL = 'cluster-local'

INGRESS_ALL = 'all'
INGRESS_INTERNAL = 'internal'


class Service(kubernetesobject.KubernetesObject):
  """Class that wraps JSON-based dict object of a Knative service."""

  @property
  def url(self):
    return self.status.url

  @property
  def latest_created_revision(self):
    return self.status.latestCreatedRevisionName

  @property
  def latest_ready_revision(self):
    return self.status.latestReadyRevisionName

  @property
  def template(self):
    return revision.Revision(self._props['spec']['template'])

  @property
  def spec_traffic(self):
    if 'traffic' in self._props['spec']:
      return {
          traffic.GetKey(tt): [tt] for tt in (
              traffic.TrafficTarget(x) for x in self._props['spec']['traffic'])
      }
    else:
      return dict()

  @property
  def status_traffic(self):
    if 'traffic' in self._props['status']:
      return {
          traffic.GetKey(tt): [tt]
          for tt in (traffic.TrafficTarget(x)
                     for x in self._props['status']['traffic'])
      }
    else:
      return dict()

  def ReadySymbolAndColor(self):
    if (self.ready is False and  # pylint: disable=g-bool-id-comparison
        self.latest_ready_revision
        and self.latest_created_revision != self.latest_ready_revision):
      return '!', 'yellow'
    return super(Service, self).ReadySymbolAndColor()

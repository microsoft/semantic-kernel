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
"""Wraps a Serverless Service message, making fields more convenient."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import revision
from googlecloudsdk.api_lib.run import traffic


ENDPOINT_VISIBILITY = 'networking.knative.dev/visibility'
CLUSTER_LOCAL = 'cluster-local'

INGRESS_ANNOTATION = 'run.googleapis.com/ingress'
INGRESS_STATUS_ANNOTATION = 'run.googleapis.com/ingress-status'
INGRESS_ALL = 'all'
INGRESS_INTERNAL = 'internal'
INGRESS_INTERNAL_AND_CLOUD_LOAD_BALANCING = 'internal-and-cloud-load-balancing'

SERVICE_MIN_SCALE_ANNOTATION = 'run.googleapis.com/minScale'
OPERATION_ID_ANNOTATION = 'run.googleapis.com/operation-id'


class Service(k8s_object.KubernetesObject):
  """Wraps a Serverless Service message, making fields more convenient.

  Setting properties on a Service (where possible) writes through to the
  nested Kubernetes-style fields.
  """
  API_CATEGORY = 'serving.knative.dev'
  KIND = 'Service'

  @property
  def template(self):
    if not self.spec.template.metadata:
      self.spec.template.metadata = k8s_object.MakeMeta(self.MessagesModule())
    ret = revision.Revision.Template(self.spec.template, self.MessagesModule())
    return ret

  @property
  def template_annotations(self):
    self.AssertFullObject()
    return k8s_object.AnnotationsFromMetadata(
        self._messages, self.template.metadata)

  @property
  def revision_labels(self):
    return self.template.labels

  @property
  def revision_name(self):
    return self.template.name

  @revision_name.setter
  def revision_name(self, value):
    self.template.name = value

  @property
  def latest_created_revision(self):
    return self.status.latestCreatedRevisionName

  @property
  def latest_ready_revision(self):
    return self.status.latestReadyRevisionName

  @property
  def serving_revisions(self):
    return [t.revisionName for t in self.status.traffic if t.percent]

  def _ShouldIncludeInLatestPercent(self, target):
    """Returns True if the target's percent is part of the latest percent."""
    is_latest_by_name = (
        self.status.latestReadyRevisionName and
        target.revisionName == self.status.latestReadyRevisionName)
    return target.latestRevision or is_latest_by_name

  @property
  def latest_percent_traffic(self):
    """The percent of traffic the latest ready revision is serving."""
    return sum(
        target.percent or 0
        for target in self.status.traffic
        if self._ShouldIncludeInLatestPercent(target))

  @property
  def latest_url(self):
    """A url at which we can reach the latest ready revision."""
    for target in self.status.traffic:
      if self._ShouldIncludeInLatestPercent(target) and target.url:
        return target.url
    return None

  @property
  def domain(self):
    if self._m.status.url:
      return self._m.status.url
    try:
      return self._m.status.domain
    except AttributeError:
      # `domain` field only exists in v1alpha1 so this could be thrown if using
      # another api version
      return None

  @domain.setter
  def domain(self, domain):
    self._m.status.url = domain
    try:
      self._m.status.domain = domain
    except AttributeError:
      # `domain` field only exists in v1alpha1 so this could be thrown if using
      # another api version
      return None

  def ReadySymbolAndColor(self):
    if (self.ready is False and  # pylint: disable=g-bool-id-comparison
        self.latest_ready_revision and
        self.latest_created_revision != self.latest_ready_revision):
      return '!', 'yellow'
    return super(Service, self).ReadySymbolAndColor()

  @property
  def last_modifier(self):
    return self.annotations.get(u'serving.knative.dev/lastModifier')

  @property
  def spec_traffic(self):
    self.AssertFullObject()
    return traffic.TrafficTargets(self._messages, self.spec.traffic)

  @property
  def status_traffic(self):
    self.AssertFullObject()
    return traffic.TrafficTargets(
        self._messages, [] if self.status is None else self.status.traffic)

  @property
  def vpc_connector(self):
    return self.annotations.get(u'run.googleapis.com/vpc-access-connector')

  @property
  def image(self):
    return self.template.image

  @image.setter
  def image(self, value):
    self.template.image = value

  @property
  def operation_id(self):
    return self.annotations.get(OPERATION_ID_ANNOTATION)

  @operation_id.setter
  def operation_id(self, value):
    self.annotations[OPERATION_ID_ANNOTATION] = value

  @property
  def description(self):
    return self.annotations.get(k8s_object.DESCRIPTION_ANNOTATION)

  @description.setter
  def description(self, value):
    self.annotations[u'run.googleapis.com/description'] = value

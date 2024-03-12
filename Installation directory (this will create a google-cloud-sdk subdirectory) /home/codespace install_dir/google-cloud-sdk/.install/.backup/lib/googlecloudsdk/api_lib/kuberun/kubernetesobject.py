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
"""JSON-based Kubernetes object wrappers."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


from googlecloudsdk.api_lib.kuberun import metadata
from googlecloudsdk.api_lib.kuberun import status
from googlecloudsdk.api_lib.kuberun import structuredout
from googlecloudsdk.core.console import console_attr

LAST_MODIFIER_ANNOTATION = 'serving.knative.dev/lastModifier'

SERVING_GROUP = 'serving.knative.dev'
AUTOSCALING_GROUP = 'autoscaling.knative.dev'
EVENTING_GROUP = 'eventing.knative.dev'
CLIENT_GROUP = 'client.knative.dev'

GOOGLE_GROUP = 'cloud.googleapis.com'

INTERNAL_GROUPS = (
    CLIENT_GROUP, SERVING_GROUP, AUTOSCALING_GROUP, EVENTING_GROUP,
    GOOGLE_GROUP)


class KubernetesObject(structuredout.MapObject):
  """Common base class for wrapping K8s JSON objects."""

  def Kind(self):
    return self._props['kind']

  @property
  def name(self):
    return self.metadata.name

  @property
  def labels(self):
    return self.metadata.labels

  @property
  def annotations(self):
    return self.metadata.annotations

  @property
  def metadata(self):
    return metadata.Metadata(self._props['metadata'])

  @property
  def namespace(self):
    return self.metadata.namespace

  @property
  def status(self):
    return status.Status(self._props['status'])

  @property
  def ready_condition(self):
    ready_cond = [x for x in self.status.conditions if x.type == 'Ready']
    if ready_cond:
      return ready_cond[0]
    else:
      return None

  @property
  def ready(self):
    if self.ready_condition:
      return self.ready_condition.status
    else:
      return None

  @property
  def ready_symbol(self):
    return self.ReadySymbolAndColor()[0]

  @property
  def self_link(self):
    return self.metadata.selfLink.lstrip('/')

  @property
  def last_transition_time(self):
    if self.ready_condition:
      return self.ready_condition.lastTransitionTime
    else:
      return None

  @property
  def last_modifier(self):
    return self.metadata.annotations.get(LAST_MODIFIER_ANNOTATION)

  def ReadySymbolAndColor(self):
    """Return a tuple of ready_symbol and display color for this object."""
    # NB: This can be overridden by subclasses to allow symbols for more
    # complex reasons the object isn't ready. Ex: Service overrides it to
    # provide '!' for "I'm serving, but not the revision you wanted."
    encoding = console_attr.GetConsoleAttr().GetEncoding()
    if self.ready is None:
      return self._PickSymbol(
          '\N{HORIZONTAL ELLIPSIS}', '.', encoding), 'yellow'
    elif self.ready:
      return self._PickSymbol('\N{HEAVY CHECK MARK}', '+', encoding), 'green'
    else:
      return 'X', 'red'

  def _PickSymbol(self, best, alt, encoding):
    """Choose the best symbol (if it's in this encoding) or an alternate."""
    try:
      best.encode(encoding)
      return best
    except UnicodeError:
      return alt

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
"""Wraps a Cloud Run revision message with convenience methods."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import container_resource
from googlecloudsdk.api_lib.run import k8s_object

# Label names as to be stored in k8s object metadata
SERVICE_LABEL = 'serving.knative.dev/service'
# Used to force a new revision, and also to tie a particular request for changes
# to a particular created revision.
NONCE_LABEL = 'client.knative.dev/nonce'
MIN_SCALE_ANNOTATION = 'autoscaling.knative.dev/minScale'
MAX_SCALE_ANNOTATION = 'autoscaling.knative.dev/maxScale'
# gcloud-disable-gdu-domain
SESSION_AFFINITY_ANNOTATION = 'run.googleapis.com/sessionAffinity'
# gcloud-disable-gdu-domain
MESH_ANNOTATION = 'run.googleapis.com/mesh'
# gcloud-disable-gdu-domain
BASE_IMAGES_ANNOTATION = 'run.googleapis.com/base-images'
# gcloud-disable-gdu-domain
BASE_IMAGE_UPDATE_RUNTIME_CLASS_NAME = (
    'run.googleapis.com/linux-base-image-update'
)


class Revision(container_resource.ContainerResource):
  """Wraps a Cloud Run Revision message, making fields more convenient."""

  API_CATEGORY = 'serving.knative.dev'
  KIND = 'Revision'
  READY_CONDITION = 'Ready'
  _ACTIVE_CONDITION = 'Active'
  TERMINAL_CONDITIONS = frozenset([
      READY_CONDITION,
  ])

  @property
  def gcs_location(self):
    return self._m.status.gcs.location

  @property
  def service_name(self):
    return self.labels[SERVICE_LABEL]

  @property
  def serving_state(self):
    return self.spec.servingState

  @property
  def active(self):
    cond = self.conditions
    if self._ACTIVE_CONDITION in cond:
      return cond[self._ACTIVE_CONDITION]['status']
    return None

  @property
  def concurrency(self):
    """The concurrency number in the revisionTemplate.

    0: Multiple concurrency, max unspecified.
    1: Single concurrency
    n>1: Allow n simultaneous requests per instance.
    """
    return self.spec.containerConcurrency

  @concurrency.setter
  def concurrency(self, value):
    # Clear the old, deperecated string field
    try:
      self.spec.concurrencyModel = None
    except AttributeError:
      # This field only exists in the v1alpha1 spec, if we're working with a
      # different version, this is safe to ignore
      pass
    self.spec.containerConcurrency = value

  @property
  def timeout(self):
    """The timeout number in the revisionTemplate.

    The lib can accept either a duration format like '1m20s' or integer like
    '80' to set the timeout. The returned object is an integer value, which
    assumes second the unit, e.g., 80.
    """
    return self.spec.timeoutSeconds

  @timeout.setter
  def timeout(self, value):
    self.spec.timeoutSeconds = value

  @property
  def service_account(self):
    """The service account in the revisionTemplate."""
    return self.spec.serviceAccountName

  @service_account.setter
  def service_account(self, value):
    self.spec.serviceAccountName = value

  @property
  def image_digest(self):
    """The URL of the image, by digest. Stable when tags are not."""
    return self.status.imageDigest

  def _EnsureNodeSelector(self):
    if self.spec.nodeSelector is None:
      self.spec.nodeSelector = k8s_object.InitializedInstance(
          self._messages.RevisionSpec.NodeSelectorValue
      )

  @property
  def node_selector(self):
    """The node selector as a dictionary { accelerator_type: value}."""
    self._EnsureNodeSelector()
    return k8s_object.KeyValueListAsDictionaryWrapper(
        self.spec.nodeSelector.additionalProperties,
        self._messages.RevisionSpec.NodeSelectorValue.AdditionalProperty,
        key_field='key',
        value_field='value',
    )

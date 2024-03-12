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
"""Wraps a Cloud Run Configuration message, making fields more convenient."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.api_lib.run import revision


class Configuration(k8s_object.KubernetesObject):
  """Wraps a Cloud Run Configuration message, making fields more convenient.

  Setting properties on a Configuration (where possible) writes through to the
  nested Kubernetes-style fields.
  """
  API_CATEGORY = 'serving.knative.dev'
  KIND = 'Configuration'

  @property
  def template(self):
    if not self.spec.template.metadata:
      self.spec.template.metadata = k8s_object.MakeMeta(self.MessagesModule())
    return revision.Revision.Template(self.spec.template, self.MessagesModule())

  @property
  def image(self):
    return self.template.image

  @property
  def container(self):
    return revision.Revision.Template(
        self.template, self.MessagesModule()).container

  @property
  def env_vars(self):
    return self.template.env_vars

  @property
  def resource_limits(self):
    return self.template.resource_limits

  @property
  def concurrency(self):
    return self.template.concurrency

  @property
  def timeout(self):
    return self.template.timeout

  @property
  def service_account(self):
    return self.template.service_account

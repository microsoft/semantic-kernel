# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Wraps a Cloud Run Job message with convenience methods."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import execution
from googlecloudsdk.api_lib.run import k8s_object

AUTHOR_ANNOTATION = k8s_object.RUN_GROUP + '/creator'

NONCE_LABEL = k8s_object.CLIENT_GROUP + '/nonce'


class Job(k8s_object.KubernetesObject):
  """Wraps a Cloud Run job message, making fields more convenient."""

  API_CATEGORY = 'run.googleapis.com'
  KIND = 'Job'

  @property
  def execution_template(self):
    return execution.Execution.Template(self.spec.template,
                                        self.MessagesModule())

  @property
  def task_template(self):
    return self.template

  @property
  def template(self):
    return self.execution_template.template

  @property
  def author(self):
    return self.annotations.get(AUTHOR_ANNOTATION)

  @property
  def image(self):
    return self.template.image

  @image.setter
  def image(self, value):
    self.template.image = value

  @property
  def parallelism(self):
    return self.execution_template.spec.parallelism

  @parallelism.setter
  def parallelism(self, value):
    self.execution_template.spec.parallelism = value

  @property
  def task_count(self):
    return self.execution_template.spec.taskCount

  @task_count.setter
  def task_count(self, value):
    self.execution_template.spec.taskCount = value

  @property
  def max_retries(self):
    return self.task_template.spec.maxRetries

  @max_retries.setter
  def max_retries(self, value):
    self.task_template.spec.maxRetries = value

  @property
  def last_modifier(self):
    return self.annotations.get(u'run.googleapis.com/lastModifier')

  @property
  def last_modified_timestamp(self):
    return self.labels.get(u'run.googleapis.com/lastUpdatedTime')

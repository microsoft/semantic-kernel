# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Utilities for dealing with ML models API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class NoFieldsSpecifiedError(exceptions.Error):
  """Error indicating that no updates were requested in a Patch operation."""


def _ParseModel(model_id):
  return resources.REGISTRY.Parse(
      model_id,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection='ml.projects.models')


class ModelsClient(object):
  """High-level client for the ML models surface."""

  def __init__(self, client=None, messages=None):
    self.client = client or apis.GetClientInstance('ml', 'v1')
    self.messages = messages or self.client.MESSAGES_MODULE

  def Create(self, model_name, regions, enable_logging=False,
             enable_console_logging=False, labels=None, description=None):
    """Create a new model."""
    model_ref = _ParseModel(model_name)
    regions_list = regions or []
    project_ref = resources.REGISTRY.Parse(model_ref.projectsId,
                                           collection='ml.projects')
    req = self.messages.MlProjectsModelsCreateRequest(
        parent=project_ref.RelativeName(),
        googleCloudMlV1Model=self.messages.GoogleCloudMlV1Model(
            name=model_ref.Name(),
            regions=regions_list,
            onlinePredictionLogging=enable_logging,
            onlinePredictionConsoleLogging=enable_console_logging,
            description=description,
            labels=labels))
    return self.client.projects_models.Create(req)

  def GetIamPolicy(self, model_ref):
    return self.client.projects_models.GetIamPolicy(
        self.messages.MlProjectsModelsGetIamPolicyRequest(
            resource=model_ref.RelativeName()))

  def SetIamPolicy(self, model_ref, policy, update_mask):
    request = self.messages.GoogleIamV1SetIamPolicyRequest(
        policy=policy,
        updateMask=update_mask)
    return self.client.projects_models.SetIamPolicy(
        self.messages.MlProjectsModelsSetIamPolicyRequest(
            googleIamV1SetIamPolicyRequest=request,
            resource=model_ref.RelativeName()))

  def Delete(self, model):
    """Delete an existing model."""
    model_ref = _ParseModel(model)
    req = self.messages.MlProjectsModelsDeleteRequest(
        name=model_ref.RelativeName())
    return self.client.projects_models.Delete(req)

  def Get(self, model):
    """Get details about a model."""
    model_ref = _ParseModel(model)
    req = self.messages.MlProjectsModelsGetRequest(
        name=model_ref.RelativeName())
    return self.client.projects_models.Get(req)

  def List(self, project_ref):
    """List models in the project."""
    req = self.messages.MlProjectsModelsListRequest(
        parent=project_ref.RelativeName())
    return list_pager.YieldFromList(
        self.client.projects_models,
        req,
        field='models',
        batch_size_attribute='pageSize')

  def Patch(self, model_ref, labels_update, description=None):
    """Update a model."""
    model = self.messages.GoogleCloudMlV1Model()
    update_mask = []
    if labels_update.needs_update:
      model.labels = labels_update.labels
      update_mask.append('labels')

    if description:
      model.description = description
      update_mask.append('description')

    if not update_mask:
      raise NoFieldsSpecifiedError('No updates requested.')

    req = self.messages.MlProjectsModelsPatchRequest(
        name=model_ref.RelativeName(),
        googleCloudMlV1Model=model,
        updateMask=','.join(update_mask))
    return self.client.projects_models.Patch(req)

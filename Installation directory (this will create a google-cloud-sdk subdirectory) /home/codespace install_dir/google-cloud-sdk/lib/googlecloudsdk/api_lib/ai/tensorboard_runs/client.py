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
"""Utilities for AI Platform Tensorboard runs API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import common_args
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.util.args import labels_util


class TensorboardRunsClient(object):
  """High-level client for the AI Platform Tensorboard run surface."""

  def __init__(self,
               client=None,
               messages=None,
               version=constants.BETA_VERSION):
    self.client = client or apis.GetClientInstance(
        constants.AI_PLATFORM_API_NAME,
        constants.AI_PLATFORM_API_VERSION[version])
    self.messages = messages or self.client.MESSAGES_MODULE
    self._service = self.client.projects_locations_tensorboards_experiments_runs
    self._version = version

  def Create(self, tensorboard_exp_ref, args):
    return self.CreateBeta(tensorboard_exp_ref, args)

  def CreateBeta(self, tensorboard_exp_ref, args):
    """Create a new Tensorboard run."""
    labels = labels_util.ParseCreateArgs(
        args,
        self.messages.GoogleCloudAiplatformV1beta1TensorboardRun.LabelsValue)
    request = self.messages.AiplatformProjectsLocationsTensorboardsExperimentsRunsCreateRequest(
        parent=tensorboard_exp_ref.RelativeName(),
        googleCloudAiplatformV1beta1TensorboardRun=self.messages
        .GoogleCloudAiplatformV1beta1TensorboardRun(
            displayName=args.display_name,
            description=args.description,
            labels=labels),
        tensorboardRunId=args.tensorboard_run_id)
    return self._service.Create(request)

  def List(self, tensorboard_exp_ref, limit=1000, page_size=50, sort_by=None):
    request = self.messages.AiplatformProjectsLocationsTensorboardsExperimentsRunsListRequest(
        parent=tensorboard_exp_ref.RelativeName(),
        orderBy=common_args.ParseSortByArg(sort_by))
    return list_pager.YieldFromList(
        self._service,
        request,
        field='tensorboardRuns',
        batch_size_attribute='pageSize',
        batch_size=page_size,
        limit=limit)

  def Get(self, tensorboard_run_ref):
    request = self.messages.AiplatformProjectsLocationsTensorboardsExperimentsRunsGetRequest(
        name=tensorboard_run_ref.RelativeName())
    return self._service.Get(request)

  def Delete(self, tensorboard_run_ref):
    request = (
        self.messages
        .AiplatformProjectsLocationsTensorboardsExperimentsRunsDeleteRequest(
            name=tensorboard_run_ref.RelativeName()))
    return self._service.Delete(request)

  def Patch(self, tensorboard_run_ref, args):
    return self.PatchBeta(tensorboard_run_ref, args)

  def PatchBeta(self, tensorboard_run_ref, args):
    """Update a Tensorboard run."""
    tensorboard_run = self.messages.GoogleCloudAiplatformV1beta1TensorboardRun()
    update_mask = []

    def GetLabels():
      return self.Get(tensorboard_run_ref).labels

    labels_update = labels_util.ProcessUpdateArgsLazy(
        args,
        self.messages.GoogleCloudAiplatformV1beta1TensorboardRun.LabelsValue,
        GetLabels)
    if labels_update.needs_update:
      tensorboard_run.labels = labels_update.labels
      update_mask.append('labels')

    if args.display_name is not None:
      tensorboard_run.displayName = args.display_name
      update_mask.append('display_name')

    if args.description is not None:
      tensorboard_run.description = args.description
      update_mask.append('description')

    if not update_mask:
      raise errors.NoFieldsSpecifiedError('No updates requested.')

    request = self.messages.AiplatformProjectsLocationsTensorboardsExperimentsRunsPatchRequest(
        name=tensorboard_run_ref.RelativeName(),
        googleCloudAiplatformV1beta1TensorboardRun=tensorboard_run,
        updateMask=','.join(update_mask))
    return self._service.Patch(request)

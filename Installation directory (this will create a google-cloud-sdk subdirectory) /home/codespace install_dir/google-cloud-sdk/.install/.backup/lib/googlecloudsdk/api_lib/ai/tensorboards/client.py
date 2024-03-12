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
"""Utilities for AI Platform Tensorboards API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.ai import util as api_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import common_args
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.ai import validation as common_validation
from googlecloudsdk.command_lib.util.args import labels_util


class TensorboardsClient(object):
  """High-level client for the AI Platform Tensorboard surface."""

  def __init__(self,
               client=None,
               messages=None,
               version=constants.BETA_VERSION):
    self.client = client or apis.GetClientInstance(
        constants.AI_PLATFORM_API_NAME,
        constants.AI_PLATFORM_API_VERSION[version])
    self.messages = messages or self.client.MESSAGES_MODULE
    self._service = self.client.projects_locations_tensorboards
    self._version = version

  def Create(self, location_ref, args):
    if self._version == constants.GA_VERSION:
      return self.CreateGa(location_ref, args)
    else:
      return self.CreateBeta(location_ref, args)

  def CreateGa(self, location_ref, args):
    """Create a new Tensorboard."""
    kms_key_name = common_validation.GetAndValidateKmsKey(args)
    labels = labels_util.ParseCreateArgs(
        args, self.messages.GoogleCloudAiplatformV1Tensorboard.LabelsValue)
    tensorboard = self.messages.GoogleCloudAiplatformV1Tensorboard(
        displayName=args.display_name,
        description=args.description,
        labels=labels)
    if kms_key_name is not None:
      tensorboard.encryptionSpec = api_util.GetMessage(
          'EncryptionSpec', self._version)(
              kmsKeyName=kms_key_name)

    request = self.messages.AiplatformProjectsLocationsTensorboardsCreateRequest(
        parent=location_ref.RelativeName(),
        googleCloudAiplatformV1Tensorboard=tensorboard)

    return self._service.Create(request)

  def CreateBeta(self, location_ref, args):
    """Create a new Tensorboard."""
    kms_key_name = common_validation.GetAndValidateKmsKey(args)
    labels = labels_util.ParseCreateArgs(
        args, self.messages.GoogleCloudAiplatformV1beta1Tensorboard.LabelsValue)
    tensorboard = self.messages.GoogleCloudAiplatformV1beta1Tensorboard(
        displayName=args.display_name,
        description=args.description,
        labels=labels)
    if kms_key_name is not None:
      tensorboard.encryptionSpec = api_util.GetMessage(
          'EncryptionSpec', self._version)(
              kmsKeyName=kms_key_name)

    request = self.messages.AiplatformProjectsLocationsTensorboardsCreateRequest(
        parent=location_ref.RelativeName(),
        googleCloudAiplatformV1beta1Tensorboard=tensorboard)

    return self._service.Create(request)

  def Get(self, tensorboard_ref):
    request = self.messages.AiplatformProjectsLocationsTensorboardsGetRequest(
        name=tensorboard_ref.RelativeName())
    return self._service.Get(request)

  def List(self, limit=1000, page_size=50, region_ref=None, sort_by=None):
    request = self.messages.AiplatformProjectsLocationsTensorboardsListRequest(
        parent=region_ref.RelativeName(),
        orderBy=common_args.ParseSortByArg(sort_by))
    return list_pager.YieldFromList(
        self._service,
        request,
        field='tensorboards',
        batch_size_attribute='pageSize',
        batch_size=page_size,
        limit=limit)

  def Delete(self, tensorboard_ref):
    request = self.messages.AiplatformProjectsLocationsTensorboardsDeleteRequest(
        name=tensorboard_ref.RelativeName())
    return self._service.Delete(request)

  def Patch(self, tensorboard_ref, args):
    """Update a Tensorboard."""
    if self._version == constants.GA_VERSION:
      tensorboard = self.messages.GoogleCloudAiplatformV1Tensorboard()
      labels_value = self.messages.GoogleCloudAiplatformV1Tensorboard.LabelsValue
    else:
      tensorboard = self.messages.GoogleCloudAiplatformV1beta1Tensorboard()
      labels_value = self.messages.GoogleCloudAiplatformV1beta1Tensorboard.LabelsValue

    update_mask = []

    def GetLabels():
      return self.Get(tensorboard_ref).labels

    labels_update = labels_util.ProcessUpdateArgsLazy(args, labels_value,
                                                      GetLabels)

    if labels_update.needs_update:
      tensorboard.labels = labels_update.labels
      update_mask.append('labels')

    if args.display_name is not None:
      tensorboard.displayName = args.display_name
      update_mask.append('display_name')

    if args.description is not None:
      tensorboard.description = args.description
      update_mask.append('description')

    if not update_mask:
      raise errors.NoFieldsSpecifiedError('No updates requested.')

    if self._version == constants.GA_VERSION:
      req = self.messages.AiplatformProjectsLocationsTensorboardsPatchRequest(
          name=tensorboard_ref.RelativeName(),
          googleCloudAiplatformV1Tensorboard=tensorboard,
          updateMask=','.join(update_mask))
    else:
      req = self.messages.AiplatformProjectsLocationsTensorboardsPatchRequest(
          name=tensorboard_ref.RelativeName(),
          googleCloudAiplatformV1beta1Tensorboard=tensorboard,
          updateMask=','.join(update_mask))
    return self._service.Patch(req)

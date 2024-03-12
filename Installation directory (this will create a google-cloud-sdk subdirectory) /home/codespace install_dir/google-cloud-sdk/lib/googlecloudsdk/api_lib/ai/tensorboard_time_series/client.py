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
"""Utilities for AI Platform Tensorboard time series API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import common_args
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import errors


def GetMessagesModule(version=constants.BETA_VERSION):
  return apis.GetMessagesModule(constants.AI_PLATFORM_API_NAME,
                                constants.AI_PLATFORM_API_VERSION[version])


class TensorboardTimeSeriesClient(object):
  """High-level client for the AI Platform Tensorboard time series surface."""

  def __init__(self,
               client=None,
               messages=None,
               version=constants.BETA_VERSION):
    self.client = client or apis.GetClientInstance(
        constants.AI_PLATFORM_API_NAME,
        constants.AI_PLATFORM_API_VERSION[version])
    self.messages = messages or self.client.MESSAGES_MODULE
    self._service = self.client.projects_locations_tensorboards_experiments_runs_timeSeries
    self._version = version

  def Create(self, tensorboard_run_ref, args):
    return self.CreateBeta(tensorboard_run_ref, args)

  def CreateBeta(self, tensorboard_run_ref, args):
    """Create a new Tensorboard time series."""
    if args.type == 'scalar':
      value_type = (
          self.messages.GoogleCloudAiplatformV1beta1TensorboardTimeSeries
          .ValueTypeValueValuesEnum.SCALAR)
    elif args.type == 'blob-sequence':
      value_type = (
          self.messages.GoogleCloudAiplatformV1beta1TensorboardTimeSeries
          .ValueTypeValueValuesEnum.BLOB_SEQUENCE)
    else:
      value_type = (
          self.messages.GoogleCloudAiplatformV1beta1TensorboardTimeSeries
          .ValueTypeValueValuesEnum.TENSOR)

    if args.plugin_data is None:
      plugin_data = ''
    else:
      plugin_data = args.plugin_data

    request = self.messages.AiplatformProjectsLocationsTensorboardsExperimentsRunsTimeSeriesCreateRequest(
        parent=tensorboard_run_ref.RelativeName(),
        googleCloudAiplatformV1beta1TensorboardTimeSeries=self.messages
        .GoogleCloudAiplatformV1beta1TensorboardTimeSeries(
            displayName=args.display_name,
            description=args.description,
            valueType=value_type,
            pluginName=args.plugin_name,
            pluginData=bytes(plugin_data, encoding='utf8')))
    return self._service.Create(request)

  def List(self, tensorboard_run_ref, limit=1000, page_size=50, sort_by=None):
    request = self.messages.AiplatformProjectsLocationsTensorboardsExperimentsRunsTimeSeriesListRequest(
        parent=tensorboard_run_ref.RelativeName(),
        orderBy=common_args.ParseSortByArg(sort_by))
    return list_pager.YieldFromList(
        self._service,
        request,
        field='tensorboardTimeSeries',
        batch_size_attribute='pageSize',
        batch_size=page_size,
        limit=limit)

  def Get(self, tensorboard_time_series_ref):
    request = self.messages.AiplatformProjectsLocationsTensorboardsExperimentsRunsTimeSeriesGetRequest(
        name=tensorboard_time_series_ref.RelativeName())
    return self._service.Get(request)

  def Delete(self, tensorboard_time_series_ref):
    request = self.messages.AiplatformProjectsLocationsTensorboardsExperimentsRunsTimeSeriesDeleteRequest(
        name=tensorboard_time_series_ref.RelativeName())
    return self._service.Delete(request)

  def Patch(self, tensorboard_time_series_ref, args):
    return self.PatchBeta(tensorboard_time_series_ref, args)

  def PatchBeta(self, tensorboard_time_series_ref, args):
    """Update a Tensorboard time series."""
    tensorboard_time_series = (
        self.messages.GoogleCloudAiplatformV1beta1TensorboardTimeSeries())
    update_mask = []

    if args.display_name is not None:
      tensorboard_time_series.displayName = args.display_name
      update_mask.append('display_name')

    if args.description is not None:
      tensorboard_time_series.description = args.description
      update_mask.append('description')

    if args.plugin_name is not None:
      tensorboard_time_series.pluginName = args.plugin_name
      update_mask.append('plugin_name')

    if args.plugin_data is not None:
      tensorboard_time_series.pluginData = bytes(
          args.plugin_data, encoding='utf8')
      update_mask.append('plugin_data')

    if not update_mask:
      raise errors.NoFieldsSpecifiedError('No updates requested.')

    request = self.messages.AiplatformProjectsLocationsTensorboardsExperimentsRunsTimeSeriesPatchRequest(
        name=tensorboard_time_series_ref.RelativeName(),
        googleCloudAiplatformV1beta1TensorboardTimeSeries=tensorboard_time_series,
        updateMask=','.join(update_mask))
    return self._service.Patch(request)

  def Read(self, tensorboard_time_series_ref, max_data_points, data_filter):
    request = self.messages.AiplatformProjectsLocationsTensorboardsExperimentsRunsTimeSeriesReadRequest(
        tensorboardTimeSeries=tensorboard_time_series_ref.RelativeName(),
        maxDataPoints=max_data_points,
        filter=data_filter)
    return self._service.Read(request)

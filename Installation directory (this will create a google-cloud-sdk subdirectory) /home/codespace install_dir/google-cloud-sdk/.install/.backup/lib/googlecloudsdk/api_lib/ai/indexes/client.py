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
"""Utilities for dealing with AI Platform indexes API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import extra_types
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import yaml


class IndexesClient(object):
  """High-level client for the AI Platform indexes surface."""

  def __init__(self, client=None, messages=None, version=None):
    self.client = client or apis.GetClientInstance(
        constants.AI_PLATFORM_API_NAME,
        constants.AI_PLATFORM_API_VERSION[version])
    self.messages = messages or self.client.MESSAGES_MODULE
    self._service = self.client.projects_locations_indexes

  def _ReadIndexMetadata(self, metadata_file):
    """Parse json metadata file."""
    if not metadata_file:
      raise gcloud_exceptions.BadArgumentException(
          '--metadata-file', 'Index metadata file must be specified.')
    index_metadata = None
    # Yaml is a superset of json, so parse json file as yaml.
    data = yaml.load_path(metadata_file)
    if data:
      index_metadata = messages_util.DictToMessageWithErrorCheck(
          data, extra_types.JsonValue)
    return index_metadata

  def Get(self, index_ref):
    request = self.messages.AiplatformProjectsLocationsIndexesGetRequest(
        name=index_ref.RelativeName())
    return self._service.Get(request)

  def List(self, limit=None, region_ref=None):
    return list_pager.YieldFromList(
        self._service,
        self.messages.AiplatformProjectsLocationsIndexesListRequest(
            parent=region_ref.RelativeName()),
        field='indexes',
        batch_size_attribute='pageSize',
        limit=limit)

  def CreateBeta(self, location_ref, args):
    """Create a new index."""
    labels = labels_util.ParseCreateArgs(
        args, self.messages.GoogleCloudAiplatformV1beta1Index.LabelsValue)

    index_update_method = None
    if args.index_update_method:
      if args.index_update_method == 'stream_update':
        index_update_method = (
            self.messages.GoogleCloudAiplatformV1beta1Index.
            IndexUpdateMethodValueValuesEnum.STREAM_UPDATE)
      else:
        index_update_method = (
            self.messages.GoogleCloudAiplatformV1beta1Index.
            IndexUpdateMethodValueValuesEnum.BATCH_UPDATE)

    encryption_spec = None
    if args.encryption_kms_key_name is not None:
      encryption_spec = (
          self.messages.GoogleCloudAiplatformV1beta1EncryptionSpec(
              kmsKeyName=args.encryption_kms_key_name))

    req = self.messages.AiplatformProjectsLocationsIndexesCreateRequest(
        parent=location_ref.RelativeName(),
        googleCloudAiplatformV1beta1Index=self.messages
        .GoogleCloudAiplatformV1beta1Index(
            displayName=args.display_name,
            description=args.description,
            metadata=self._ReadIndexMetadata(args.metadata_file),
            labels=labels,
            indexUpdateMethod=index_update_method,
            encryptionSpec=encryption_spec
            ))
    return self._service.Create(req)

  def Create(self, location_ref, args):
    """Create a new v1 index."""
    labels = labels_util.ParseCreateArgs(
        args, self.messages.GoogleCloudAiplatformV1Index.LabelsValue)

    index_update_method = None
    if args.index_update_method:
      if args.index_update_method == 'stream_update':
        index_update_method = (
            self.messages.GoogleCloudAiplatformV1Index
            .IndexUpdateMethodValueValuesEnum.STREAM_UPDATE)
      else:
        index_update_method = (
            self.messages.GoogleCloudAiplatformV1Index
            .IndexUpdateMethodValueValuesEnum.BATCH_UPDATE
        )

    encryption_spec = None
    if args.encryption_kms_key_name is not None:
      encryption_spec = (
          self.messages.GoogleCloudAiplatformV1EncryptionSpec(
              kmsKeyName=args.encryption_kms_key_name))

    req = self.messages.AiplatformProjectsLocationsIndexesCreateRequest(
        parent=location_ref.RelativeName(),
        googleCloudAiplatformV1Index=self.messages.GoogleCloudAiplatformV1Index(
            displayName=args.display_name,
            description=args.description,
            metadata=self._ReadIndexMetadata(args.metadata_file),
            labels=labels,
            indexUpdateMethod=index_update_method,
            encryptionSpec=encryption_spec
            ))
    return self._service.Create(req)

  def PatchBeta(self, index_ref, args):
    """Update an index."""
    index = self.messages.GoogleCloudAiplatformV1beta1Index()
    update_mask = []

    if args.metadata_file is not None:
      index.metadata = self._ReadIndexMetadata(args.metadata_file)
      update_mask.append('metadata')
    else:
      if args.display_name is not None:
        index.displayName = args.display_name
        update_mask.append('display_name')

      if args.description is not None:
        index.description = args.description
        update_mask.append('description')

      def GetLabels():
        return self.Get(index_ref).labels

      labels_update = labels_util.ProcessUpdateArgsLazy(
          args, self.messages.GoogleCloudAiplatformV1beta1Index.LabelsValue,
          GetLabels)
      if labels_update.needs_update:
        index.labels = labels_update.labels
        update_mask.append('labels')

    if not update_mask:
      raise errors.NoFieldsSpecifiedError('No updates requested.')

    request = self.messages.AiplatformProjectsLocationsIndexesPatchRequest(
        name=index_ref.RelativeName(),
        googleCloudAiplatformV1beta1Index=index,
        updateMask=','.join(update_mask))
    return self._service.Patch(request)

  def Patch(self, index_ref, args):
    """Update an v1 index."""
    index = self.messages.GoogleCloudAiplatformV1Index()
    update_mask = []

    if args.metadata_file is not None:
      index.metadata = self._ReadIndexMetadata(args.metadata_file)
      update_mask.append('metadata')
    else:
      if args.display_name is not None:
        index.displayName = args.display_name
        update_mask.append('display_name')

      if args.description is not None:
        index.description = args.description
        update_mask.append('description')

      def GetLabels():
        return self.Get(index_ref).labels

      labels_update = labels_util.ProcessUpdateArgsLazy(
          args, self.messages.GoogleCloudAiplatformV1Index.LabelsValue,
          GetLabels)
      if labels_update.needs_update:
        index.labels = labels_update.labels
        update_mask.append('labels')

    if not update_mask:
      raise errors.NoFieldsSpecifiedError('No updates requested.')

    request = self.messages.AiplatformProjectsLocationsIndexesPatchRequest(
        name=index_ref.RelativeName(),
        googleCloudAiplatformV1Index=index,
        updateMask=','.join(update_mask))
    return self._service.Patch(request)

  def Delete(self, index_ref):
    request = self.messages.AiplatformProjectsLocationsIndexesDeleteRequest(
        name=index_ref.RelativeName())
    return self._service.Delete(request)

  def RemoveDatapointsBeta(self, index_ref, args):
    """Remove data points from a v1beta1 index."""
    if args.datapoint_ids and args.datapoints_from_file:
      raise errors.ArgumentError(
          'datapoint_ids and datapoints_from_file can not be set'
          ' at the same time.'
      )

    if args.datapoint_ids:
      req = self.messages.AiplatformProjectsLocationsIndexesRemoveDatapointsRequest(
          index=index_ref.RelativeName(),
          googleCloudAiplatformV1beta1RemoveDatapointsRequest=self.messages
          .GoogleCloudAiplatformV1beta1RemoveDatapointsRequest(
              datapointIds=args.datapoint_ids))
    if args.datapoints_from_file:
      data = yaml.load_path(args.datapoints_from_file)
      req = self.messages.AiplatformProjectsLocationsIndexesRemoveDatapointsRequest(
          index=index_ref.RelativeName(),
          googleCloudAiplatformV1beta1RemoveDatapointsRequest=self.messages
          .GoogleCloudAiplatformV1beta1RemoveDatapointsRequest(
              datapointIds=data))
    return self._service.RemoveDatapoints(req)

  def RemoveDatapoints(self, index_ref, args):
    """Remove data points from a v1 index."""
    if args.datapoint_ids and args.datapoints_from_file:
      raise errors.ArgumentError(
          '`--datapoint_ids` and `--datapoints_from_file` can not be set at the'
          ' same time.'
      )

    if args.datapoint_ids:
      req = self.messages.AiplatformProjectsLocationsIndexesRemoveDatapointsRequest(
          index=index_ref.RelativeName(),
          googleCloudAiplatformV1RemoveDatapointsRequest=self.messages
          .GoogleCloudAiplatformV1RemoveDatapointsRequest(
              datapointIds=args.datapoint_ids))
    if args.datapoints_from_file:
      data = yaml.load_path(args.datapoints_from_file)
      req = self.messages.AiplatformProjectsLocationsIndexesRemoveDatapointsRequest(
          index=index_ref.RelativeName(),
          googleCloudAiplatformV1RemoveDatapointsRequest=self.messages
          .GoogleCloudAiplatformV1RemoveDatapointsRequest(
              datapointIds=data))
    return self._service.RemoveDatapoints(req)

  def UpsertDatapointsBeta(self, index_ref, args):
    """Upsert data points from a v1beta1 index."""
    datapoints = []
    if args.datapoints_from_file:
      data = yaml.load_path(args.datapoints_from_file)
      for datapoint_json in data:
        datapoint = messages_util.DictToMessageWithErrorCheck(
            datapoint_json,
            self.messages.GoogleCloudAiplatformV1beta1IndexDatapoint)
        datapoints.append(datapoint)
    update_mask = None
    if args.update_mask:
      update_mask = ','.join(args.update_mask)

    req = self.messages.AiplatformProjectsLocationsIndexesUpsertDatapointsRequest(
        index=index_ref.RelativeName(),
        googleCloudAiplatformV1beta1UpsertDatapointsRequest=self.messages
        .GoogleCloudAiplatformV1beta1UpsertDatapointsRequest(
            datapoints=datapoints,
            updateMask=update_mask))
    return self._service.UpsertDatapoints(req)

  def UpsertDatapoints(self, index_ref, args):
    """Upsert data points from a v1 index."""
    datapoints = []
    if args.datapoints_from_file:
      data = yaml.load_path(args.datapoints_from_file)
      for datapoint_json in data:
        datapoint = messages_util.DictToMessageWithErrorCheck(
            datapoint_json,
            self.messages.GoogleCloudAiplatformV1IndexDatapoint)
        datapoints.append(datapoint)
    update_mask = None
    if args.update_mask:
      update_mask = ','.join(args.update_mask)

    req = self.messages.AiplatformProjectsLocationsIndexesUpsertDatapointsRequest(
        index=index_ref.RelativeName(),
        googleCloudAiplatformV1UpsertDatapointsRequest=self.messages
        .GoogleCloudAiplatformV1UpsertDatapointsRequest(
            datapoints=datapoints,
            updateMask=update_mask))
    return self._service.UpsertDatapoints(req)

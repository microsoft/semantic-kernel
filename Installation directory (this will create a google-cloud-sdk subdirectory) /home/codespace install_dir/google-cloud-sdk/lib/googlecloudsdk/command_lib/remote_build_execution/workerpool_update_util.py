# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Utilities for remotebuildexecution update command."""

# Disable linting for line-too-long since the API path itself is too long.
# pylint: disable=line-too-long

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util


def RemoveDockerRootDiskConfig(ref, args, request):
  del ref
  if args.IsSpecified('clear_docker_root_disk_config'):
    if request.googleDevtoolsRemotebuildexecutionAdminV1alphaUpdateWorkerPoolRequest.workerPool.workerConfig.attachedDisks is not None:
      request.googleDevtoolsRemotebuildexecutionAdminV1alphaUpdateWorkerPoolRequest.workerPool.workerConfig.attachedDisks.dockerRootDisk = None
    req = request.googleDevtoolsRemotebuildexecutionAdminV1alphaUpdateWorkerPoolRequest
    AddFieldToMask('workerConfig.attachedDisks.dockerRootDisk.sourceImage', req)
    AddFieldToMask('workerConfig.attachedDisks.dockerRootDisk.diskType', req)
    AddFieldToMask('workerConfig.attachedDisks.dockerRootDisk.diskSizeGb', req)
  return request


def RemoveAcceleratorConfig(ref, args, request):
  del ref
  if args.IsSpecified('clear_accelerator_config'):
    request.googleDevtoolsRemotebuildexecutionAdminV1alphaUpdateWorkerPoolRequest.workerPool.workerConfig.accelerator = None
    req = request.googleDevtoolsRemotebuildexecutionAdminV1alphaUpdateWorkerPoolRequest
    AddFieldToMask('workerConfig.accelerator.acceleratorCount', req)
    AddFieldToMask('workerConfig.accelerator.acceleratorType', req)
  return request


def RemoveAutoscale(ref, args, request):
  del ref
  if args.IsSpecified('clear_autoscale'):
    request.googleDevtoolsRemotebuildexecutionAdminV1alphaUpdateWorkerPoolRequest.workerPool.autoscale = None
    req = request.googleDevtoolsRemotebuildexecutionAdminV1alphaUpdateWorkerPoolRequest
    AddFieldToMask('autoscale.min_size', req)
    AddFieldToMask('autoscale.max_size', req)
  return request


def AddLabelsFlags():
  remove_group = base.ArgumentGroup(mutex=True)
  remove_group.AddArgument(labels_util.GetClearLabelsFlag())
  remove_group.AddArgument(labels_util.GetRemoveLabelsFlag(''))
  return [labels_util.GetUpdateLabelsFlag(''), remove_group]


def UpdateLabels(ref, args, request):
  """Update Labels."""
  del ref
  req = request.googleDevtoolsRemotebuildexecutionAdminV1alphaUpdateWorkerPoolRequest

  labels = {}
  additions = args.update_labels or {}
  subtractions = args.remove_labels or []
  clear = args.clear_labels

  if clear:
    req = AddFieldToMask('workerConfig.labels', req)
  else:
    AddLabelKeysToMask(additions, req)
    AddLabelKeysToMask(subtractions, req)

  if additions:
    labels = additions

  for key in subtractions:
    labels.pop(key, None)

  arg_utils.SetFieldInMessage(req, 'workerPool.workerConfig.labels', labels)
  return request


def AddLabelKeysToMask(labels, request):
  for key in labels:
    request = AddFieldToMask('workerConfig.labels.' + key, request)
  return request


def AddFieldToMask(field, request):
  if request.updateMask:
    if field not in request.updateMask:
      request.updateMask = request.updateMask + ',' + field
  else:
    request.updateMask = field
  return request

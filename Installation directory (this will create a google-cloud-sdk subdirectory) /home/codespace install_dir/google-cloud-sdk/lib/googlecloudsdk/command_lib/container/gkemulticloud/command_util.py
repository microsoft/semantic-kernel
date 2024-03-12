# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utilities for all CRUD commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.container import util as gke_util
from googlecloudsdk.api_lib.container.gkemulticloud import operations as op_api_util
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


def _GetOperationResource(op):
  return resources.REGISTRY.ParseRelativeName(
      op.name, collection='gkemulticloud.projects.locations.operations'
  )


def _GetOperationTarget(op):
  op_cluster = ''
  if op.metadata is not None:
    metadata = encoding.MessageToPyValue(op.metadata)
    if 'target' in metadata:
      op_cluster = metadata['target']
  return resources.REGISTRY.ParseRelativeName(
      op_cluster, collection='gkemulticloud.projects.locations.attachedClusters'
  )


def _LogAndWaitForOperation(op, async_, message):
  op_ref = _GetOperationResource(op)
  log.CreatedResource(op_ref, kind=constants.LRO_KIND)
  if not async_:
    op_client = op_api_util.OperationsClient()
    op_client.Wait(op_ref, message)


def ClusterMessage(name, action=None, kind=None, region=None):
  msg = 'cluster [{name}]'.format(name=name)
  if action:
    msg = '{action} '.format(action=action) + msg
  if kind and region:
    msg += ' in {kind} region [{region}]'.format(kind=kind, region=region)
  return msg


def NodePoolMessage(name, action=None, cluster=None, kind=None, region=None):
  msg = 'node pool [{name}]'.format(name=name)
  if action:
    msg = '{action} '.format(action=action) + msg
  if cluster:
    msg += ' in cluster [{cluster}]'.format(cluster=cluster)
  if kind and region:
    msg += ' in {kind} region [{region}]'.format(kind=kind, region=region)
  return msg


def ClientMessage(name, action=None, region=None):
  msg = 'client [{name}]'.format(name=name)
  if action:
    msg = '{action} '.format(action=action) + msg
  if region:
    msg += ' in [{region}]'.format(region=region)
  return msg


def Create(
    resource_ref=None, resource_client=None, args=None, kind=None, message=None
):
  """Runs a create command for gkemulticloud.

  Args:
    resource_ref: obj, resource reference.
    resource_client: obj, client for the resource.
    args: obj, arguments parsed from the command.
    kind: str, the kind of resource e.g. AWS Cluster, Azure Node Pool.
    message: str, message to display while waiting for LRO to complete.

  Returns:
    The details of the created resource.
  """
  op = resource_client.Create(resource_ref, args)
  validate_only = getattr(args, 'validate_only', False)
  if validate_only:
    args.format = 'disable'
    return
  async_ = getattr(args, 'async_', False)
  _LogAndWaitForOperation(op, async_, message)
  log.CreatedResource(resource_ref, kind=kind, is_async=async_)
  return resource_client.Get(resource_ref)


def Update(
    resource_ref=None, resource_client=None, args=None, kind=None, message=None
):
  """Runs an update command for gkemulticloud.

  Args:
    resource_ref: obj, resource reference.
    resource_client: obj, client for the resource.
    args: obj, arguments parsed from the command.
    kind: str, the kind of resource e.g. AWS Cluster, Azure Node Pool.
    message: str, message to display while waiting for LRO to complete.

  Returns:
    The details of the updated resource.
  """
  op = resource_client.Update(resource_ref, args)
  validate_only = getattr(args, 'validate_only', False)
  if validate_only:
    args.format = 'disable'
    return
  async_ = getattr(args, 'async_', False)
  _LogAndWaitForOperation(op, async_, message)
  log.UpdatedResource(resource_ref, kind=kind, is_async=async_)
  return resource_client.Get(resource_ref)


def _DeletePrompt(kind, items):
  """Generates a delete prompt for a resource."""
  title = 'The following {} will be deleted.'
  if (
      kind == constants.AWS_CLUSTER_KIND
      or kind == constants.AZURE_CLUSTER_KIND
      or kind == constants.ATTACHED_CLUSTER_KIND
  ):
    title = title.format('clusters')
  elif (
      kind == constants.AWS_NODEPOOL_KIND
      or kind == constants.AZURE_NODEPOOL_KIND
  ):
    title = title.format('node pool')
  elif kind == constants.AZURE_CLIENT_KIND:
    title = title.format('client')
  console_io.PromptContinue(
      message=gke_util.ConstructList(title, items),
      throw_if_unattended=True,
      cancel_on_no=True,
  )


def Delete(
    resource_ref=None, resource_client=None, args=None, kind=None, message=None
):
  """Runs a delete command for gkemulticloud.

  Args:
    resource_ref: obj, resource reference.
    resource_client: obj, client for the resource.
    args: obj, arguments parsed from the command.
    kind: str, the kind of resource e.g. AWS Cluster, Azure Node Pool.
    message: str, message to display while waiting for LRO to complete.

  Returns:
    The details of the updated resource.
  """
  validate_only = getattr(args, 'validate_only', False)
  if not validate_only:
    _DeletePrompt(kind, [message])
  async_ = getattr(args, 'async_', False)
  allow_missing = getattr(args, 'allow_missing', False)
  ignore_errors = getattr(args, 'ignore_errors', False)
  op = resource_client.Delete(
      resource_ref,
      validate_only=validate_only,
      allow_missing=allow_missing,
      ignore_errors=ignore_errors,
  )
  if validate_only:
    args.format = 'disable'
    return
  _LogAndWaitForOperation(op, async_, 'Deleting ' + message)
  log.DeletedResource(resource_ref, kind=kind, is_async=async_)


def CancelOperationMessage(name, kind):
  """Message to display after cancelling an LRO operation.

  Args:
    name: str, name of the operation.
    kind: str, the kind of LRO operation e.g. AWS or Azure.

  Returns:
    The operation cancellation message.
  """
  msg = (
      'Cancelation of operation {0} has been requested. '
      'Please use gcloud container {1} operations describe {2} to '
      'check if the operation has been cancelled successfully.'
  )
  return msg.format(name, kind, name)


def CancelOperationPrompt(op_name):
  """Prompt the user before cancelling an LRO operation.

  Args:
    op_name: str, name of the operation.
  """
  message = 'The operation {0} will be cancelled.'
  console_io.PromptContinue(
      message=message.format(op_name),
      throw_if_unattended=True,
      cancel_on_no=True,
  )


def Import(
    location_ref=None,
    resource_client=None,
    fleet_membership_ref=None,
    args=None,
    kind=None,
    message=None,
):
  """Runs an import command for gkemulticloud.

  Args:
    location_ref: obj, location reference.
    resource_client: obj, client for the resource.
    fleet_membership_ref: obj, fleet membership reference.
    args: obj, arguments parsed from the command.
    kind: str, the kind of resource e.g. AWS Cluster, Azure Node Pool.
    message: str, message to display while waiting for LRO to complete.

  Returns:
    The details of the imported resource.
  """
  op = resource_client.Import(
      location_ref=location_ref,
      fleet_membership_ref=fleet_membership_ref,
      args=args,
  )
  validate_only = getattr(args, 'validate_only', False)
  if validate_only:
    args.format = 'disable'
    return
  async_ = getattr(args, 'async_', False)
  _LogAndWaitForOperation(op, async_, message)
  op_target = _GetOperationTarget(op)
  log.ImportResource(op_target, kind=kind, is_async=async_)


def _RollbackPrompt(items):
  """Generates a rollback prompt for the node pool resource."""
  title = 'The following node pool will be rolled back.'
  console_io.PromptContinue(
      message=gke_util.ConstructList(title, items),
      throw_if_unattended=True,
      cancel_on_no=True,
  )


def Rollback(
    resource_ref=None, resource_client=None, args=None, kind=None, message=None
):
  """Runs a rollback command for gkemulticloud.

  Args:
    resource_ref: obj, resource reference.
    resource_client: obj, client for the resource.
    args: obj, arguments parsed from the command.
    kind: str, the kind of resource e.g. AWS Cluster, Azure Node Pool.
    message: str, message to display while waiting for LRO to complete.

  Returns:
    The details of the updated resource.
  """
  _RollbackPrompt([message])
  async_ = getattr(args, 'async_', False)
  op = resource_client.Rollback(resource_ref, args)
  _LogAndWaitForOperation(op, async_, 'Rolling back ' + message)
  log.UpdatedResource(resource_ref, kind=kind, is_async=async_)
  return resource_client.Get(resource_ref)

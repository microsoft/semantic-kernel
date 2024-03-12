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
"""Utilities for the cloud deploy rollout resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.clouddeploy import client_util
from googlecloudsdk.api_lib.clouddeploy import release
from googlecloudsdk.api_lib.clouddeploy import rollout
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.deploy import exceptions as cd_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

_ROLLOUT_COLLECTION = (
    'clouddeploy.projects.locations.deliveryPipelines.releases.rollouts'
)
PENDING_APPROVAL_FILTER_TEMPLATE = (
    'approvalState="NEEDS_APPROVAL" AND '
    'state="PENDING_APPROVAL" AND targetId="{}"'
)
DEPLOYED_ROLLOUT_FILTER_TEMPLATE = (
    '(approvalState!="REJECTED" AND '
    'approvalState!="NEEDS_APPROVAL") AND state="SUCCEEDED" AND targetId="{}"'
)
ROLLOUT_IN_TARGET_FILTER_TEMPLATE = 'targetId="{}"'
ROLLOUT_ID_TEMPLATE = '{}-to-{}-{:04d}'
WILDCARD_RELEASE_NAME_TEMPLATE = '{}/releases/-'
SUCCEED_ROLLOUT_ORDERBY = 'DeployEndTime desc'
PENDING_ROLLOUT_ORDERBY = 'CreateTime desc'
ENQUEUETIME_ROLLOUT_ORDERBY = 'EnqueueTime desc'


def RolloutReferenceFromName(rollout_name):
  """Returns a rollout reference object from a rollout message.

  Args:
    rollout_name: str, full canonical resource name of the rollout

  Returns:
    Rollout reference object
  """
  return resources.REGISTRY.ParseRelativeName(
      rollout_name, collection=_ROLLOUT_COLLECTION
  )


def RolloutId(rollout_name_or_id):
  """Returns rollout ID.

  Args:
    rollout_name_or_id: str, rollout full name or ID.

  Returns:
    Rollout ID.
  """
  rollout_id = rollout_name_or_id
  if 'projects/' in rollout_name_or_id:
    rollout_id = resources.REGISTRY.ParseRelativeName(
        rollout_name_or_id, collection=_ROLLOUT_COLLECTION
    ).Name()

  return rollout_id


def ListPendingRollouts(target_ref, pipeline_ref):
  """Lists the rollouts in PENDING_APPROVAL state for the releases associated with the specified target.

  The rollouts must be approvalState=NEEDS_APPROVAL and
  state=PENDING_APPROVAL. The returned list is sorted by rollout's create
  time.

  Args:
    target_ref: protorpc.messages.Message, target object.
    pipeline_ref: protorpc.messages.Message, pipeline object.

  Returns:
    a sorted list of rollouts.
  """
  filter_str = PENDING_APPROVAL_FILTER_TEMPLATE.format(target_ref.Name())
  parent = WILDCARD_RELEASE_NAME_TEMPLATE.format(pipeline_ref.RelativeName())

  return rollout.RolloutClient().List(
      release_name=parent,
      filter_str=filter_str,
      order_by=PENDING_ROLLOUT_ORDERBY,
  )


def GetFilteredRollouts(
    target_ref, pipeline_ref, filter_str, order_by, page_size=None, limit=None
):
  """Gets successfully deployed rollouts for the releases associated with the specified target and index.

  Args:
    target_ref: protorpc.messages.Message, target object.
    pipeline_ref: protorpc.messages.Message, pipeline object.
    filter_str: Filter string to use when listing rollouts.
    order_by: order_by field to use when listing rollouts.
    page_size: int, the maximum number of objects to return per page.
    limit: int, the maximum number of `Rollout` objects to return.

  Returns:
    a rollout object or None if no rollouts in the target.
  """
  parent = WILDCARD_RELEASE_NAME_TEMPLATE.format(pipeline_ref.RelativeName())

  return rollout.RolloutClient().List(
      release_name=parent,
      filter_str=filter_str.format(target_ref.Name()),
      order_by=order_by,
      page_size=page_size,
      limit=limit,
  )


def GenerateRolloutId(to_target, release_ref):
  filter_str = ROLLOUT_IN_TARGET_FILTER_TEMPLATE.format(to_target)
  try:
    rollouts = rollout.RolloutClient().List(
        release_ref.RelativeName(), filter_str
    )
    return ComputeRolloutID(release_ref.Name(), to_target, rollouts)
  except apitools_exceptions.HttpError:
    raise cd_exceptions.ListRolloutsError(release_ref.RelativeName())


def CreateRollout(
    release_ref,
    to_target,
    rollout_id=None,
    annotations=None,
    labels=None,
    description=None,
    starting_phase_id=None,
    override_deploy_policies=None,
):
  """Creates a rollout by calling the rollout create API and waits for the operation to finish.

  Args:
    release_ref: protorpc.messages.Message, release resource object.
    to_target: str, the target to create create the rollout in.
    rollout_id: str, rollout ID.
    annotations: dict[str,str], a dict of annotation (key,value) pairs that
      allow clients to store small amounts of arbitrary data in cloud deploy
      resources.
    labels: dict[str,str], a dict of label (key,value) pairs that can be used to
      select cloud deploy resources and to find collections of cloud deploy
      resources that satisfy certain conditions.
    description: str, rollout description.
    starting_phase_id: str, rollout starting phase.
    override_deploy_policies: List of Deploy Policies to override.

  Raises:
      ListRolloutsError: an error occurred calling rollout list API.

  Returns:
    The rollout resource created.
  """
  final_rollout_id = rollout_id
  if not final_rollout_id:
    final_rollout_id = GenerateRolloutId(to_target, release_ref)

  resource_dict = release_ref.AsDict()
  rollout_ref = resources.REGISTRY.Parse(
      final_rollout_id,
      collection=_ROLLOUT_COLLECTION,
      params={
          'projectsId': resource_dict.get('projectsId'),
          'locationsId': resource_dict.get('locationsId'),
          'deliveryPipelinesId': resource_dict.get('deliveryPipelinesId'),
          'releasesId': release_ref.Name(),
      },
  )
  rollout_obj = client_util.GetMessagesModule().Rollout(
      name=rollout_ref.RelativeName(),
      targetId=to_target,
      description=description,
  )

  log.status.Print(
      'Creating rollout {} in target {}'.format(
          rollout_ref.RelativeName(), to_target
      )
  )
  operation = rollout.RolloutClient().Create(
      rollout_ref,
      rollout_obj,
      annotations,
      labels,
      starting_phase_id,
      override_deploy_policies,
  )
  operation_ref = resources.REGISTRY.ParseRelativeName(
      operation.name, collection='clouddeploy.projects.locations.operations'
  )

  client_util.OperationsClient().WaitForOperation(
      operation,
      operation_ref,
      'Waiting for rollout creation operation to complete',
  )
  return rollout.RolloutClient().Get(rollout_ref.RelativeName())


def GetValidRollBackCandidate(target_ref, pipeline_ref):
  """Gets the currently deployed release and the next valid release that can be rolled back to.

  Args:
    target_ref: protorpc.messages.Message, target resource object.
    pipeline_ref: protorpc.messages.Message, pipeline resource object.

  Raises:
      HttpException: an error occurred fetching a resource.

  Returns:
    An list containg the currently deployed release and the next valid
    deployable release.
  """
  iterable = GetFilteredRollouts(
      target_ref=target_ref,
      pipeline_ref=pipeline_ref,
      filter_str=DEPLOYED_ROLLOUT_FILTER_TEMPLATE,
      order_by=SUCCEED_ROLLOUT_ORDERBY,
      limit=None,
      page_size=10,
  )
  rollouts = []
  for rollout_obj in iterable:
    if not rollouts:  # Currently deployed rollout in target
      rollouts.append(rollout_obj)
    elif not _RolloutIsFromAbandonedRelease(rollout_obj):
      rollouts.append(rollout_obj)
    if len(rollouts) >= 2:
      break
  return rollouts


def _RolloutIsFromAbandonedRelease(rollout_obj):
  rollout_ref = RolloutReferenceFromName(rollout_obj.name)
  release_ref = rollout_ref.Parent()
  try:
    release_obj = release.ReleaseClient().Get(release_ref.RelativeName())
  except apitools_exceptions.HttpError as error:
    raise exceptions.HttpException(error)
  return release_obj.abandoned


def ComputeRolloutID(release_id, target_id, rollouts):
  """Generates a rollout ID.

  Args:
    release_id: str, release ID.
    target_id: str, target ID.
    rollouts: [apitools.base.protorpclite.messages.Message], list of rollout
      messages.

  Returns:
    rollout ID.

  Raises:
    googlecloudsdk.command_lib.deploy.exceptions.RolloutIdExhaustedError: if
    there are more than 1000 rollouts with auto-generated ID.
  """
  rollout_ids = {RolloutId(r.name) for r in rollouts}
  for i in range(1, 1001):
    # If the rollout ID is too long, the resource will fail to be created.
    # It is up to the user to mitigate this by passing an explicit rollout ID
    # to use, instead.
    rollout_id = ROLLOUT_ID_TEMPLATE.format(release_id, target_id, i)
    if rollout_id not in rollout_ids:
      return rollout_id

  raise cd_exceptions.RolloutIDExhaustedError(release_id)

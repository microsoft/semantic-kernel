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
"""Utilities for the promote operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.clouddeploy import rollout
from googlecloudsdk.command_lib.deploy import exceptions
from googlecloudsdk.command_lib.deploy import release_util
from googlecloudsdk.command_lib.deploy import rollout_util
from googlecloudsdk.command_lib.deploy import target_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

_LAST_TARGET_IN_SEQUENCE = (
    'Release {} is already deployed to the last target '
    '({}) in the promotion sequence.\n- Release: {}\n- Target: {}\n'
)
# In progress List filter
IN_PROGRESS_FILTER_TEMPLATE = 'state="IN_PROGRESS"'


def Promote(
    release_ref,
    release_obj,
    to_target,
    is_create,
    rollout_id=None,
    annotations=None,
    labels=None,
    description=None,
    starting_phase_id=None,
    override_deploy_policies=None,
):
  """Creates a rollout for the given release in the destination target.

  If to_target is not specified and there is a rollout in progress, the promote
  will fail. Otherwise this computes the destination target based on the
  promotion sequence.

  Args:
    release_ref: protorpc.messages.Message, release resource object.
    release_obj: apitools.base.protorpclite.messages.Message, release message
      object.
    to_target: str, the target to promote the release to.
    is_create: bool, if creates a rollout during release creation.
    rollout_id: str, ID to assign to the generated rollout.
    annotations: dict[str,str], a dict of annotation (key,value) pairs that
      allow clients to store small amounts of arbitrary data in cloud deploy
      resources.
    labels: dict[str,str], a dict of label (key,value) pairs that can be used to
      select cloud deploy resources and to find collections of cloud deploy
      resources that satisfy certain conditions.
    description: str, rollout description.
    starting_phase_id: str, the starting phase for the rollout.
    override_deploy_policies: List of Deploy Policies to override.

  Raises:
    googlecloudsdk.command_lib.deploy.exceptions.RolloutIdExhausted
    googlecloudsdk.command_lib.deploy.exceptions.ReleaseInactiveError
  Returns:
    The rollout resource created.
  """
  dest_target = to_target
  if not dest_target:
    dest_target = GetToTargetID(release_obj, is_create)

  rollout_resource = rollout_util.CreateRollout(
      release_ref,
      dest_target,
      rollout_id,
      annotations,
      labels,
      description,
      starting_phase_id,
      override_deploy_policies,
  )

  # Check if it requires approval.
  target_obj = release_util.GetSnappedTarget(release_obj, dest_target)
  if target_obj and target_obj.requireApproval:
    log.status.Print('The rollout is pending approval.')

  return rollout_resource


def GetToTargetID(release_obj, is_create):
  """Get the to_target parameter for promote API.

  This checks the promotion sequence to get the next stage to promote the
  release to.

  Args:
    release_obj: apitools.base.protorpclite.messages.Message, release message.
    is_create: bool, if getting the target for release creation.

  Returns:
    the target ID.

  Raises:
    NoStagesError: if no pipeline stages exist in the release.
    ReleaseInactiveError: if this is not called during release creation and the
    specified release has no rollouts.
  """

  if not release_obj.deliveryPipelineSnapshot.serialPipeline.stages:
    raise exceptions.NoStagesError(release_obj.name)
  # Use release short name to avoid the issue by mixed use of
  # the project number and id.
  release_ref = resources.REGISTRY.ParseRelativeName(
      release_obj.name,
      collection='clouddeploy.projects.locations.deliveryPipelines.releases',
  )
  to_target = release_obj.deliveryPipelineSnapshot.serialPipeline.stages[
      0
  ].targetId
  # The order of pipeline stages represents the promotion sequence.
  # E.g. test->stage->prod. Here we start with the last stage.
  reversed_stages = list(
      reversed(release_obj.deliveryPipelineSnapshot.serialPipeline.stages)
  )
  release_dict = release_ref.AsDict()
  for i, stage in enumerate(reversed_stages):
    target_ref = target_util.TargetReference(
        stage.targetId, release_dict['projectsId'], release_dict['locationsId']
    )
    # Starting with the last target in the promotion sequence per above, find
    # the last successfully deployed rollout to that target.
    current_rollout = target_util.GetCurrentRollout(
        target_ref,
        resources.REGISTRY.Parse(
            None,
            collection='clouddeploy.projects.locations.deliveryPipelines',
            params={
                'projectsId': release_dict['projectsId'],
                'locationsId': release_dict['locationsId'],
                'deliveryPipelinesId': release_dict['deliveryPipelinesId'],
            },
        ),
    )

    if current_rollout:
      current_rollout_ref = resources.REGISTRY.Parse(
          current_rollout.name,
          collection='clouddeploy.projects.locations.deliveryPipelines.releases.rollouts',
      )
      # Promotes the release from the target that is farthest along in the
      # promotion sequence to its next stage in the promotion sequence.
      if current_rollout_ref.Parent().Name() == release_ref.Name():
        if i > 0:
          to_target = reversed_stages[i - 1].targetId
        else:
          log.status.Print(
              _LAST_TARGET_IN_SEQUENCE.format(
                  release_ref.Name(),
                  target_ref.Name(),
                  release_ref.RelativeName(),
                  target_ref.RelativeName(),
              )
          )
          to_target = target_ref.RelativeName()
          # Once a target to promote to is found break out of the loop
        break

  # This means the release is not deployed to any target,
  # to_target flag is required in this case.
  if (
      to_target
      == release_obj.deliveryPipelineSnapshot.serialPipeline.stages[0].targetId
      and not is_create
  ):
    raise exceptions.ReleaseInactiveError()

  return target_util.TargetId(to_target)


def CheckIfInProgressRollout(release_ref, release_obj, to_target_id):
  """Checks if there are any rollouts in progress for the given release.

  Args:
    release_ref: protorpc.messages.Message, release resource object.
    release_obj: apitools.base.protorpclite.messages.Message, release message
      object.
    to_target_id: string, target id (e.g. 'prod')

  Raises:
    googlecloudsdk.command_lib.deploy.exceptions.RolloutInProgressError
  """
  rollouts = list(
      rollout.RolloutClient().List(
          release_ref.RelativeName(), IN_PROGRESS_FILTER_TEMPLATE, limit=1
      )
  )

  if rollouts:
    raise exceptions.RolloutInProgressError(release_obj.name, to_target_id)

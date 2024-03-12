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
"""Rollback a Cloud Deploy target to a prior rollout."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.clouddeploy import client_util
from googlecloudsdk.api_lib.clouddeploy import release
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.deploy import delivery_pipeline_util
from googlecloudsdk.command_lib.deploy import deploy_policy_util
from googlecloudsdk.command_lib.deploy import deploy_util
from googlecloudsdk.command_lib.deploy import exceptions as deploy_exceptions
from googlecloudsdk.command_lib.deploy import flags
from googlecloudsdk.command_lib.deploy import promote_util
from googlecloudsdk.command_lib.deploy import release_util
from googlecloudsdk.command_lib.deploy import resource_args
from googlecloudsdk.command_lib.deploy import rollout_util
from googlecloudsdk.command_lib.deploy import target_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
  To rollback a target 'prod' for delivery pipeline 'test-pipeline' in region 'us-central1', run:

  $ {command} prod --delivery-pipeline=test-pipeline --region=us-central1


""",
}
_ROLLBACK = 'rollback'


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Rollback(base.CreateCommand):
  """Rollbacks a target to a prior rollout.

  If release is not specified, the command rollbacks the target with the last
  successful deployed release. If optional rollout-id parameter is not
  specified, a generated rollout ID will be used.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddTargetResourceArg(parser, positional=True)
    flags.AddRelease(parser, 'Name of the release to rollback to.')
    flags.AddRolloutID(parser)
    flags.AddDeliveryPipeline(parser)
    flags.AddDescriptionFlag(parser)
    flags.AddAnnotationsFlag(parser, _ROLLBACK)
    flags.AddLabelsFlag(parser, _ROLLBACK)
    flags.AddStartingPhaseId(parser)
    flags.AddOverrideDeployPolicies(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      deploy_exceptions.HTTP_ERROR_FORMAT
  )
  def Run(self, args):
    target_ref = args.CONCEPTS.target.Parse()
    ref_dict = target_ref.AsDict()
    pipeline_ref = resources.REGISTRY.Parse(
        args.delivery_pipeline,
        collection='clouddeploy.projects.locations.deliveryPipelines',
        params={
            'projectsId': ref_dict['projectsId'],
            'locationsId': ref_dict['locationsId'],
            'deliveryPipelinesId': args.delivery_pipeline,
        },
    )
    pipeline_obj = delivery_pipeline_util.GetPipeline(
        pipeline_ref.RelativeName()
    )
    failed_activity_error_annotation_prefix = 'Cannot perform rollback.'
    delivery_pipeline_util.ThrowIfPipelineSuspended(
        pipeline_obj, failed_activity_error_annotation_prefix
    )
    # Check if target exists
    target_util.GetTarget(target_ref)

    current_release_ref, rollback_release_ref = _GetCurrentAndRollbackRelease(
        args.release, pipeline_ref, target_ref
    )

    release_obj = release.ReleaseClient().Get(
        rollback_release_ref.RelativeName()
    )

    if release_obj.abandoned:
      error_msg_annotation_prefix = 'Cannot perform rollback.'
      raise deploy_exceptions.AbandonedReleaseError(
          error_msg_annotation_prefix, rollback_release_ref.RelativeName()
      )
    messages = core_apis.GetMessagesModule('clouddeploy', 'v1')
    skaffold_support_state = release_util.GetSkaffoldSupportState(release_obj)
    skaffold_support_state_enum = (
        messages.SkaffoldSupportedCondition.SkaffoldSupportStateValueValuesEnum
    )
    if (skaffold_support_state ==
        skaffold_support_state_enum.SKAFFOLD_SUPPORT_STATE_MAINTENANCE_MODE):
      log.status.Print(
          "WARNING: This release's Skaffold version is in maintenance mode and"
          " will be unsupported soon.\n"
          " https://cloud.google.com/deploy/docs/using-skaffold/select-skaffold"
          "#skaffold_version_deprecation_and_maintenance_policy")

    if (skaffold_support_state ==
        skaffold_support_state_enum.SKAFFOLD_SUPPORT_STATE_UNSUPPORTED):
      raise core_exceptions.Error(
          "You can't roll back this target because the Skaffold version that"
          " was used to create the release is no longer supported.\n"
          "https://cloud.google.com/deploy/docs/using-skaffold/select-skaffold"
          "#skaffold_version_deprecation_and_maintenance_policy"
      )

    prompt = 'Rolling back target {} to release {}.\n\n'.format(
        target_ref.Name(), rollback_release_ref.Name()
    )
    release_util.PrintDiff(
        rollback_release_ref, release_obj, target_ref.Name(), prompt
    )

    console_io.PromptContinue(cancel_on_no=True)

    rollout_description = args.description or 'Rollback from {}'.format(
        current_release_ref.Name()
    )
    # On the command line deploy policy IDs are provided, but for the
    # CreateRollout API we need to provide the full resource name.
    policies = deploy_policy_util.CreateDeployPolicyNamesFromIDs(
        pipeline_ref, args.override_deploy_policies
    )
    return promote_util.Promote(
        rollback_release_ref,
        release_obj,
        target_ref.Name(),
        False,
        rollout_id=args.rollout_id,
        annotations=args.annotations,
        labels=args.labels,
        description=rollout_description,
        # For rollbacks, default is `stable`.
        starting_phase_id=args.starting_phase_id or 'stable',
        override_deploy_policies=policies,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RollbackAlpha(Rollback):
  """Rollbacks a target to a prior rollout.

  If release is not specified, the command rollbacks the target with the last
  successful deployed release. If optional rollout-id parameter is not
  specified, a generated rollout ID will be used.
  """

  @staticmethod
  def Args(parser):
    # add the original args
    Rollback.Args(parser)
    flags.AddRollbackOfRollout(parser)

  def Run(self, args):
    target_ref = args.CONCEPTS.target.Parse()
    ref_dict = target_ref.AsDict()
    pipeline_ref = resources.REGISTRY.Parse(
        args.delivery_pipeline,
        collection='clouddeploy.projects.locations.deliveryPipelines',
        params={
            'projectsId': ref_dict['projectsId'],
            'locationsId': ref_dict['locationsId'],
            'deliveryPipelinesId': args.delivery_pipeline,
        },
    )
    pipeline_obj = delivery_pipeline_util.GetPipeline(
        pipeline_ref.RelativeName()
    )
    failed_activity_error_annotation_prefix = 'Cannot perform rollback.'
    delivery_pipeline_util.ThrowIfPipelineSuspended(
        pipeline_obj, failed_activity_error_annotation_prefix
    )

    rollout_obj = client_util.GetMessagesModule().Rollout(
        description=args.description
    )

    deploy_util.SetMetadata(
        client_util.GetMessagesModule(),
        rollout_obj,
        deploy_util.ResourceType.ROLLOUT,
        args.annotations,
        args.labels,
    )

    # First call, we perform validate only call, making a copy of the response.
    validate_response = copy.deepcopy(
        delivery_pipeline_util.CreateRollbackTarget(
            pipeline_ref.RelativeName(),
            target_ref.Name(),
            validate_only=True,
            rollout_id=args.rollout_id,
            rollout_to_rollback=args.rollback_of_rollout,
            release_id=args.release,
            rollout_obj=rollout_obj,
            starting_phase=args.starting_phase_id,
        )
    )

    final_rollout_id = args.rollout_id
    rollback_release_ref = resources.REGISTRY.ParseRelativeName(
        resources.REGISTRY.Parse(
            validate_response.rollbackConfig.rollout.name,
            collection='clouddeploy.projects.locations.deliveryPipelines.releases.rollouts',
        )
        .Parent()
        .RelativeName(),
        collection='clouddeploy.projects.locations.deliveryPipelines.releases',
    )

    # If the rollout_id is not given, we will generate it and overwrite the
    # name that was part of the validate_only call. The reason for this is that
    # we want to generate the name from the release, but this isn't
    # available until after the validate_only call.
    # To make the initial validate_only call, there must be a rollout_id given,
    # so UUID is initially created for the request but ignored here.
    if not args.rollout_id:
      final_rollout_id = rollout_util.GenerateRolloutId(
          target_ref.Name(), rollback_release_ref
      )
      resource_dict = rollback_release_ref.AsDict()
      new_rollout_ref = resources.REGISTRY.Parse(
          final_rollout_id,
          collection='clouddeploy.projects.locations.deliveryPipelines.releases.rollouts',
          params={
              'projectsId': resource_dict.get('projectsId'),
              'locationsId': resource_dict.get('locationsId'),
              'deliveryPipelinesId': resource_dict.get('deliveryPipelinesId'),
              'releasesId': rollback_release_ref.Name(),
          },
      )
      validate_response.rollbackConfig.rollout.name = (
          new_rollout_ref.RelativeName()
      )

    # if args.description isn't set.
    if not args.description:
      current_release_ref = resources.REGISTRY.ParseRelativeName(
          resources.REGISTRY.Parse(
              validate_response.rollbackConfig.rollout.rollbackOfRollout,
              collection='clouddeploy.projects.locations.deliveryPipelines.releases.rollouts',
          )
          .Parent()
          .RelativeName(),
          collection=(
              'clouddeploy.projects.locations.deliveryPipelines.releases'
          ),
      )
      validate_response.rollbackConfig.rollout.description = (
          'Rollback from {}'.format(current_release_ref.Name())
      )

    try:
      release_obj = release.ReleaseClient().Get(
          rollback_release_ref.RelativeName()
      )
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(error)

    messages = core_apis.GetMessagesModule('clouddeploy', 'v1')
    skaffold_support_state_enum = (
        messages.SkaffoldSupportedCondition.SkaffoldSupportStateValueValuesEnum
    )
    skaffold_support_state = release_util.GetSkaffoldSupportState(release_obj)
    if (skaffold_support_state ==
        skaffold_support_state_enum.SKAFFOLD_SUPPORT_STATE_MAINTENANCE_MODE):
      log.status.Print(
          "WARNING: This release's Skaffold version is in maintenance mode and"
          " will be unsupported soon.\n"
          " https://cloud.google.com/deploy/docs/using-skaffold/select-skaffold"
          "#skaffold_version_deprecation_and_maintenance_policy")

    if (skaffold_support_state ==
        skaffold_support_state_enum.SKAFFOLD_SUPPORT_STATE_UNSUPPORTED):
      raise core_exceptions.Error(
          "You can't roll back this target because the Skaffold version that"
          " was used to create the release is no longer supported.\n"
          "https://cloud.google.com/deploy/docs/using-skaffold/select-skaffold"
          "#skaffold_version_deprecation_and_maintenance_policy"
      )
    # prompt to see whether user wants to continue.
    prompt = 'Rolling back target {} to release {}.\n\n'.format(
        target_ref.Name(), rollback_release_ref.Name()
    )
    release_util.PrintDiff(
        rollback_release_ref, release_obj, target_ref.Name(), prompt
    )

    console_io.PromptContinue(cancel_on_no=True)

    create_response = delivery_pipeline_util.CreateRollbackTarget(
        pipeline_ref.RelativeName(),
        target_ref.Name(),
        validate_only=False,
        # use the final_rollout_id which was calculated on client
        rollout_id=final_rollout_id,
        release_id=rollback_release_ref.Name(),
        # use the server calculated fields for the rest of the fields.
        rollout_to_rollback=validate_response.rollbackConfig.rollout.rollbackOfRollout,
        rollout_obj=validate_response.rollbackConfig.rollout,
        starting_phase=validate_response.rollbackConfig.startingPhaseId,
    )
    # return the rollout resource that was created
    return create_response.rollbackConfig.rollout


def _GetCurrentAndRollbackRelease(release_id, pipeline_ref, target_ref):
  """Gets the current deployed release and the release that will be used by promote API to create the rollback rollout."""
  if release_id:
    ref_dict = target_ref.AsDict()
    current_rollout = target_util.GetCurrentRollout(target_ref, pipeline_ref)
    current_release_ref = resources.REGISTRY.ParseRelativeName(
        resources.REGISTRY.Parse(
            current_rollout.name,
            collection='clouddeploy.projects.locations.deliveryPipelines.releases.rollouts',
        )
        .Parent()
        .RelativeName(),
        collection='clouddeploy.projects.locations.deliveryPipelines.releases',
    )
    rollback_release_ref = resources.REGISTRY.Parse(
        release_id,
        collection='clouddeploy.projects.locations.deliveryPipelines.releases',
        params={
            'projectsId': ref_dict['projectsId'],
            'locationsId': ref_dict['locationsId'],
            'deliveryPipelinesId': pipeline_ref.Name(),
            'releasesId': release_id,
        },
    )
    return current_release_ref, rollback_release_ref
  else:
    prior_rollouts = rollout_util.GetValidRollBackCandidate(
        target_ref, pipeline_ref
    )
    if len(prior_rollouts) < 2:
      raise core_exceptions.Error(
          'unable to rollback target {}. Target has less than 2 rollouts.'
          .format(target_ref.Name())
      )
    current_deployed_rollout, previous_deployed_rollout = prior_rollouts

    current_release_ref = resources.REGISTRY.ParseRelativeName(
        resources.REGISTRY.Parse(
            current_deployed_rollout.name,
            collection='clouddeploy.projects.locations.deliveryPipelines.releases.rollouts',
        )
        .Parent()
        .RelativeName(),
        collection='clouddeploy.projects.locations.deliveryPipelines.releases',
    )
    rollback_release_ref = resources.REGISTRY.ParseRelativeName(
        resources.REGISTRY.Parse(
            previous_deployed_rollout.name,
            collection='clouddeploy.projects.locations.deliveryPipelines.releases.rollouts',
        )
        .Parent()
        .RelativeName(),
        collection='clouddeploy.projects.locations.deliveryPipelines.releases',
    )
    return current_release_ref, rollback_release_ref

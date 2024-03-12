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
"""Redeploy a rollout to a target."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.clouddeploy import release
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import delivery_pipeline_util
from googlecloudsdk.command_lib.deploy import deploy_policy_util
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
  To redeploy a target `prod` for delivery pipeline `test-pipeline` in region `us-central1`, run:

  $ {command} prod --delivery-pipeline=test-pipeline --region=us-central1

""",
}
_ROLLOUT = 'rollout'


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Redeploy(base.CreateCommand):
  """Redeploy the last release to a target.

  Redeploy the last rollout that has a state of SUCCESSFUL or FAILED to a
  target.
  If rollout-id is not specified, a rollout ID will be generated.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddTargetResourceArg(parser, positional=True)
    flags.AddRolloutID(parser)
    flags.AddDeliveryPipeline(parser)
    flags.AddDescriptionFlag(parser)
    flags.AddAnnotationsFlag(parser, _ROLLOUT)
    flags.AddLabelsFlag(parser, _ROLLOUT)
    flags.AddStartingPhaseId(parser)
    flags.AddOverrideDeployPolicies(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      deploy_exceptions.HTTP_ERROR_FORMAT
  )
  def Run(self, args):
    target_ref = args.CONCEPTS.target.Parse()
    # Check if target exists
    target_util.GetTarget(target_ref)
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
    failed_redeploy_prefix = 'Cannot perform redeploy.'
    # Check is the pipeline is suspended.
    delivery_pipeline_util.ThrowIfPipelineSuspended(
        pipeline_obj, failed_redeploy_prefix
    )
    current_release_ref = _GetCurrentRelease(
        pipeline_ref, target_ref, rollout_util.ROLLOUT_IN_TARGET_FILTER_TEMPLATE
    )
    release_obj = release.ReleaseClient().Get(
        current_release_ref.RelativeName()
    )

    # Check if the release is abandoned.
    if release_obj.abandoned:
      raise deploy_exceptions.AbandonedReleaseError(
          failed_redeploy_prefix, current_release_ref.RelativeName()
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
          ' will be unsupported soon.\n'
          ' https://cloud.google.com/deploy/docs/using-skaffold/select-skaffold'
          '#skaffold_version_deprecation_and_maintenance_policy'
      )

    if (skaffold_support_state ==
        skaffold_support_state_enum.SKAFFOLD_SUPPORT_STATE_UNSUPPORTED):
      raise core_exceptions.Error(
          "You can't redeploy this release because the Skaffold version that"
          ' was used to create the release is no longer supported.\n'
          'https://cloud.google.com/deploy/docs/using-skaffold/select-skaffold'
          '#skaffold_version_deprecation_and_maintenance_policy'
      )

    prompt = (
        'Are you sure you want to redeploy release {} to target {}?'.format(
            current_release_ref.Name(), target_ref.Name()
        )
    )
    console_io.PromptContinue(prompt, cancel_on_no=True)
    # On the command line deploy policy IDs are provided, but for the
    # CreateRollout API we need to provide the full resource name.
    policies = deploy_policy_util.CreateDeployPolicyNamesFromIDs(
        pipeline_ref, args.override_deploy_policies
    )

    promote_util.Promote(
        current_release_ref,
        release_obj,
        target_ref.Name(),
        False,
        rollout_id=args.rollout_id,
        annotations=args.annotations,
        labels=args.labels,
        description=args.description,
        starting_phase_id=args.starting_phase_id,
        override_deploy_policies=policies,
    )


def _GetCurrentRelease(pipeline_ref, target_ref, filter_str):
  """Gets the current release in the target.

  Args:
    pipeline_ref: pipeline_ref: protorpc.messages.Message, pipeline object.
    target_ref: target_ref: protorpc.messages.Message, target object.
    filter_str: Filter string to use when listing rollouts.

  Returns:
    The most recent release with the given pipeline and target with a rollout
    that is redeployable.

  Raises:
    core.Error: Target has no rollouts or rollouts in target are not
                redeployable.
  """
  # Get the most recent rollout in the target, by EnqueueTime descending. Using
  # EnqueueTime instead of DeployEndTime because this needs to return the latest
  # rollout in any state (e.g. PENDING_APPROVAL, IN_PROGRESS). If it's not in
  # a state that's redeployable an exception is returned.
  prior_rollouts = list(
      rollout_util.GetFilteredRollouts(
          target_ref=target_ref,
          pipeline_ref=pipeline_ref,
          filter_str=filter_str,
          order_by=rollout_util.ENQUEUETIME_ROLLOUT_ORDERBY,
          limit=1,
      )
  )
  if len(prior_rollouts) < 1:
    raise core_exceptions.Error(
        'unable to redeploy to target {}. Target has no rollouts.'.format(
            target_ref.Name()
        )
    )
  prior_rollout = prior_rollouts[0]
  messages = core_apis.GetMessagesModule('clouddeploy', 'v1')
  redeployable_states = [
      messages.Rollout.StateValueValuesEnum.SUCCEEDED,
      messages.Rollout.StateValueValuesEnum.FAILED,
      messages.Rollout.StateValueValuesEnum.CANCELLED,
  ]
  if prior_rollout.state not in redeployable_states:
    raise deploy_exceptions.RedeployRolloutError(
        target_ref.Name(), prior_rollout.name, prior_rollout.state
    )

  current_release_ref = resources.REGISTRY.ParseRelativeName(
      resources.REGISTRY.Parse(
          prior_rollout.name,
          collection=(
              'clouddeploy.projects.locations.deliveryPipelines'
              '.releases.rollouts'
          ),
      )
      .Parent()
      .RelativeName(),
      collection='clouddeploy.projects.locations.deliveryPipelines.releases',
  )
  return current_release_ref

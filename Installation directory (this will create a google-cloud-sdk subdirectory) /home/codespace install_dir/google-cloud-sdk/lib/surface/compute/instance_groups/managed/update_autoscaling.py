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
"""Command to PATCH-style update autoscaling for a managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils as mig_utils
from googlecloudsdk.api_lib.compute.instance_groups.managed import autoscalers as autoscalers_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import exceptions


def _CommonArgs(parser):
  instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
      parser)
  mig_utils.GetModeFlag().AddToParser(parser)
  mig_utils.AddScaleInControlFlag(parser, include_clear=True)
  mig_utils.AddMinMaxControl(parser, max_required=False)
  mig_utils.AddScheduledAutoscaling(parser, patch_args=True)


class NoMatchingAutoscalerFoundError(exceptions.Error):
  pass


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateAutoscaling(base.Command):
  """Update autoscaling parameters of a managed instance group."""

  clear_scale_down = False

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)
    mig_utils.AddPredictiveAutoscaling(parser, standard=False)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    igm_ref = instance_groups_flags.CreateGroupReference(
        client, holder.resources, args)

    # Assert that Instance Group Manager exists.
    mig_utils.GetInstanceGroupManagerOrThrow(igm_ref, client)

    old_autoscaler = mig_utils.AutoscalerForMigByRef(client, holder.resources,
                                                     igm_ref)
    if mig_utils.IsAutoscalerNew(old_autoscaler):
      raise NoMatchingAutoscalerFoundError(
          'Instance group manager [{}] has no existing autoscaler; '
          'cannot update.'.format(igm_ref.Name()))

    autoscalers_client = autoscalers_api.GetClient(client, igm_ref)
    new_autoscaler = autoscalers_client.message_type(
        name=old_autoscaler.name,  # PATCH needs this
        autoscalingPolicy=client.messages.AutoscalingPolicy())
    if args.IsSpecified('mode'):
      mode = mig_utils.ParseModeString(args.mode, client.messages)
      new_autoscaler.autoscalingPolicy.mode = mode

    if args.IsSpecified('clear_scale_in_control'):
      new_autoscaler.autoscalingPolicy.scaleInControl = None
    else:
      new_autoscaler.autoscalingPolicy.scaleInControl = \
        mig_utils.BuildScaleIn(args, client.messages)

    if self.clear_scale_down and args.IsSpecified('clear_scale_down_control'):
      new_autoscaler.autoscalingPolicy.scaleDownControl = None

    if args.IsSpecified('cpu_utilization_predictive_method'):
      cpu_predictive_enum = client.messages.AutoscalingPolicyCpuUtilization.PredictiveMethodValueValuesEnum
      new_autoscaler.autoscalingPolicy.cpuUtilization = client.messages.AutoscalingPolicyCpuUtilization(
      )
      new_autoscaler.autoscalingPolicy.cpuUtilization.predictiveMethod = arg_utils.ChoiceToEnum(
          args.cpu_utilization_predictive_method, cpu_predictive_enum)

    scheduled = mig_utils.BuildSchedules(args, client.messages)
    if scheduled:
      new_autoscaler.autoscalingPolicy.scalingSchedules = scheduled

    if args.IsSpecified('min_num_replicas'):
      new_autoscaler.autoscalingPolicy.minNumReplicas = args.min_num_replicas
    if args.IsSpecified('max_num_replicas'):
      new_autoscaler.autoscalingPolicy.maxNumReplicas = args.max_num_replicas

    return self._SendPatchRequest(args, client, autoscalers_client, igm_ref,
                                  new_autoscaler)

  def _SendPatchRequest(self, args, client, autoscalers_client, igm_ref,
                        new_autoscaler):
    if args.IsSpecified('clear_scale_in_control'):
      # Apitools won't send null fields unless explicitly told to.
      with client.apitools_client.IncludeFields(
          ['autoscalingPolicy.scaleInControl']):
        return autoscalers_client.Patch(igm_ref, new_autoscaler)
    elif self.clear_scale_down and args.IsSpecified('clear_scale_down_control'):
      with client.apitools_client.IncludeFields(
          ['autoscalingPolicy.scaleDownControl']):
        return autoscalers_client.Patch(igm_ref, new_autoscaler)
    else:
      return autoscalers_client.Patch(igm_ref, new_autoscaler)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateAutoscalingBeta(UpdateAutoscaling):
  """Update autoscaling parameters of a managed instance group."""

  clear_scale_down = True

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)
    mig_utils.AddPredictiveAutoscaling(parser, standard=False)
    mig_utils.AddClearScaleDownControlFlag(parser)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAutoscalingAlpha(UpdateAutoscalingBeta):
  """Update autoscaling parameters of a managed instance group."""

  clear_scale_down = True

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)
    mig_utils.AddPredictiveAutoscaling(parser)
    mig_utils.AddClearScaleDownControlFlag(parser)

UpdateAutoscaling.detailed_help = {
    'brief': 'Update autoscaling parameters of a managed instance group',
    'EXAMPLES':
        """\
        To update an existing instance group:

            $ {command} --mode=only-scale-out

        """,
    'DESCRIPTION': """
*{command}* updates autoscaling parameters of specified managed instance
group.

Autoscalers can use one or more autoscaling signals. Information on using
multiple autoscaling signals can be found here: [](https://cloud.google.com/compute/docs/autoscaler/multiple-signals)

In contrast to *{parent_command} set-autoscaling*, this command *only* updates
specified fields. For instance:

    $ {command} --mode only-scale-out

would change the *mode* field of the autoscaler policy, but leave the rest of
the settings intact.
        """,
}
UpdateAutoscalingAlpha.detailed_help = UpdateAutoscaling.detailed_help
UpdateAutoscalingBeta.detailed_help = UpdateAutoscaling.detailed_help

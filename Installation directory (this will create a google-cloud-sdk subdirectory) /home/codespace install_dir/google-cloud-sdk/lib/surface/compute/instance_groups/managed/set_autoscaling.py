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
"""Command for configuring autoscaling of a managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import re

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.api_lib.compute.instance_groups.managed import autoscalers as autoscalers_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files


_DELETE_AUTOSCALER_PROMPT = (
    'Configuration specifies no autoscaling configuration. '
    'Continuing will delete the existing autoscaler '
    'configuration.')
_REPLACE_AUTOSCALER_PROMPT = (
    'Configuration specifies autoscaling configuration with a '
    'different name than existing. Continuing will delete '
    'existing autoscaler and create new one with a different name.')
_DELETION_CANCEL_STRING = 'Deletion aborted by user.'


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SetAutoscaling(base.Command):
  """Set autoscaling parameters of a managed instance group."""

  @staticmethod
  def Args(parser):
    managed_instance_groups_utils.AddAutoscalerArgs(parser=parser)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)
    managed_instance_groups_utils.AddPredictiveAutoscaling(parser,
                                                           standard=False)

  def CreateAutoscalerResource(self,
                               client,
                               resources,
                               igm_ref,
                               args):
    autoscaler = managed_instance_groups_utils.AutoscalerForMigByRef(
        client, resources, igm_ref)
    autoscaler_name = getattr(autoscaler, 'name', None)
    new_one = managed_instance_groups_utils.IsAutoscalerNew(autoscaler)
    autoscaler_name = autoscaler_name or args.name
    autoscaler_resource = managed_instance_groups_utils.BuildAutoscaler(
        args,
        client.messages,
        igm_ref,
        autoscaler_name,
        autoscaler)
    return autoscaler_resource, new_one

  def _SetAutoscalerFromFile(
      self, autoscaling_file, autoscalers_client, igm_ref,
      existing_autoscaler_name):
    new_autoscaler = json.loads(files.ReadFileContents(autoscaling_file))
    if new_autoscaler is None:
      if existing_autoscaler_name is None:
        log.info('Configuration specifies no autoscaling and there is no '
                 'autoscaling configured. Nothing to do.')
        return
      else:
        console_io.PromptContinue(
            message=_DELETE_AUTOSCALER_PROMPT, cancel_on_no=True,
            cancel_string=_DELETION_CANCEL_STRING)
        return autoscalers_client.Delete(igm_ref, existing_autoscaler_name)

    new_autoscaler = encoding.DictToMessage(new_autoscaler,
                                            autoscalers_client.message_type)
    if existing_autoscaler_name is None:
      managed_instance_groups_utils.AdjustAutoscalerNameForCreation(
          new_autoscaler, igm_ref)
      return autoscalers_client.Insert(igm_ref, new_autoscaler)

    if (getattr(new_autoscaler, 'name', None) and
        getattr(new_autoscaler, 'name') != existing_autoscaler_name):
      console_io.PromptContinue(
          message=_REPLACE_AUTOSCALER_PROMPT, cancel_on_no=True,
          cancel_string=_DELETION_CANCEL_STRING)
      autoscalers_client.Delete(igm_ref, existing_autoscaler_name)
      return autoscalers_client.Insert(igm_ref, new_autoscaler)

    new_autoscaler.name = existing_autoscaler_name
    return autoscalers_client.Update(igm_ref, new_autoscaler)

  def _PromptToAutoscaleGKENodeGroup(self, args):
    prompt_message = (
        'You should not use Compute Engine\'s autoscaling feature '
        'on instance groups created by Kubernetes Engine.')
    if re.match(r'^gke-.*-[0-9a-f]{1,8}-grp$', args.name):
      console_io.PromptContinue(
          message=prompt_message, default=False, cancel_on_no=True,
          cancel_string='Setting autoscaling aborted by user.')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    managed_instance_groups_utils.ValidateAutoscalerArgs(args)
    managed_instance_groups_utils.ValidateStackdriverMetricsFlags(args)

    igm_ref = instance_groups_flags.CreateGroupReference(
        client, holder.resources, args)

    # Assert that Instance Group Manager exists.
    managed_instance_groups_utils.GetInstanceGroupManagerOrThrow(
        igm_ref, client)

    # Require confirmation if autoscaling a GKE node group.
    self._PromptToAutoscaleGKENodeGroup(args)

    autoscaler_resource, is_new = self.CreateAutoscalerResource(
        client, holder.resources, igm_ref, args)

    managed_instance_groups_utils.ValidateGeneratedAutoscalerIsValid(
        args, autoscaler_resource)

    autoscalers_client = autoscalers_api.GetClient(client, igm_ref)
    if is_new:
      managed_instance_groups_utils.AdjustAutoscalerNameForCreation(
          autoscaler_resource, igm_ref)
      return autoscalers_client.Insert(igm_ref, autoscaler_resource)
    return autoscalers_client.Update(igm_ref, autoscaler_resource)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class SetAutoscalingBeta(SetAutoscaling):
  """Set autoscaling parameters of a managed instance group."""

  @staticmethod
  def Args(parser):
    managed_instance_groups_utils.AddAutoscalerArgs(
        parser=parser,
        autoscaling_file_enabled=True,
        patch_args=False)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)
    managed_instance_groups_utils.AddPredictiveAutoscaling(parser,
                                                           standard=False)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    managed_instance_groups_utils.ValidateAutoscalerArgs(args)
    managed_instance_groups_utils.ValidateStackdriverMetricsFlags(args)
    managed_instance_groups_utils.ValidateConflictsWithAutoscalingFile(
        args,
        (managed_instance_groups_utils.
         ARGS_CONFLICTING_WITH_AUTOSCALING_FILE_BETA))
    igm_ref = instance_groups_flags.CreateGroupReference(
        client, holder.resources, args)

    # Assert that Instance Group Manager exists.
    managed_instance_groups_utils.GetInstanceGroupManagerOrThrow(
        igm_ref, client)

    autoscaler_resource, is_new = self.CreateAutoscalerResource(
        client, holder.resources, igm_ref, args)

    managed_instance_groups_utils.ValidateGeneratedAutoscalerIsValid(
        args, autoscaler_resource)

    autoscalers_client = autoscalers_api.GetClient(client, igm_ref)
    if args.IsSpecified('autoscaling_file'):
      if is_new:
        existing_autoscaler_name = None
      else:
        existing_autoscaler_name = autoscaler_resource.name
      return self._SetAutoscalerFromFile(
          args.autoscaling_file, autoscalers_client, igm_ref,
          existing_autoscaler_name)

    if is_new:
      managed_instance_groups_utils.AdjustAutoscalerNameForCreation(
          autoscaler_resource, igm_ref)
      return autoscalers_client.Insert(igm_ref, autoscaler_resource)
    return autoscalers_client.Update(igm_ref, autoscaler_resource)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class SetAutoscalingAlpha(SetAutoscaling):
  """Set autoscaling parameters of a managed instance group."""

  @staticmethod
  def Args(parser):
    managed_instance_groups_utils.AddAutoscalerArgs(
        parser=parser,
        autoscaling_file_enabled=True,
        patch_args=False)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)
    managed_instance_groups_utils.AddPredictiveAutoscaling(parser,
                                                           standard=True)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    managed_instance_groups_utils.ValidateAutoscalerArgs(args)
    managed_instance_groups_utils.ValidateStackdriverMetricsFlags(args)
    managed_instance_groups_utils.ValidateConflictsWithAutoscalingFile(
        args,
        (managed_instance_groups_utils.
         ARGS_CONFLICTING_WITH_AUTOSCALING_FILE_ALPHA))
    igm_ref = instance_groups_flags.CreateGroupReference(
        client, holder.resources, args)

    # Assert that Instance Group Manager exists.
    managed_instance_groups_utils.GetInstanceGroupManagerOrThrow(
        igm_ref, client)

    autoscaler_resource, is_new = self.CreateAutoscalerResource(
        client,
        holder.resources,
        igm_ref,
        args)

    managed_instance_groups_utils.ValidateGeneratedAutoscalerIsValid(
        args, autoscaler_resource)

    autoscalers_client = autoscalers_api.GetClient(client, igm_ref)
    if args.IsSpecified('autoscaling_file'):
      if is_new:
        existing_autoscaler_name = None
      else:
        existing_autoscaler_name = autoscaler_resource.name
      return self._SetAutoscalerFromFile(
          args.autoscaling_file, autoscalers_client, igm_ref,
          existing_autoscaler_name)

    if is_new:
      managed_instance_groups_utils.AdjustAutoscalerNameForCreation(
          autoscaler_resource, igm_ref)
      return autoscalers_client.Insert(igm_ref, autoscaler_resource)
    return autoscalers_client.Update(igm_ref, autoscaler_resource)

SetAutoscaling.detailed_help = {
    'brief': 'Set autoscaling parameters of a managed instance group',
    'DESCRIPTION': """
        *{command}* sets autoscaling parameters of specified managed instance
group.

Autoscalers can use one or more autoscaling signals. Information on using
multiple autoscaling signals can be found here: [](https://cloud.google.com/compute/docs/autoscaler/multiple-signals)
        """,
}
SetAutoscalingAlpha.detailed_help = SetAutoscaling.detailed_help
SetAutoscalingBeta.detailed_help = SetAutoscaling.detailed_help

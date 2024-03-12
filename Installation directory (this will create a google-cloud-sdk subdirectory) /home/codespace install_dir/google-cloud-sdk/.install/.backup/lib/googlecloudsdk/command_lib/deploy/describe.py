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
"""Utilities for the cloud deploy describe commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.command_lib.deploy import delivery_pipeline_util
from googlecloudsdk.command_lib.deploy import rollout_util
from googlecloudsdk.command_lib.deploy import target_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


def DescribeTarget(target_ref, pipeline_id, skip_pipeline_lookup,
                   list_all_pipelines):
  """Describes details specific to the individual target, delivery pipeline qualified.

  Args:
    target_ref: protorpc.messages.Message, target reference.
    pipeline_id: str, delivery pipeline ID.
    skip_pipeline_lookup: Boolean, flag indicating whether to fetch information
      from the pipeline(s) containing target. If set, pipeline information will
      not be fetched.
    list_all_pipelines: Boolean, flag indicating whether to fetch information
      from all pipelines associated with target, if set to false, it will fetch
      information from the most recently updated one.

  Returns:
    A dictionary of <section name:output>.

  """
  target_obj = target_util.GetTarget(target_ref)
  output = {'Target': target_obj}
  if skip_pipeline_lookup:
    return output
  if pipeline_id:
    return DescribeTargetWithPipeline(target_obj, target_ref, pipeline_id,
                                      output)
  else:
    return DescribeTargetWithNoPipeline(target_obj, target_ref,
                                        list_all_pipelines, output)


def DescribeTargetWithPipeline(target_obj, target_ref, pipeline_id, output):
  """Describes details specific to the individual target, delivery pipeline qualified.

  The output contains four sections:

  target
    - detail of the target to be described.

  latest release
    - the detail of the active release in the target.

  latest rollout
    - the detail of the active rollout in the target.

  deployed
    - timestamp of the last successful deployment.

  pending approvals
    - list rollouts that require approval.
  Args:
    target_obj: protorpc.messages.Message, target object.
    target_ref: protorpc.messages.Message, target reference.
    pipeline_id: str, delivery pipeline ID.
    output: A dictionary of <section name:output>.

  Returns:
    A dictionary of <section name:output>.

  """
  target_dict = target_ref.AsDict()
  pipeline_ref = resources.REGISTRY.Parse(
      None,
      collection='clouddeploy.projects.locations.deliveryPipelines',
      params={
          'projectsId': target_dict['projectsId'],
          'locationsId': target_dict['locationsId'],
          'deliveryPipelinesId': pipeline_id
      })

  current_rollout = target_util.GetCurrentRollout(target_ref, pipeline_ref)
  output = SetCurrentReleaseAndRollout(current_rollout, output)
  if target_obj.requireApproval:
    output = ListPendingApprovals(target_ref, pipeline_ref, output)
  return output


def DescribeTargetWithNoPipeline(target_obj, target_ref, list_all_pipelines,
                                 output):
  """Describes details specific to the individual target.

  In addition, it will also display details about pipelines associated
  with the given target.

  The output contains the following sections:

  target
    - details of the target to be described.

  associated pipelines
    - details of the pipelines that use the target.

  For each associated pipeline, the following will be displayed:

  latest release
    - details of the active release in the target.

  latest rollout
    - details of the active rollout in the target.

  deployed
    - timestamp of the last successful deployment.

  pending approvals
    - list the rollouts that require approval.

  Args:
    target_obj: protorpc.messages.Message, target object.
    target_ref: protorpc.messages.Message, target reference.
    list_all_pipelines: Boolean, if true, will return information about all
      pipelines associated with target, otherwise, the most recently active
      pipeline information will be displayed.
    output: A dictionary of <section name:output>.

  Returns:
    A dictionary of <section name:output>.

  """
  sorted_pipelines = GetTargetDeliveryPipelines(target_ref)
  if not sorted_pipelines:
    return output

  output['Number of associated delivery pipelines'] = len(sorted_pipelines)
  pipeline_refs = list(
      map(delivery_pipeline_util.PipelineToPipelineRef, sorted_pipelines))
  if list_all_pipelines:
    output['Associated delivery pipelines'] = ListAllPipelineReleaseRollout(
        target_ref, pipeline_refs)
    if target_obj.requireApproval:
      ListPendingApprovalsMultiplePipelines(target_ref, pipeline_refs, output)
  else:
    active_pipeline_ref, latest_rollout = GetMostRecentlyActivePipeline(
        target_ref, pipeline_refs)
    if active_pipeline_ref and latest_rollout:
      output['Active Pipeline'] = SetMostRecentlyActivePipeline(
          active_pipeline_ref, latest_rollout)
    if target_obj.requireApproval:
      ListPendingApprovals(target_ref, active_pipeline_ref, output)
  return output


def ListPendingApprovalsMultiplePipelines(target_ref, pipeline_refs, output):
  """Fetches a list of pending rollouts for each pipeline and appends the result to a single list.

  Args:
    target_ref: protorpc.messages.Message, target object.
    pipeline_refs: protorpc.messages.Message, list of pipeline objects.
    output: dictionary object

  Returns:
    The modified output object with the list of pending rollouts.

  """
  all_pending_approvals = []
  for pipeline_ref in pipeline_refs:
    result_dict = ListPendingApprovals(target_ref, pipeline_ref, {})
    approvals_one_pipeline = result_dict.get('Pending Approvals', [])
    all_pending_approvals.extend(approvals_one_pipeline)
  output['Pending Approvals'] = all_pending_approvals
  return output


def SetCurrentReleaseAndRollout(current_rollout, output):
  """Set current release and the last deployment section in the output.

  Args:
    current_rollout: protorpc.messages.Message, rollout object.
    output: dictionary object

  Returns:
    The modified output object with the rollout's parent release, the name of
    the rollout, and the time it was deployed.

  """
  if current_rollout:
    current_rollout_ref = resources.REGISTRY.Parse(
        current_rollout.name,
        collection='clouddeploy.projects.locations.deliveryPipelines.releases.rollouts'
    )
    # get the name of the release associated with the current rollout.
    output['Latest release'] = current_rollout_ref.Parent().RelativeName()
    output['Latest rollout'] = current_rollout_ref.RelativeName()
    output['Deployed'] = current_rollout.deployEndTime

  return output


def ListPendingApprovals(target_ref, pipeline_ref, output):
  """Lists the rollouts in pending approval state for the specified target.

  Args:
    target_ref: protorpc.messages.Message, target object.
    pipeline_ref: protorpc.messages.Message, pipeline object.
    output: dictionary object

  Returns:
    The modified output object with the rollouts from the given pipeline pending
    approval on the given target.

  """
  try:
    pending_approvals = rollout_util.ListPendingRollouts(
        target_ref, pipeline_ref)
    pending_approvals_names = []
    for ro in pending_approvals:
      pending_approvals_names.append(ro.name)
    if pending_approvals_names:
      output['Pending Approvals'] = pending_approvals_names
  except apitools_exceptions.HttpError as error:
    log.debug('Failed to list pending approvals: ' + error.content)

  return output


def GetTargetDeliveryPipelines(target_ref):
  """Get all pipelines associated with a target.

  Args:
    target_ref: protorpc.messages.Message, target object.

  Returns:
    A list of delivery pipelines sorted by creation date, or an null list if
    there is an error fetching the pipelines.

  """

  target_dict = target_ref.AsDict()
  location_ref = resources.REGISTRY.Parse(
      None,
      collection='clouddeploy.projects.locations',
      params={
          'projectsId': target_dict['projectsId'],
          'locationsId': target_dict['locationsId'],
      })
  try:
    return delivery_pipeline_util.ListDeliveryPipelinesWithTarget(
        target_ref, location_ref)
  except apitools_exceptions.HttpError as error:
    log.warning('Failed to fetch pipelines for target: ' + error.content)
    return None


def GetPipelinesAndRollouts(target_ref, pipeline_refs):
  """Retrieves the latest rollout for each delivery pipeline.

  Args:
    target_ref: protorpc.messages.Message, target object.
    pipeline_refs: protorpc.messages.Message, pipeline object.

  Returns:
    A list with element [pipeline_ref, rollout] where the rollout is the latest
    successful rollout of the pipeline resource.

  """
  result = []
  for pipeline_ref in pipeline_refs:
    rollout = target_util.GetCurrentRollout(target_ref, pipeline_ref)
    if rollout is not None:
      result.append([pipeline_ref, rollout])
  return result


def GetMostRecentlyActivePipeline(target_ref, sorted_pipeline_refs):
  """Retrieves latest rollout and release information for a list of delivery pipelines.

  Args:
    target_ref: protorpc.messages.Message, target object.
    sorted_pipeline_refs: protorpc.messages.Message, a list of pipeline objects,
      sorted in descending order by create time.

  Returns:
    A tuple of the pipeline with the most recent deploy time with
     latest rollout.

  """
  pipeline_rollouts = GetPipelinesAndRollouts(target_ref, sorted_pipeline_refs)
  if not pipeline_rollouts:
    log.debug('Target: {} has no recently active pipelines.'.format(
        target_ref.RelativeName()))
    return sorted_pipeline_refs[0], None
  most_recent_pipeline_ref, most_recent_rollout = pipeline_rollouts[0]
  most_recent_rollout_deploy_time = datetime.datetime.strptime(
      most_recent_rollout.deployEndTime, '%Y-%m-%dT%H:%M:%S.%fZ')

  for pipeline_rollout_tuple in pipeline_rollouts[1:]:
    pipeline_ref, rollout = pipeline_rollout_tuple
    rollout_deploy_time = datetime.datetime.strptime(rollout.deployEndTime,
                                                     '%Y-%m-%dT%H:%M:%S.%fZ')
    if rollout_deploy_time > most_recent_rollout_deploy_time:
      most_recent_pipeline_ref = pipeline_ref
      most_recent_rollout = rollout
      most_recent_rollout_deploy_time = rollout_deploy_time
  return most_recent_pipeline_ref, most_recent_rollout


def SetMostRecentlyActivePipeline(pipeline_ref, rollout):
  """Retrieves latest rollout and release information for a delivery pipeline.

  Args:
    pipeline_ref: protorpc.messages.Message a DeliveryPipeline object.
    rollout: protorpc.messages.Message a Rollout object.

  Returns:
    A content directory.

  """
  output = [{
      pipeline_ref.RelativeName(): SetCurrentReleaseAndRollout(rollout, {})
  }]
  return output


def SetPipelineReleaseRollout(target_ref, pipeline_ref):
  """Retrieves latest rollout and release information for a single delivery pipeline.

  Args:
    target_ref: protorpc.messages.Message, target object.
    pipeline_ref: protorpc.messages.Message, DeliveryPipeline object

  Returns:
    A content directory.

  """

  current_rollout = target_util.GetCurrentRollout(target_ref, pipeline_ref)
  output = {}
  output = SetCurrentReleaseAndRollout(current_rollout, output)
  return output


def ListAllPipelineReleaseRollout(target_ref, pipeline_refs):
  """Retrieves latest rollout and release information for each delivery pipeline.

  Args:
    target_ref: protorpc.messages.Message, target object.
    pipeline_refs: protorpc.messages.Message a list of DeliveryPipeline objects

  Returns:
    A content directory.

  """
  output = []
  for pipeline_ref in pipeline_refs:
    pipeline_entry = SetPipelineReleaseRollout(target_ref, pipeline_ref)
    output.append({pipeline_ref.RelativeName(): pipeline_entry})
  return output

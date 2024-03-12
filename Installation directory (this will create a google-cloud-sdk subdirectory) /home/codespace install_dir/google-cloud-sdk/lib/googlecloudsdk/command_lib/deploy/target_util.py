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
"""Utilities for the cloud deploy target resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.clouddeploy import target
from googlecloudsdk.command_lib.deploy import rollout_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

_SHARED_TARGET_COLLECTION = 'clouddeploy.projects.locations.targets'


def GetCurrentRollout(target_ref, pipeline_ref):
  """Gets the releases in the specified target and the last deployment associated with the target.

  Args:
    target_ref: protorpc.messages.Message, target resource object.
    pipeline_ref: protorpc.messages.Message, pipeline object.

  Returns:
    release messages associated with the target.
    last deployed rollout message.
  Raises:
   Exceptions raised by RolloutClient.GetCurrentRollout()
  """
  current_rollout = None
  try:
    # find the last deployed rollout.
    rollouts = list(
        rollout_util.GetFilteredRollouts(
            target_ref,
            pipeline_ref,
            filter_str=rollout_util.DEPLOYED_ROLLOUT_FILTER_TEMPLATE,
            order_by=rollout_util.SUCCEED_ROLLOUT_ORDERBY,
            limit=1))
    if rollouts:
      current_rollout = rollouts[0]
  except apitools_exceptions.HttpError as error:
    log.debug('failed to get the current rollout of target {}: {}'.format(
        target_ref.RelativeName(), error.content))

  return current_rollout


def TargetReferenceFromName(target_name):
  """Creates a target reference from full name.

  Args:
    target_name: str, target resource name.

  Returns:
    Target reference.
  """

  return resources.REGISTRY.ParseRelativeName(
      target_name, collection=_SHARED_TARGET_COLLECTION)


def TargetId(target_name_or_id):
  """Returns target ID.

  Args:
    target_name_or_id: str, target full name or ID.

  Returns:
    Target ID.
  """

  if 'projects/' in target_name_or_id:
    return TargetReferenceFromName(target_name_or_id).Name()

  return target_name_or_id


def TargetReference(target_name_or_id, project, location_id):
  """Creates the target reference base on the parameters.

  Returns the shared target reference.

  Args:
    target_name_or_id: str, target full name or ID.
    project: str,project number or ID.
    location_id: str, region ID.

  Returns:
    Target reference.
  """
  return resources.REGISTRY.Parse(
      None,
      collection=_SHARED_TARGET_COLLECTION,
      params={
          'projectsId': project,
          'locationsId': location_id,
          'targetsId': TargetId(target_name_or_id),
      })


def GetTarget(target_ref):
  """Gets the target message by calling the get target API.

  Args:
    target_ref: protorpc.messages.Message, protorpc.messages.Message, target
      reference.

  Returns:
    Target message.
  Raises:
    Exceptions raised by TargetsClient's get functions
  """
  return target.TargetsClient().Get(target_ref.RelativeName())


def PatchTarget(target_obj):
  """Patches a target resource by calling the patch target API.

  Args:
      target_obj: apitools.base.protorpclite.messages.Message, target message.

  Returns:
      The operation message.
  """
  return target.TargetsClient().Patch(target_obj)


def DeleteTarget(name):
  """Deletes a target resource by calling the delete target API.

  Args:
    name: str, target name.

  Returns:
    The operation message.
  """
  return target.TargetsClient().Delete(name)


def ListTarget(parent_name):
  """List target resources by calling the list target API.

  Args:
    parent_name: str, the name of the collection that owns the targets.

  Returns:
    List of targets returns from target list API call.
  """
  return target.TargetsClient().List(parent_name)

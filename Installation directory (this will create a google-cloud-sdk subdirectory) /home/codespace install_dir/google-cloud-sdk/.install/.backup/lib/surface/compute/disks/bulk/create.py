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
"""Command for creating disks."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import filter_rewrite
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.disks import flags as disks_flags
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'brief':
        """
          Create multiple Compute Engine disks.
        """,
    'DESCRIPTION':
        """
        *{command}* facilitates the creation of multiple Compute Engine
        disks with a single command. This includes cloning a set of Async PD
        secondary disks with the same consistency group policy.
        """,
    'EXAMPLES':
        """
        To consistently clone secondary disks with the same consistency group
        policy 'projects/example-project/regions/us-central1/resourcePolicies/example-group-policy' to target zone 'us-central1-a', run:

          $ {command} --source-consistency-group-policy=projects/example-project/regions/us-central1/resourcePolicies/example-group-policy --zone=us-central1-a
        """,
}


def _CommonArgs(parser):
  """Add arguments used for parsing in all command tracks."""
  disks_flags.AddBulkCreateArgs(parser)


def _GetOperations(compute_client,
                   project,
                   operation_group_id,
                   scope_name,
                   is_zonal):
  """Requests operations with group id matching the given one."""

  errors_to_collect = []

  _, operation_filter = filter_rewrite.Rewriter().Rewrite(
      expression='operationGroupId=' + operation_group_id)

  if is_zonal:
    operations_response = compute_client.MakeRequests(
        [(compute_client.apitools_client.zoneOperations, 'List',
          compute_client.apitools_client.zoneOperations.GetRequestType('List')(
              filter=operation_filter, zone=scope_name, project=project))],
        errors_to_collect=errors_to_collect,
        log_result=False,
        always_return_operation=True,
        no_followup=True)
  else:
    operations_response = compute_client.MakeRequests(
        [(compute_client.apitools_client.regionOperations, 'List',
          compute_client.apitools_client.regionOperations.GetRequestType('List')
          (filter=operation_filter, region=scope_name, project=project))],
        errors_to_collect=errors_to_collect,
        log_result=False,
        always_return_operation=True,
        no_followup=True)

  return operations_response, errors_to_collect


def _GetResult(compute_client, request, operation_group_id, parent_errors):
  """Requests operations with group id and parses them as an output."""

  is_zonal = hasattr(request, 'zone')
  scope_name = request.zone if is_zonal else request.region
  operations_response, errors = _GetOperations(compute_client, request.project,
                                               operation_group_id, scope_name,
                                               is_zonal)
  result = {'operationGroupId': operation_group_id, 'createdDisksCount': 0}
  if not parent_errors and not errors:
    def IsPerDiskOperation(op):
      return op.operationType == 'insert' and str(
          op.status) == 'DONE' and op.error is None

    result['createdDisksCount'] = sum(
        map(IsPerDiskOperation, operations_response))
  return result


@base.ReleaseTracks(base.ReleaseTrack.GA)
class BulkCreate(base.Command):
  """Create multiple Compute Engine disks."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  @classmethod
  def _GetApiHolder(cls, no_http=False):
    return base_classes.ComputeApiHolder(cls.ReleaseTrack(), no_http)

  def Run(self, args):
    return self._Run(args)

  def _Run(self, args):
    compute_holder = self._GetApiHolder()
    client = compute_holder.client

    policy_url = getattr(args, 'source_consistency_group_policy', None)
    project = properties.VALUES.core.project.GetOrFail()
    if args.IsSpecified('zone'):
      request = client.messages.ComputeDisksBulkInsertRequest(
          project=project,
          zone=args.zone,
          bulkInsertDiskResource=client.messages.BulkInsertDiskResource(
              sourceConsistencyGroupPolicy=policy_url))
      request = (client.apitools_client.disks, 'BulkInsert', request)
    else:
      request = client.messages.ComputeRegionDisksBulkInsertRequest(
          project=project,
          region=args.region,
          bulkInsertDiskResource=client.messages.BulkInsertDiskResource(
              sourceConsistencyGroupPolicy=policy_url))
      request = (client.apitools_client.regionDisks, 'BulkInsert', request)
    errors_to_collect = []
    response = client.MakeRequests([request],
                                   errors_to_collect=errors_to_collect,
                                   no_followup=True,
                                   always_return_operation=True)

    # filters error object so that only error message is persisted
    if errors_to_collect:
      # workaround to change errors_to_collect since tuples are immutable
      for i in range(len(errors_to_collect)):
        error_tuple = errors_to_collect[i]
        error_list = list(error_tuple)
        # When requests are accepted, but workflow server processed it
        # exceptionally, the error message is in message field. However, when
        # requests are rejected, message field doesn't exist, we don't need to
        # extract error message from message field.
        if hasattr(error_list[1], 'message'):
          error_list[1] = error_list[1].message
        errors_to_collect[i] = tuple(error_list)
    self._errors = errors_to_collect
    if not response:
      return
    operation_group_id = response[0].operationGroupId
    result = _GetResult(client, request[2], operation_group_id,
                        errors_to_collect)

    if response[0].statusMessage:
      result['statusMessage'] = response[0].statusMessage
    return result

  def Epilog(self, resources_were_displayed):
    del resources_were_displayed
    if self._errors:
      log.error(self._errors[0][1])

BulkCreate.detailed_help = DETAILED_HELP


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BulkCreateBeta(BulkCreate):
  """Create multiple Compute Engine disks."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)

BulkCreateBeta.detailed_help = DETAILED_HELP


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class BulkCreateAlpha(BulkCreate):
  """Create multiple Compute Engine disks."""

  @classmethod
  def Args(cls, parser):
    _CommonArgs(parser)

  def Run(self, args):
    return self._Run(args)

BulkCreateAlpha.detailed_help = DETAILED_HELP

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
"""OS policy assignment report gcloud commands declarative functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute.os_config import flags
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties

_LIST_URI = ('projects/{project}/locations/{location}'
             '/instances/{instance}/osPolicyAssignments/{os_policy_assignment}')

_LIST_SUMMARY_STR = (
    '{compliant_policies_count}/{total_policies_count} policies compliant')


class ListTableRow:
  """View model for table rows of OS policy assignment reports list."""

  def __init__(self, instance, assignment_id, location, update_time,
               summary_str):
    self.instance = instance
    self.assignment_id = assignment_id
    self.location = location
    self.update_time = update_time
    self.summary_str = summary_str

  def __eq__(self, other):
    return self.instance == other.instance and self.assignment_id == other.assignment_id and self.location == other.location and self.update_time == other.update_time and self.summary_str == other.summary_str

  def __repr__(self):
    return ('ListTableRow(instance=%s, assignment_id=%s, location=%s, '
            'update_time=%s, summary_str=%s)') % (
                self.instance, self.assignment_id, self.location,
                self.update_time, self.summary_str)


def SetParentOnListRequestHook(unused_ref, args, request):
  """Add parent field to List request.

  Args:
    unused_ref: A parsed resource reference; unused.
    args: The parsed args namespace from CLI
    request: List request for the API call

  Returns:
    Modified request that includes the parent field.
  """
  project = args.project or properties.VALUES.core.project.GetOrFail()
  location = args.location or properties.VALUES.compute.zone.Get()

  if not location:
    raise exceptions.Error(
        'Location value is required either from `--location` or default zone, see {url}. '
        .format(
            url='https://cloud.google.com/compute/docs/gcloud-compute#default-region-zone'
        ))

  instance = args.instance or '-'
  os_policy_assignment = args.assignment_id or '-'

  flags.ValidateInstance(instance, '--instance')
  flags.ValidateZone(location, '--location')
  flags.ValidateInstanceOsPolicyAssignment(os_policy_assignment,
                                           '--assignment-id')

  request.parent = _LIST_URI.format(
      project=project,
      location=location,
      instance=instance,
      os_policy_assignment=os_policy_assignment)
  return request


def CreateSummarizedListOSPolicyAssignmentReportsHook(response, args):
  """Create ListTableRow from ListOSPolicyAssignmentReports response.

  Args:
    response: Response from ListOSPolicyAssignmentReports
    args: gcloud args

  Returns:
    ListTableRows of summarized os policy assignment reports
  """
  rows = []
  for report in response:
    compliant_policies_count = 0
    total_policies_count = 0
    for policy in report.osPolicyCompliances:
      total_policies_count += 1
      if policy.complianceState.name == 'COMPLIANT':
        compliant_policies_count += 1
    summary_str = _LIST_SUMMARY_STR.format(
        compliant_policies_count=compliant_policies_count,
        total_policies_count=total_policies_count)
    rows.append(
        ListTableRow(
            instance=report.instance,
            assignment_id=report.name.split('/')[-2],
            location=args.location or properties.VALUES.compute.zone.Get(),
            update_time=report.updateTime,
            summary_str=summary_str))

  return rows

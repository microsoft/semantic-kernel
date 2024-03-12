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
"""Implements command to list the instance details for an OS patch job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.os_config import resource_args
from googlecloudsdk.core.resource import resource_projector


def _TransformFailureReason(resource):
  max_len = 80  # Show the first 80 characters if failure reason is long.
  message = resource.get('failureReason', '')
  return (message[:max_len] + '..') if len(message) > max_len else message


def _PostProcessListResult(results):
  # Inject a "zone" field into the output resources for easy filtering.
  results_json = resource_projector.MakeSerializable(results)
  for result in results_json:
    result['zone'] = result['name'].split('/')[3]

  return results_json


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class ListInstanceDetails(base.ListCommand):
  """List the instance details for an OS patch job.

  ## EXAMPLES

  To list the instance details for each instance in the patch job `job1`, run:

        $ {command} job1

  """

  @staticmethod
  def Args(parser):
    base.URI_FLAG.RemoveFromParser(parser)  # InstanceDetails have no URI.
    resource_args.AddPatchJobResourceArg(parser, 'to list instance details.')
    parser.display_info.AddFormat("""
          table(
            name.basename(),
            zone,
            state,
            failure_reason()
          )
        """)
    parser.display_info.AddTransforms(
        {'failure_reason': _TransformFailureReason})

  def Run(self, args):
    patch_job_ref = args.CONCEPTS.patch_job.Parse()

    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(release_track)
    messages = osconfig_api_utils.GetClientMessages(release_track)

    request = messages.OsconfigProjectsPatchJobsInstanceDetailsListRequest(
        pageSize=args.page_size, parent=patch_job_ref.RelativeName())

    results = list(
        list_pager.YieldFromList(
            client.projects_patchJobs_instanceDetails,
            request,
            limit=args.limit,
            batch_size=args.page_size,
            field='patchJobInstanceDetails',
            batch_size_attribute='pageSize'),)

    return _PostProcessListResult(results)

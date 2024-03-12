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
"""Implements command to list ongoing and completed patch jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.os_config import utils as osconfig_command_utils
from googlecloudsdk.core import properties


_DEFAULT_LIMIT = 10


def _TransformPatchJobDisplayName(resource):
  """Returns the display name of a patch job."""

  max_len = 15  # Show only the first 15 characters if display name is long.

  if resource.get('displayName', ''):
    name = resource['displayName']
  elif resource.get('patchDeployment', ''):
    name = osconfig_command_utils.GetResourceName(resource['patchDeployment'])
  else:
    name = ''

  return (name[:max_len] + '..') if len(name) > max_len else name


def _TransformPatchJobDescription(resource):
  max_len = 30  # Show only the first 30 characters if description is long.
  description = resource.get('description', '')
  return (description[:max_len] +
          '..') if len(description) > max_len else description


def _TransformState(resource):
  state = resource.get('state', '')

  if 'instanceDetailsSummary' in resource:
    num_instances_pending_reboot = int(resource['instanceDetailsSummary'].get(
        'instancesSucceededRebootRequired', '0'))
    if state == 'SUCCEEDED' and num_instances_pending_reboot > 0:
      return 'SUCCEEDED_INSTANCES_PENDING_REBOOT'

  return state


def _TransformNumInstances(resource):
  """Sums up number of instances in a patch job."""
  if 'instanceDetailsSummary' not in resource:
    return None

  instance_details_summary = resource['instanceDetailsSummary']
  num_instances = 0
  for status in instance_details_summary:
    num_instances += int(instance_details_summary.get(status, 0))
  return num_instances


def _MakeGetUriFunc(registry):
  """Returns a transformation function from a patch job resource to an URI."""

  def UriFunc(resource):
    ref = registry.Parse(
        resource.name,
        params={
            'projects': properties.VALUES.core.project.GetOrFail,
            'patchJobs': resource.name
        },
        collection='osconfig.projects.patchJobs')
    return ref.SelfLink()

  return UriFunc


def _Args(parser, release_track):
  """Parses input flags and sets up output formats."""

  base.LIMIT_FLAG.SetDefault(parser, _DEFAULT_LIMIT)
  parser.display_info.AddFormat("""
        table(
          name.basename():label=ID,
          display_name():label=NAME,
          description(),
          create_time,
          update_time,
          state(),
          targeted_instances()
        )
      """)
  parser.display_info.AddTransforms({
      'display_name': _TransformPatchJobDisplayName,
      'description': _TransformPatchJobDescription,
      'state': _TransformState,
      'targeted_instances': _TransformNumInstances,
  })
  registry = osconfig_api_utils.GetRegistry(release_track)
  parser.display_info.AddUriFunc(_MakeGetUriFunc(registry))


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List ongoing and completed patch jobs.

  ## EXAMPLES

  To list patch jobs in the current project, run:

        $ {command}

  """

  @staticmethod
  def Args(parser):
    _Args(parser, base.ReleaseTrack.GA)

  def Run(self, args):
    project = properties.VALUES.core.project.GetOrFail()

    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(release_track)
    messages = osconfig_api_utils.GetClientMessages(release_track)

    request = messages.OsconfigProjectsPatchJobsListRequest(
        pageSize=args.page_size,
        parent=osconfig_command_utils.GetProjectUriPath(project))

    return list_pager.YieldFromList(
        client.projects_patchJobs,
        request,
        limit=args.limit,
        batch_size=osconfig_command_utils.GetListBatchSize(args),
        field='patchJobs',
        batch_size_attribute='pageSize',
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List ongoing and completed patch jobs.

  ## EXAMPLES

  To list patch jobs in the current project, run:

        $ {command}

  """

  @staticmethod
  def Args(parser):
    _Args(parser, base.ReleaseTrack.BETA)

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
"""Implements command to list patch deployments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.os_config import utils as osconfig_command_utils
from googlecloudsdk.core import properties

_DEFAULT_NO_VALUE = '---'
_ONE_TIME_SCHEDULE = 'oneTimeSchedule'
_RECURRING_SCHEDULE = 'recurringSchedule'
_LAST_EXECUTE_TIME = 'lastExecuteTime'
_NEXT_EXECUTE_TIME = 'nextExecuteTime'


def _TransformLastRun(resource):
  return resource.get(_LAST_EXECUTE_TIME, _DEFAULT_NO_VALUE)


def _TransformNextRun(resource):
  """Returns the timestamp of the next scheduled run for this patch deployment."""

  if _ONE_TIME_SCHEDULE in resource:
    if resource.get(_LAST_EXECUTE_TIME, ''):
      # This works as long as we don't allow user to update any patch deployment
      # with a one-time schedule.
      return _DEFAULT_NO_VALUE
    else:
      schedule = resource[_ONE_TIME_SCHEDULE]
      return schedule.get('executeTime', _DEFAULT_NO_VALUE)
  elif _RECURRING_SCHEDULE in resource:
    schedule = resource[_RECURRING_SCHEDULE]
    return schedule.get(_NEXT_EXECUTE_TIME, _DEFAULT_NO_VALUE)
  else:
    return _DEFAULT_NO_VALUE


def _TransformFrequency(resource):
  """Returns a string description of the patch deployment schedule."""

  if _ONE_TIME_SCHEDULE in resource:
    return 'Once: Scheduled for ' + resource[_ONE_TIME_SCHEDULE]['executeTime']
  elif _RECURRING_SCHEDULE in resource:
    output_format = 'Recurring - {} {}'
    schedule = resource[_RECURRING_SCHEDULE]
    if schedule['frequency'] == 'DAILY':
      return output_format.format('Daily', '')
    elif schedule['frequency'] == 'WEEKLY':
      return output_format.format('Weekly', '')
    elif schedule['frequency'] == 'MONTHLY':
      if schedule['monthly'].get('weekDayOfMonth', ''):
        return output_format.format('Monthly', 'on specific day(s)')
      else:
        return output_format.format('Monthly', 'on specific date(s)')
    else:
      return _DEFAULT_NO_VALUE
  else:
    return _DEFAULT_NO_VALUE


def _MakeGetUriFunc(registry):
  """Returns a transformation function from a patch deployment resource to an URI."""

  def UriFunc(resource):
    ref = registry.Parse(
        resource.name,
        params={
            'projects': properties.VALUES.core.project.GetOrFail,
            'patchDeployments': resource.name
        },
        collection='osconfig.projects.patchDeployments')
    return ref.SelfLink()

  return UriFunc


def _Args(parser, release_track):
  """Parses input flags and sets up output formats."""

  parser.display_info.AddFormat("""
          table(
            name.basename(),
            last_run(),
            next_run(),
            frequency()
          )
        """)
  parser.display_info.AddTransforms({
      'last_run': _TransformLastRun,
      'next_run': _TransformNextRun,
      'frequency': _TransformFrequency,
  })
  registry = osconfig_api_utils.GetRegistry(release_track)
  parser.display_info.AddUriFunc(_MakeGetUriFunc(registry))


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List patch deployments in a project."""

  detailed_help = {
      'EXAMPLES':
          """\
      To list all patch deployments in the current project, run:

          $ {command}
      """,
  }

  @staticmethod
  def Args(parser):
    _Args(parser, base.ReleaseTrack.GA)

  def Run(self, args):
    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(release_track)
    messages = osconfig_api_utils.GetClientMessages(release_track)

    project = properties.VALUES.core.project.GetOrFail()
    request = messages.OsconfigProjectsPatchDeploymentsListRequest(
        pageSize=args.page_size,
        parent=osconfig_command_utils.GetProjectUriPath(project),
    )
    service = client.projects_patchDeployments

    return list_pager.YieldFromList(
        service,
        request,
        limit=args.limit,
        batch_size=osconfig_command_utils.GetListBatchSize(args),
        field='patchDeployments',
        batch_size_attribute='pageSize',
    )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListBeta(List):
  """List patch deployments in a project."""

  detailed_help = {
      'EXAMPLES':
          """\
      To list all patch deployments in the current project, run:

          $ {command}
      """,
  }

  @staticmethod
  def Args(parser):
    _Args(parser, base.ReleaseTrack.BETA)

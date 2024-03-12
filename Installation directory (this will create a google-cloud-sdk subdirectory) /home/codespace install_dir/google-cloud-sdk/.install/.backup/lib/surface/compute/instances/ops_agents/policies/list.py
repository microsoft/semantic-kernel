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
"""Implements command to list guest policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.compute.instances.ops_agents import ops_agents_policy as agent_policy
from googlecloudsdk.api_lib.compute.instances.ops_agents.converters import guest_policy_to_ops_agents_policy_converter as converter
from googlecloudsdk.api_lib.compute.instances.ops_agents.validators import guest_policy_validator
from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.os_config import utils as osconfig_command_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _TransformGuestPolicyDescription(resource):
  """Returns a length-limited guest policy description."""

  max_len = 30  # Show only the first 30 characters if description is long.
  description = resource.get('description', '')
  return (description[:max_len] +
          '...') if len(description) > max_len else description


def _Args(parser):
  """Parses input flags and sets up output formats."""

  parser.display_info.AddFormat("""
        table(
          id.basename(),
          description(),
          create_time,
          update_time
        )
      """)
  parser.display_info.AddTransforms(
      {'description': _TransformGuestPolicyDescription})


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List Google Cloud's operations suite agents (Ops Agents) policies.

  {command} lists policies that facilitate agent management across Compute
  Engine instances based on user specified instance filters. These policies
  install, specify versioning, enable autoupgrade, and remove Ops Agents.

  The command returns a list of policies, including the ``ID'', ``DESCRIPTION'',
  ``CREATE_TIME'', and ``UPDATE_TIME'' for each policy. If no policies are
  found, it returns an empty list. If malformed policies are found, they are
  included in the result list with the descriptions replaced by ``<MALFORMED>'',
  and a warning is shown.
  """

  detailed_help = {
      'DESCRIPTION':
      '{description}',
      'EXAMPLES':
      """\
      To list guest policies in the current project, run:

      $ {command}
      """,
  }

  @staticmethod
  def Args(parser):
    """See base class."""
    _Args(parser)

  def Run(self, args):
    """See base class."""
    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(
        release_track, api_version_override='v1beta')
    messages = osconfig_api_utils.GetClientMessages(
        release_track, api_version_override='v1beta')

    project = properties.VALUES.core.project.GetOrFail()
    request = messages.OsconfigProjectsGuestPoliciesListRequest(
        pageSize=args.page_size,
        parent=osconfig_command_utils.GetProjectUriPath(project),
    )
    service = client.projects_guestPolicies

    for guest_policy in list_pager.YieldFromList(
        service,
        request,
        limit=args.limit,
        predicate=guest_policy_validator.IsOpsAgentPolicy,
        batch_size=osconfig_command_utils.GetListBatchSize(args),
        field='guestPolicies',
        batch_size_attribute='pageSize',
    ):
      try:
        yield converter.ConvertGuestPolicyToOpsAgentPolicy(guest_policy)
      except exceptions.BadArgumentException:
        log.warning(
            'Encountered a malformed policy. The Ops Agents policy [%s] may '
            'have been modified directly by the OS Config guest policy API / '
            'gcloud commands. If so, please delete and re-create with the Ops '
            'Agents policy gcloud commands. If not, this may be an internal '
            'error.',
            guest_policy.name,
        )
        yield agent_policy.OpsAgentPolicy(
            assignment=None,
            agent_rules=None,
            description='<MALFORMED>',
            etag=None,
            name=guest_policy.name,
            update_time=guest_policy.updateTime,
            create_time=guest_policy.createTime
        )

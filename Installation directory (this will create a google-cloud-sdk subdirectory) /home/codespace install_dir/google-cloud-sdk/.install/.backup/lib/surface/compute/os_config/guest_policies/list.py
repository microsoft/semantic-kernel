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
from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.os_config import utils as osconfig_command_utils
from googlecloudsdk.core import properties


def _TransformGuestPolicyDescription(resource):
  """Returns a length-limited guest policy description."""

  max_len = 30  # Show only the first 30 characters if description is long.
  description = resource.get('description', '')
  return (description[:max_len] +
          '..') if len(description) > max_len else description


def _MakeGetUriFunc(registry):
  """Returns a transformation function from a guest policy resource to URI."""

  def UriFunc(resource):
    parent_type = resource.name.split('/')[0]
    ref = registry.Parse(
        resource.name,
        collection='osconfig.{}.guestPolicies'.format(parent_type))
    return ref.SelfLink()

  return UriFunc


def _Args(parser, release_track):
  """Parses input flags and sets up output formats."""

  parser.display_info.AddFormat("""
        table(
          name.basename(),
          description(),
          create_time,
          update_time
        )
      """)
  parser.display_info.AddTransforms(
      {'description': _TransformGuestPolicyDescription})
  registry = osconfig_api_utils.GetRegistry(release_track)
  parser.display_info.AddUriFunc(_MakeGetUriFunc(registry))


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class List(base.ListCommand):
  """List guest policies in a project.

  ## EXAMPLES

    To list guest policies in the current project, run:

          $ {command}

  """

  @staticmethod
  def Args(parser):
    """See base class."""
    _Args(parser, base.ReleaseTrack.BETA)

  def Run(self, args):
    """See base class."""
    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(release_track)
    messages = osconfig_api_utils.GetClientMessages(release_track)

    project = properties.VALUES.core.project.GetOrFail()
    request = messages.OsconfigProjectsGuestPoliciesListRequest(
        pageSize=args.page_size,
        parent=osconfig_command_utils.GetProjectUriPath(project),
    )
    service = client.projects_guestPolicies

    return list_pager.YieldFromList(
        service,
        request,
        limit=args.limit,
        batch_size=osconfig_command_utils.GetListBatchSize(args),
        field='guestPolicies',
        batch_size_attribute='pageSize',
    )
